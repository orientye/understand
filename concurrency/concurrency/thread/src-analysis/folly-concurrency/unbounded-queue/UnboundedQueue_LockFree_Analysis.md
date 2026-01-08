# UnboundedQueue 是否无锁？

## 简短回答

**UnboundedQueue 的无锁性取决于两个因素：**

1. **`Atom` 模板参数**（根本因素）
   - 如果 `Atom` 不是真正的原子类型 → ❌ 整个队列不是无锁的
   - 如果 `Atom = std::atomic`（默认）→ ✅ 原子操作层面是无锁的

2. **`MayBlock` 模板参数**（行为因素）
   - `MayBlock = false`：✅ 完全无锁（只自旋，不阻塞）
   - `MayBlock = true`：⚠️ 可能阻塞（使用 futex）

**综合判断：**
- ✅ **完全无锁**：`Atom = std::atomic` + `MayBlock = false`
- ⚠️ **部分无锁**：`Atom = std::atomic` + `MayBlock = true`（原子操作无锁，但可能阻塞）

## 详细分析

### 1. 无锁（Lock-Free）的定义

**无锁算法的特征：**
- 不使用互斥锁（mutex）
- 使用原子操作和 CAS
- 保证至少有一个线程能够取得进展（即使其他线程被挂起）

**无等待（Wait-Free）的定义：**
- 更强的保证：每个线程都能在有限步内完成操作

### 2. Atom 模板参数：无锁性的根本因素

**关键观察：`Atom` 参数是决定无锁性的根本因素！**

```cpp
template <
    typename T,
    bool SingleProducer,
    bool SingleConsumer,
    bool MayBlock,
    size_t LgSegmentSize = 8,
    size_t LgAlign = constexpr_log2(hardware_destructive_interference_size),
    template <typename> class Atom = std::atomic>  // ← 关键！
class UnboundedQueue
```

#### Atom 在代码中的使用

```cpp
// 1. 票号（生产者/消费者）
struct Producer {
    Atom<Segment*> tail;
    Atom<Ticket> ticket;  // ← 使用 Atom
};

struct Consumer {
    Atom<Segment*> head;
    Atom<Ticket> ticket;  // ← 使用 Atom
};

// 2. 段的 next 指针
class Segment {
    Atom<Segment*> next_{nullptr};  // ← 使用 Atom
};

// 3. 信号量也使用 Atom
using Sem = folly::SaturatingSemaphore<MayBlock, Atom>;
```

#### Atom 对无锁性的影响

**如果 `Atom = std::atomic`（默认）：**

```cpp
// 这些操作都是 lock-free 的
Atom<Ticket> ticket;
ticket.fetch_add(1, std::memory_order_acq_rel);  // ✅ lock-free

Atom<Segment*> next_;
next_.compare_exchange_strong(...);  // ✅ lock-free
```

**如果 `Atom` 不是真正的原子类型：**
- ❌ `fetch_add` 可能不是 lock-free
- ❌ `compare_exchange_strong` 可能不是 lock-free
- ❌ **整个队列不是无锁的**

**结论：**
- ✅ **原子操作层面**：取决于 `Atom`（默认 `std::atomic` 是无锁的）
- ⚠️ **整体行为**：取决于 `Atom` + `MayBlock`

#### Atom 参数还可能是什么？

`Atom` 是一个模板模板参数（template template parameter），要求是一个接受一个类型参数的模板类。以下是可能的值：

##### 1. std::atomic（默认，推荐）

```cpp
UMPMCQueue<int, true, 8, 7, std::atomic> queue;
// 或者使用默认值
UMPMCQueue<int> queue;  // Atom = std::atomic
```

**特点：**
- ✅ 标准库实现，跨平台
- ✅ 提供完整的原子操作接口
- ✅ 大多数操作是 lock-free 的（取决于平台）
- ✅ 内存序支持完整（relaxed, acquire, release, acq_rel, seq_cst）

**适用场景：**
- 默认选择，适用于大多数场景
- 需要标准兼容性

##### 2. folly::atomic（Folly 优化版本）

```cpp
UMPMCQueue<int, true, 8, 7, folly::atomic> queue;
```

**特点：**
- ✅ Folly 库提供的原子类型
- ✅ 可能针对特定平台有优化
- ✅ 提供与 `std::atomic` 兼容的接口
- ✅ 可能在某些场景下性能更好

**适用场景：**
- 使用 Folly 库的项目
- 需要特定平台优化
- 性能敏感场景

##### 3. 自定义原子类型包装器

理论上可以传入自定义的原子类型，但需要满足接口要求：

