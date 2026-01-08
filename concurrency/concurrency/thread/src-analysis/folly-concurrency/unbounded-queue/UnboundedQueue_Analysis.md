# UnboundedQueue 源码解析

## 概述

`UnboundedQueue` 是 Facebook Folly 库中的**无界动态扩展队列**，与 `MPMCQueue`（有界队列）形成对比。

### 核心特性

- ✅ **无界容量**：可以动态扩展，理论上无上限
- ✅ **多种变体**：支持 SPSC, MPSC, SPMC, MPMC
- ✅ **可选阻塞**：通过 `MayBlock` 参数控制
- ✅ **线性化保证**：严格的顺序性
- ✅ **内存安全**：使用 hazard pointer 进行延迟回收

## 与 MPMCQueue 的对比

| 特性 | MPMCQueue | UnboundedQueue |
|------|-----------|----------------|
| 容量 | 固定有界 | 无界动态扩展 |
| 内存分配 | 构造时一次性分配 | 运行时按需分配段 |
| 适用场景 | 容量可预估 | 容量不可预估或可能很大 |
| 性能 | 更高（无分配开销） | 稍低（有分配开销） |

## 核心设计：分段（Segment）架构

### 1. 整体结构

```
UnboundedQueue
┌─────────────────────────────────────────────────────┐
│ Consumer: head → Segment0 → Segment1 → Segment2    │
│ Producer: tail → Segment2                          │
│                                                     │
│ Segment0: [Entry0] [Entry1] ... [Entry255]        │
│ Segment1: [Entry0] [Entry1] ... [Entry255]         │
│ Segment2: [Entry0] [Entry1] ... [Entry255]         │
└─────────────────────────────────────────────────────┘
```

### 2. Segment（段）

```cpp
class Segment : public hazptr_obj_base_linked<Segment, Atom> {
    Atom<Segment*> next_{nullptr};  // 指向下一个段
    const Ticket min_;              // 该段的最小票号
    alignas(Align) Entry b_[SegmentSize];  // 固定大小的 Entry 数组
};
```

**关键点：**
- 每个段包含 `2^LgSegmentSize` 个 Entry（默认 256 个）
- 段之间通过单向链表连接
- 每个段有固定的票号范围：`[min_, min_ + SegmentSize)`
- 继承自 `hazptr_obj_base_linked`，支持延迟回收

### 3. Entry（条目）

```cpp
class Entry {
    Sem flag_;                      // 同步信号量
    aligned_storage_for_t<T> item_; // 存储元素
};
```

**关键点：**
- 每个 Entry 存储一个元素
- 使用 `SaturatingSemaphore` 进行同步
- 写入时 `post()`，读取时 `wait()`

## 票号系统

### 票号到位置的映射

```cpp
FOLLY_ALWAYS_INLINE size_t index(Ticket t) const noexcept {
    return (t * Stride) & (SegmentSize - 1);
}
```

**示例：** `SegmentSize = 256`（2^8），`Stride = 27`

| 票号 | 计算 | Entry 索引 |
|------|------|-----------|
| 0    | (0×27) & 255 = 0 | Entry[0] |
| 1    | (1×27) & 255 = 27 | Entry[27] |
| 2    | (2×27) & 255 = 54 | Entry[54] |
| 256  | (256×27) & 255 = 0 | **下一个段的 Entry[0]** |

**关键理解：**
- 票号 `t` 对应的段：`segment = floor(t / SegmentSize)`
- 票号 `t` 在段内的索引：`index(t)`
- 使用位运算 `& (SegmentSize - 1)` 代替取模（更快）

## 核心操作流程

### 1. 入队（Enqueue）

```cpp
template <typename Arg>
void enqueueImpl(Arg&& arg) {
    // 1. 获取当前尾段（使用 hazard pointer 保护）
    Segment* s = hptr.protect(p_.tail);
    
    // 2. 获取并递增生产者票号
    Ticket t = fetchIncrementProducerTicket();
    
    // 3. 如果是多生产者，可能需要找到正确的段
    if (!SingleProducer) {
        s = findSegment(s, t);
    }
    
    // 4. 计算 Entry 索引并写入
    size_t idx = index(t);
    Entry& e = s->entry(idx);
    e.putItem(std::forward<Arg>(arg));
    
    // 5. 如果是段内第一个票号，负责分配下一个段
    if (responsibleForAlloc(t)) {
        allocNextSegment(s);
    }
    
    // 6. 如果是段内最后一个票号，负责推进 tail
    if (responsibleForAdvance(t)) {
        advanceTail(s);
    }
}
```

