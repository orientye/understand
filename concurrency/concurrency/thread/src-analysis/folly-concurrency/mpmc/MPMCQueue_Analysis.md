# MPMCQueue 源码解析

## 概述

`MPMCQueue` 是 Facebook Folly 库中的高性能有界并发队列，支持：
- **多生产者多消费者 (MPMC)**
- **固定容量**（或动态扩展）
- **可选的阻塞操作**
- **线性化保证**

## 核心设计思想

### 1. 票号系统 (Ticket System)

队列使用**票号分发器 (ticket dispenser)** 来分配队列位置：
- `pushTicket_`: 生产者获取的递增票号
- `popTicket_`: 消费者获取的递增票号
- 每个操作都有唯一的票号，保证顺序

### 2. 单元素队列数组

队列内部由多个 `SingleElementQueue` 组成：
- 每个槽位是一个单元素队列
- 通过 `stride` 计算避免缓存行冲突（false sharing）
- 使用 `kSlotPadding` 在数组两端填充，进一步避免 false sharing

### 3. 线性化保证

代码注释明确说明：
> "if a call to write(A) returns before a call to write(B) begins, then A will definitely end up in the queue before B"

这保证了操作的顺序性。

## 主要组件

### 1. MPMCQueueBase (CRTP 基类)

使用 **CRTP (Curiously Recurring Template Pattern)** 设计：

```cpp
template <typename Derived>
class MPMCQueueBase<Derived<T, Atom, Dynamic, Allocator>>
```

**关键成员变量：**
- `capacity_`: 队列容量
- `slots_` / `dslots_`: 槽位数组（静态/动态版本）
- `stride_` / `dstride_`: 步长，用于避免缓存冲突
- `pushTicket_` / `popTicket_`: 票号分发器
- `pushSpinCutoff_` / `popSpinCutoff_`: 自适应自旋阈值

**关键方法：**
- `size()`: 计算队列大小（通过比较 pushTicket 和 popTicket）
- `blockingWrite()`: 阻塞写入
- `write()`: 非阻塞写入（如果可能）
- `blockingRead()`: 阻塞读取
- `read()`: 非阻塞读取（如果可能）

### 2. SingleElementQueue

每个槽位的实现，使用 `TurnSequencer` 来同步：

```cpp
struct SingleElementQueue {
    aligned_storage_for_t<T> contents_;  // 存储元素
    TurnSequencer<Atom> sequencer_;      // 轮次序列器
};
```

**关键特性：**
- 支持两种入队方式：
  - **移动构造**（如果 `is_nothrow_move_constructible`）
  - **重定位模拟**（如果 `IsRelocatable`）
- 支持两种出队方式：
  - **重定位**（如果 `IsRelocatable`，性能更好）
  - **移动赋值**（否则）

### 3. 步长计算 (Stride Computation)

```cpp
static int computeStride(size_t capacity) noexcept
```

**目的：** 避免 false sharing

**策略：**
- 使用小质数作为候选步长
- 选择与容量互质且分离度最大的步长
- 确保 `gcd(capacity, stride) == 1`，这样所有槽位都会被使用

### 4. 索引和轮次计算

```cpp
size_t idx(uint64_t ticket, size_t cap, int stride) noexcept {
    return ((ticket * stride) % cap) + kSlotPadding;
}

uint32_t turn(uint64_t ticket, size_t cap) noexcept {
    return uint32_t(ticket / cap);
}
```

- `idx()`: 将票号映射到槽位索引
- `turn()`: 计算轮次（每个槽位会重复使用，用轮次区分）

## 操作流程

### 写入流程

1. **获取票号**: `pushTicket_++`
2. **计算槽位**: `idx(ticket, capacity, stride)`
3. **等待轮次**: 通过 `TurnSequencer` 等待对应轮次
4. **构造元素**: 在槽位中构造元素
5. **完成轮次**: 通知等待的读者

### 读取流程

1. **获取票号**: `popTicket_++`
2. **计算槽位**: `idx(ticket, capacity, stride)`
3. **等待轮次**: 等待对应轮次（确保元素已写入）
4. **提取元素**: 移动或重定位元素
5. **完成轮次**: 通知等待的写者

## 动态版本 (Dynamic MPMCQueue)

### 设计特点

使用 **seqlock** 机制实现无锁扩展：

```cpp
template <typename T, template <typename> class Atom, class Allocator>
class MPMCQueue<T, Atom, true, Allocator>  // Dynamic = true
```

**关键机制：**

1. **Seqlock**: 
   - 低 6 位：锁状态和已关闭数组数量
   - 高位：票号偏移量

2. **ClosedArray**: 存储已关闭的旧数组信息
   - 供滞后操作使用（票号小于当前偏移的操作）

3. **扩展流程**:
   ```cpp
   bool tryExpand(const uint64_t state, const size_t cap) noexcept
   ```
   - 获取 seqlock
   - 分配新数组
   - 将旧数组信息存入 `closed_`
   - 更新票号偏移量
   - 释放 seqlock

### 滞后操作处理

```cpp
bool maybeUpdateFromClosed(...)
```

如果操作的票号小于当前偏移，需要从 `closed_` 数组中找到对应的旧数组。

## 性能优化

### 1. 自适应自旋

```cpp
Atom<uint32_t> pushSpinCutoff_;
Atom<uint32_t> popSpinCutoff_;
```

- 每 `kAdaptationFreq` (128) 次操作，尝试更长的自旋
- 使用指数移动平均平滑调整
- 减少不必要的系统调用

### 2. 缓存行对齐

```cpp
alignas(hardware_destructive_interference_size)
```

关键变量按缓存行对齐，避免 false sharing。

### 3. Futex 支持

`TurnSequencer` 内部使用 `futex()` 的 `_BITSET` 操作：
- 减少不必要的唤醒
- 比 `sched_yield` 更高效

## 异常安全

### Noexcept 要求

代码强制要求：
```cpp
static_assert(
    std::is_nothrow_constructible<T, T&&>::value ||
        folly::IsRelocatable<T>::value,
    "T must be relocatable or have a noexcept move constructor");
```

**原因：** 票号系统将位置分配与元素构造分离，构造必须在已分配的槽位中进行，不能抛出异常。

### 解决方案

1. **移动构造**（如果 noexcept）
2. **重定位模拟**（如果 `IsRelocatable`）：
   - 使用 `memcpy` 模拟移动
   - 然后在新位置默认构造

## 使用场景

### 静态版本
- 容量固定
- 内存预先分配
- 性能最优

### 动态版本（已弃用）
- 容量可扩展
- 使用 `UnboundedQueue` 替代

## 关键设计模式

1. **CRTP**: 静态多态，避免虚函数开销
2. **Seqlock**: 动态版本的读多写少场景
3. **Ticket System**: 保证顺序性
4. **Turn Sequencer**: 单元素队列的同步机制

## 总结

`MPMCQueue` 是一个精心设计的高性能并发队列：

- ✅ **线性化保证**：严格的顺序性
- ✅ **高性能**：避免 false sharing，自适应自旋
- ✅ **灵活性**：支持阻塞/非阻塞操作
- ✅ **类型安全**：编译时检查 noexcept 要求

适合需要严格顺序保证和高性能的生产者-消费者场景。