```cpp
// 示例：自定义原子包装器（仅用于说明，不推荐）
template <typename T>
struct CustomAtomic {
    std::atomic<T> impl_;
    
    T load(std::memory_order order = std::memory_order_seq_cst) const noexcept {
        return impl_.load(order);
    }
    
    void store(T desired, std::memory_order order = std::memory_order_seq_cst) noexcept {
        impl_.store(desired, order);
    }
    
    T fetch_add(T arg, std::memory_order order = std::memory_order_seq_cst) noexcept {
        return impl_.fetch_add(arg, order);
    }
    
    bool compare_exchange_strong(
        T& expected, T desired,
        std::memory_order success,
        std::memory_order failure) noexcept {
        return impl_.compare_exchange_strong(expected, desired, success, failure);
    }
    
    // ... 其他必需的接口
};

// 使用（不推荐，除非有特殊需求）
UMPMCQueue<int, true, 8, 7, CustomAtomic> queue;
```

**特点：**
- ⚠️ 需要实现完整的原子操作接口
- ⚠️ 必须保证操作是线程安全的
- ⚠️ 可能不是 lock-free 的（取决于实现）
- ❌ **不推荐**：除非有特殊需求

##### 4. 非原子类型（错误用法）

```cpp
// 错误：非原子类型
template <typename T>
struct NonAtomic {
    T value_;
    // 没有原子操作，不是线程安全的
};

// 这样使用会导致未定义行为！
// UMPMCQueue<int, true, 8, 7, NonAtomic> queue;  // ❌ 危险！
```

**特点：**
- ❌ 不是线程安全的
- ❌ 不是 lock-free 的
- ❌ 会导致数据竞争和未定义行为
- ❌ **绝对不能使用**

##### 5. 平台特定的原子类型

某些平台可能提供特定的原子类型实现：

```cpp
// 示例：某些平台特定的原子类型（如果存在）
// UMPMCQueue<int, true, 8, 7, PlatformSpecificAtomic> queue;
```

**特点：**
- ⚠️ 平台特定，可移植性差
- ⚠️ 需要仔细验证接口兼容性
- ⚠️ 可能提供性能优势（取决于平台）

#### Atom 参数的要求

`Atom` 必须是一个模板类，满足以下接口要求：

```cpp
template <typename T>
class Atom {
public:
    // 必需的操作
    T load(std::memory_order order) const noexcept;
    void store(T desired, std::memory_order order) noexcept;
    T fetch_add(T arg, std::memory_order order) noexcept;
    bool compare_exchange_strong(
        T& expected, T desired,
        std::memory_order success,
        std::memory_order failure) noexcept;
    
    // 可选但推荐的操作
    T fetch_sub(T arg, std::memory_order order) noexcept;
    bool compare_exchange_weak(...) noexcept;
    T exchange(T desired, std::memory_order order) noexcept;
};
```

#### 实际使用建议

**推荐做法：**

```cpp
// 1. 使用默认值（std::atomic）
UMPMCQueue<int> queue;  // ✅ 推荐

// 2. 显式指定 std::atomic（如果需要明确）
UMPMCQueue<int, false, false, true, 8, 7, std::atomic> queue;  // ✅ 推荐

// 3. 使用 folly::atomic（如果使用 Folly 且需要优化）
UMPMCQueue<int, false, false, true, 8, 7, folly::atomic> queue;  // ✅ 可选
```

**不推荐做法：**

```cpp
// ❌ 不要传入非原子类型
// UMPMCQueue<int, false, false, true, 8, 7, NonAtomic> queue;

// ❌ 不要传入未经验证的自定义类型
// UMPMCQueue<int, false, false, true, 8, 7, CustomAtomic> queue;
```

### 3. UnboundedQueue 的同步机制

#### 生产者操作（enqueue）

```cpp
template <typename Arg>
void enqueueImpl(Arg&& arg) {
    // 1. 使用 hazard pointer 保护（无锁）
    hazptr_holder<Atom> hptr = make_hazard_pointer<Atom>();
    Segment* s = hptr.protect(p_.tail);
    
    // 2. 原子操作获取票号
    Ticket t = fetchIncrementProducerTicket();
    // SP: 直接 store
    // MP: fetch_add (lock-free)
    
    // 3. CAS 设置 next 指针（lock-free）
    if (!s->casNextSegment(next)) {
        // 其他线程已设置，使用已设置的段
    }
    
    // 4. CAS 推进 tail（lock-free）
    casTail(s, next);
}
```