**责任分配：**
- **第一个票号**（`t & (SegmentSize-1) == 0`）：分配下一个段
- **最后一个票号**（`t & (SegmentSize-1) == SegmentSize-1`）：推进 tail 指针

### 2. 出队（Dequeue）

```cpp
T dequeueImpl() noexcept {
    // 1. 获取当前头段
    Segment* s = hptr.protect(c_.head);
    
    // 2. 获取并递增消费者票号
    Ticket t = fetchIncrementConsumerTicket();
    
    // 3. 如果是多消费者，可能需要找到正确的段
    if (!SingleConsumer) {
        s = findSegment(s, t);
    }
    
    // 4. 计算 Entry 索引并读取
    size_t idx = index(t);
    Entry& e = s->entry(idx);
    auto res = e.takeItem();  // 会等待直到元素可用
    
    // 5. 如果是段内最后一个票号，负责推进 head
    if (responsibleForAdvance(t)) {
        advanceHead(s);
    }
    
    return res;
}
```

### 3. 段分配（allocNextSegment）

```cpp
Segment* allocNextSegment(Segment* s) {
    auto t = s->minTicket() + SegmentSize;
    Segment* next = new Segment(t);  // 分配新段
    
    // 设置 hazard pointer cohort
    next->set_cohort_no_tag(&c_.cohort);
    next->acquire_ref_safe();
    
    // CAS 设置 next 指针（可能失败，如果其他线程已经设置）
    if (!s->casNextSegment(next)) {
        delete next;  // 失败则删除，使用其他线程分配的段
        next = s->nextSegment();
    }
    
    return next;
}
```

**关键点：**
- 使用 CAS 确保只有一个线程成功设置 `next`
- 失败的线程使用已分配的段，避免重复分配
- 新段继承 hazard pointer cohort，支持延迟回收

### 4. 段回收（reclaimSegment）

```cpp
void reclaimSegment(Segment* s) noexcept {
    if (SPSC) {
        delete s;  // SPSC 可以直接删除
    } else {
        s->retire();  // MPMC 使用 hazard pointer 延迟回收
    }
}
```

**SPSC vs MPMC：**
- **SPSC**：单生产者单消费者，可以直接删除（无并发访问）
- **MPMC**：多生产者多消费者，使用 hazard pointer 延迟回收（可能有滞后线程仍在使用）

## 关键机制详解

### 1. Hazard Pointer（危险指针）

**用途：** 在多线程环境下安全地访问和回收段

```cpp
hazptr_holder<Atom> hptr = make_hazard_pointer<Atom>();
Segment* s = hptr.protect(c_.head);  // 保护 head 指向的段
```

**工作原理：**
1. 线程将指针注册到 hazard pointer
2. 其他线程在回收前检查是否有 hazard pointer 引用
3. 只有当没有 hazard pointer 引用时才真正回收

### 2. SaturatingSemaphore

**用途：** Entry 的同步机制

```cpp
class Entry {
    Sem flag_;  // SaturatingSemaphore
    
    void putItem(Arg&& arg) {
        new (&item_) T(std::forward<Arg>(arg));
        flag_.post();  // 通知等待的消费者
    }
    
    T takeItem() {
        flag_.wait();  // 等待直到元素可用
        return getItem();
    }
};
```

**特点：**
- 支持阻塞和自旋两种模式（由 `MayBlock` 控制）
- 使用 futex 实现高效等待
- 饱和信号量，不会溢出

### 3. 责任分配机制

**为什么需要责任分配？**

在并发环境下，如果所有线程都尝试分配段或推进指针，会导致：
- 重复分配（浪费）
- 竞争激烈（性能下降）

**解决方案：** 让特定票号的线程负责特定任务