**分析：**
- ✅ 使用 `Atom::fetch_add`（多生产者时，如果 `Atom = std::atomic` 则是 lock-free）
- ✅ 使用 `Atom::compare_exchange_strong`（如果 `Atom = std::atomic` 则是 lock-free）
- ✅ 使用 hazard pointer（无锁内存回收）
- ✅ **没有使用互斥锁**
- ✅ **生产者操作完全无锁**（前提：`Atom = std::atomic`）

#### 消费者操作（dequeue）

```cpp
T dequeueImpl() noexcept {
    // 1. 使用 hazard pointer 保护（无锁）
    hazptr_holder<Atom> hptr = make_hazard_pointer<Atom>();
    Segment* s = hptr.protect(c_.head);
    
    // 2. 原子操作获取票号
    Ticket t = fetchIncrementConsumerTicket();
    // SC: 直接 store
    // MC: fetch_add (lock-free)
    
    // 3. 等待元素可用
    Entry& e = s->entry(idx);
    auto res = e.takeItem();  // ← 关键：这里可能阻塞！
    
    // 4. CAS 推进 head（lock-free）
    if (responsibleForAdvance(t)) {
        advanceHead(s);
    }
}
```

**关键：`Entry::takeItem()`**

```cpp
class Entry {
    Sem flag_;  // SaturatingSemaphore
    
    T takeItem() noexcept {
        flag_.wait();  // ← 这里可能阻塞！
        return getItem();
    }
};
```

**`SaturatingSemaphore::wait()` 的行为：**

取决于 `MayBlock` 模板参数：

```cpp
// 如果 MayBlock = false
flag_.wait() {
    // 只自旋，不阻塞
    while (!flag_.try_wait()) {
        spin_pause();
    }
}

// 如果 MayBlock = true
flag_.wait() {
    // 可能使用 futex 阻塞
    if (!flag_.try_wait()) {
        futex_wait(...);  // ← 可能阻塞！
    }
}
```

### 4. Atom 和 MayBlock 的组合影响

#### 情况 1：Atom = std::atomic, MayBlock = false

```cpp
UMPMCQueue<int, false, 8, 7, std::atomic> queue;
```

**分析：**
- ✅ `Atom = std::atomic` → 原子操作是 lock-free 的
- ✅ `MayBlock = false` → 不阻塞，只自旋
- ✅ **完全无锁**

#### 情况 2：Atom = std::atomic, MayBlock = true

```cpp
UMPMCQueue<int, true, 8, 7, std::atomic> queue;
```

**分析：**
- ✅ `Atom = std::atomic` → 原子操作是 lock-free 的
- ⚠️ `MayBlock = true` → 可能阻塞（使用 futex）
- ⚠️ **原子操作无锁，但整体可能阻塞**

#### 情况 3：Atom = 非原子类型（假设）

```cpp
// 假设有人传入非原子类型（通常不会这样做）
// UMPMCQueue<int, false, 8, 7, NonAtomicWrapper> queue;
```

**分析：**
- ❌ `Atom` 不是原子类型 → 原子操作不是 lock-free 的
- ❌ **整个队列不是无锁的**

### 5. 不同配置下的无锁性

#### SPSC + MayBlock = false

```cpp
USPSCQueue<int, false> queue;
```

**分析：**
- ✅ 生产者：无锁（单生产者，直接 store）
- ✅ 消费者：无锁（单消费者，直接 store，只自旋）
- ✅ **完全无锁**

#### SPSC + MayBlock = true

```cpp
USPSCQueue<int, true> queue;
```

**分析：**
- ✅ 生产者：无锁
- ⚠️ 消费者：可能阻塞（使用 futex）
- ⚠️ **生产者无锁，消费者可能阻塞**

#### MPMC + MayBlock = false

```cpp
UMPMCQueue<int, false> queue;
```

**分析：**
- ✅ 生产者：无锁（使用 `fetch_add` 和 CAS）
- ✅ 消费者：无锁（使用 `fetch_add` 和 CAS，只自旋）
- ✅ **完全无锁**

#### MPMC + MayBlock = true

```cpp
UMPMCQueue<int, true> queue;
```

**分析：**
- ✅ 生产者：无锁（使用 `fetch_add` 和 CAS）
- ⚠️ 消费者：可能阻塞（使用 futex）
- ⚠️ **生产者无锁，消费者可能阻塞**

### 6. 与 MPMCQueue 的对比

| 队列 | 生产者 | 消费者 | 整体 |
|------|--------|--------|------|
| **MPMCQueue** | 无锁 | 无锁 | ✅ 完全无锁 |
| **UnboundedQueue (MayBlock=false)** | 无锁 | 无锁 | ✅ 完全无锁 |
| **UnboundedQueue (MayBlock=true)** | 无锁 | 可能阻塞 | ⚠️ 部分无锁 |

**MPMCQueue 为什么完全无锁？**