```cpp
// 段内第一个票号负责分配
bool responsibleForAlloc(Ticket t) const noexcept {
    return (t & (SegmentSize - 1)) == 0;
}

// 段内最后一个票号负责推进指针
bool responsibleForAdvance(Ticket t) const noexcept {
    return (t & (SegmentSize - 1)) == (SegmentSize - 1);
}
```

**示例：** `SegmentSize = 256`

- 票号 0, 256, 512, ... → 负责分配下一个段
- 票号 255, 511, 767, ... → 负责推进 tail/head

### 4. 滞后线程处理

**问题：** 在多线程环境下，某些线程可能滞后，仍在使用已"过期"的段

**解决方案：**

```cpp
Segment* findSegment(Segment* s, const Ticket t) noexcept {
    while (FOLLY_UNLIKELY(t >= (s->minTicket() + SegmentSize))) {
        s = getAllocNextSegment(s, t);  // 找到正确的段
        DCHECK(s);
    }
    return s;
}
```

**getAllocNextSegment 的处理：**
1. 先检查 `nextSegment()` 是否已存在
2. 如果不存在，等待一段时间（自旋）
3. 如果仍不存在，主动分配

## 性能优化

### 1. SPSC 特殊优化

```cpp
static constexpr bool SPSC = SingleProducer && SingleConsumer;

if (SPSC) {
    Segment* s = tail();  // 直接读取，无需原子操作
    enqueueCommon(s, std::forward<Arg>(arg));
} else {
    hazptr_holder<Atom> hptr = make_hazard_pointer<Atom>();
    Segment* s = hptr.protect(p_.tail);  // 需要保护
    enqueueCommon(s, std::forward<Arg>(arg));
}
```

**SPSC 优势：**
- 无需 `fetch_add`（单生产者）
- 无需 CAS（单消费者）
- 无需 hazard pointer（无并发访问）
- 无内存屏障（relaxed 内存序）

### 2. 步长（Stride）避免 False Sharing

```cpp
static constexpr size_t Stride = SPSC || (LgSegmentSize <= 1) ? 1 : 27;
```

- **SPSC**：步长为 1（无竞争）
- **其他情况**：步长为 27（质数，避免缓存行冲突）

### 3. 对齐优化

```cpp
alignas(Align) Entry b_[SegmentSize];
```

- 默认对齐到缓存行大小
- 可通过 `LgAlign` 参数调整（平衡性能和内存）

## 内存管理

### 内存使用

- **空队列**：包含 1 个段
- **非空队列**：包含 1-2 个额外段（超出内容所需）
- **已移除的段**：延迟回收，直到没有线程引用

### 清理机制

```cpp
~UnboundedQueue() {
    cleanUpRemainingItems();      // 清理剩余元素
    reclaimRemainingSegments();   // 回收所有段
}
```

## 使用场景

### 适合使用 UnboundedQueue

- ✅ 容量不可预估
- ✅ 可能有突发流量
- ✅ 可以接受动态分配开销

### 不适合使用 UnboundedQueue

- ❌ 必须限制内存使用 → 使用 `DynamicBoundedQueue`
- ❌ 不能接受分配开销 → 使用固定大小 `MPMCQueue`
- ❌ 非阻塞 SPSC → 使用 `ProducerConsumerQueue`

## 模板别名

```cpp
USPSCQueue<T>  // 单生产者单消费者
UMPSCQueue<T>  // 多生产者单消费者
USPMCQueue<T>  // 单生产者多消费者
UMPMCQueue<T>  // 多生产者多消费者
```

## 总结

**UnboundedQueue 的核心设计思想：**

1. **分段架构**：将无界队列分解为固定大小的段
2. **责任分配**：特定票号负责分配和推进，减少竞争
3. **延迟回收**：使用 hazard pointer 安全回收，支持滞后线程
4. **性能优化**：SPSC 特殊路径，步长避免 false sharing
5. **线性化保证**：票号系统确保严格的顺序性

**与 MPMCQueue 的对比：**
- MPMCQueue：固定容量，一次分配，性能更高
- UnboundedQueue：动态扩展，按需分配，更灵活

两者都是高性能并发队列的优秀实现，选择取决于具体需求。