```cpp
// MPMCQueue 使用 TurnSequencer
void enqueue(...) {
    sequencer_.waitForTurn(turn, ...);
    // TurnSequencer 使用自旋 + futex，但设计上保证无锁
}
```

**UnboundedQueue 的阻塞点：**

```cpp
// UnboundedQueue 使用 SaturatingSemaphore
T takeItem() {
    flag_.wait();  // 如果 MayBlock=true，可能阻塞
}
```

### 7. 阻塞 vs 无锁

**关键区别：**

| 特性 | 阻塞 | 无锁 |
|------|------|------|
| 线程状态 | 可能进入睡眠 | 始终运行 |
| 系统调用 | 可能调用 futex | 无系统调用 |
| 性能 | 低延迟，节省 CPU | 高吞吐，消耗 CPU |
| 适用场景 | 等待时间较长 | 等待时间较短 |

**为什么需要阻塞？**

- 如果队列经常为空，自旋会浪费 CPU
- 阻塞可以让出 CPU 给其他线程
- 适合等待时间较长的场景

**为什么需要无锁？**

- 避免上下文切换开销
- 适合高吞吐场景
- 适合等待时间很短的场景

### 8. 实际使用建议

#### 场景 1：高吞吐，低延迟

```cpp
// 使用无锁版本
UMPMCQueue<int, false> queue;  // MayBlock = false
```

- ✅ 完全无锁
- ✅ 最高性能
- ⚠️ 队列空时 CPU 会自旋

#### 场景 2：等待时间较长

```cpp
// 使用阻塞版本
UMPMCQueue<int, true> queue;  // MayBlock = true
```

- ✅ 节省 CPU（队列空时阻塞）
- ⚠️ 消费者可能阻塞（不是完全无锁）
- ✅ 适合等待时间较长的场景

#### 场景 3：SPSC 高性能

```cpp
// SPSC 无阻塞版本
USPSCQueue<int, false> queue;
```

- ✅ 完全无锁
- ✅ 性能最优（无原子操作开销）

## 总结

### UnboundedQueue 的无锁性（完整分析）

**无锁性的两个维度：**

1. **原子操作层面**：取决于 `Atom` 参数
   - `Atom = std::atomic`（默认）→ ✅ 原子操作是 lock-free 的
   - `Atom` 不是原子类型 → ❌ 原子操作不是 lock-free 的

2. **阻塞行为层面**：取决于 `MayBlock` 参数
   - `MayBlock = false` → ✅ 不阻塞，只自旋
   - `MayBlock = true` → ⚠️ 可能阻塞（使用 futex）

**综合判断：**

| Atom | MayBlock | 原子操作 | 阻塞行为 | 整体 |
|------|----------|---------|---------|------|
| `std::atomic` | `false` | ✅ lock-free | ✅ 不阻塞 | ✅ **完全无锁** |
| `std::atomic` | `true` | ✅ lock-free | ⚠️ 可能阻塞 | ⚠️ **部分无锁** |
| 非原子类型 | `false` | ❌ 不是 lock-free | ✅ 不阻塞 | ❌ **不是无锁** |
| 非原子类型 | `true` | ❌ 不是 lock-free | ⚠️ 可能阻塞 | ❌ **不是无锁** |

**关键理解：**
- ✅ **`Atom` 是决定无锁性的根本因素**（你的观察很准确！）
- ⚠️ **`MayBlock` 影响阻塞行为**（但不影响原子操作的无锁性）

### 与 MPMCQueue 的对比

- **MPMCQueue**：✅ 完全无锁（即使阻塞操作也设计为无锁）
- **UnboundedQueue (MayBlock=false)**：✅ 完全无锁
- **UnboundedQueue (MayBlock=true)**：⚠️ 部分无锁

### 选择建议

**默认使用（推荐）：**
```cpp
// 默认 Atom = std::atomic, MayBlock = true
UMPMCQueue<int> queue;  // 原子操作无锁，但可能阻塞
```

**完全无锁版本：**
```cpp
// Atom = std::atomic, MayBlock = false
UMPMCQueue<int, false> queue;  // ✅ 完全无锁
```

**关键点：**
- ✅ **`Atom` 参数**：决定原子操作是否无锁（默认 `std::atomic` 是无锁的）
- ⚠️ **`MayBlock` 参数**：决定是否阻塞（不影响原子操作的无锁性）
- ✅ 需要完全无锁 → 使用 `MayBlock = false`
- ✅ 需要节省 CPU → 使用 `MayBlock = true`（接受部分阻塞）
- ✅ 需要最高性能 → 使用 `MPMCQueue`（固定容量，完全无锁）

