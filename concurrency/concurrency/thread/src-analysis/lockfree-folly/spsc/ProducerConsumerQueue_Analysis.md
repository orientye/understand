# ProducerConsumerQueue 源码解析

## 概述

`ProducerConsumerQueue` 是 Facebook Folly 库中最简单的并发队列实现，专门针对**单生产者单消费者**即**SPSC**场景优化。

### 核心特性

- ✅ **SPSC 专用**：只支持一个生产者和一个消费者
- ✅ **无锁设计**：使用原子操作和内存序，无需互斥锁
- ✅ **高性能**：最简单的实现，性能最优
- ✅ **环形缓冲区**：固定大小，循环使用

## 与 MPMCQueue 和 UnboundedQueue 的对比

| 特性 | ProducerConsumerQueue | MPMCQueue | UnboundedQueue |
|------|----------------------|-----------|----------------|
| 生产者数量 | 1 | 多 | 多/1 |
| 消费者数量 | 1 | 多 | 多/1 |
| 容量 | 固定 | 固定 | 无界 |
| 同步机制 | 内存序 | TurnSequencer | SaturatingSemaphore |
| 复杂度 | 最低 | 中等 | 最高 |
| 性能 | 最高 | 高 | 中等 |

## 核心设计：环形缓冲区

### 数据结构

```cpp
template <class T>
struct ProducerConsumerQueue {
    const uint32_t size_;           // 缓冲区大小
    T* const records_;              // 元素数组
    AtomicIndex readIndex_;         // 读索引（消费者）
    AtomicIndex writeIndex_;        // 写索引（生产者）
};
```

### 环形缓冲区示意图

```
size_ = 8 的队列（实际可用容量 = 7）：

初始状态（空）：
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  0  │  1  │  2  │  3  │  4  │  5  │  6  │  7  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
  ↑
readIndex_ = 0
writeIndex_ = 0

写入 3 个元素后：
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  A  │  B  │  C  │  3  │  4  │  5  │  6  │  7  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
  ↑                           ↑
readIndex_ = 0          writeIndex_ = 3

读取 2 个元素后：
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│ 空  │ 空  │  C  │  3  │  4  │  5  │  6  │  7  │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
            ↑               ↑
      readIndex_ = 2  writeIndex_ = 3
```

## 关键设计：为什么容量是 size - 1？

### 问题：如何区分空和满？

如果 `readIndex_ == writeIndex_`，有两种可能：
1. **队列为空**：还没有写入任何元素
2. **队列为满**：所有位置都已写入

### 解决方案：保留一个空位

```cpp
// 实际可用容量
size_t capacity() const { return size_ - 1; }
```

**规则：**
- 如果 `(writeIndex_ + 1) % size_ == readIndex_` → **队列满**
- 如果 `writeIndex_ == readIndex_` → **队列空**

**示例：** `size_ = 8`

```
空队列：
readIndex_ = 0, writeIndex_ = 0
→ 空

满队列（7 个元素）：
readIndex_ = 0, writeIndex_ = 7
→ (7 + 1) % 8 = 0 == readIndex_ → 满
```

## 核心操作

### 1. 写入（write）

```cpp
template <class... Args>
bool write(Args&&... recordArgs) {
    // 1. 获取当前写索引
    auto const currentWrite = writeIndex_.load(std::memory_order_relaxed);
    
    // 2. 计算下一个位置（环形）
    auto nextRecord = currentWrite + 1;
    if (nextRecord == size_) {
        nextRecord = 0;
    }
    
    // 3. 检查是否满（关键：检查下一个位置）
    if (nextRecord != readIndex_.load(std::memory_order_acquire)) {
        // 4. 构造元素
        new (&records_[currentWrite]) T(std::forward<Args>(recordArgs)...);
        
        // 5. 更新写索引（release 确保元素构造完成）
        writeIndex_.store(nextRecord, std::memory_order_release);
        return true;
    }
    
    // 队列满
    return false;
}
```

**内存序说明：**
- `memory_order_relaxed`：读取自己的索引，无需同步
- `memory_order_acquire`：读取对方的索引，需要看到最新值
- `memory_order_release`：更新索引，确保元素构造完成后才可见

### 2. 读取（read）

```cpp
bool read(T& record) {
    // 1. 获取当前读索引
    auto const currentRead = readIndex_.load(std::memory_order_relaxed);
    
    // 2. 检查是否空
    if (currentRead == writeIndex_.load(std::memory_order_acquire)) {
        return false;  // 队列空
    }
    
    // 3. 计算下一个位置
    auto nextRecord = currentRead + 1;
    if (nextRecord == size_) {
        nextRecord = 0;
    }
    
    // 4. 移动元素并析构
    record = std::move(records_[currentRead]);
    records_[currentRead].~T();
    
    // 5. 更新读索引（release 确保析构完成）
    readIndex_.store(nextRecord, std::memory_order_release);
    return true;
}
```

### 3. 原地访问（frontPtr + popFront）

```cpp
// 获取队首元素指针（不移动）
T* frontPtr() {
    auto const currentRead = readIndex_.load(std::memory_order_relaxed);
    if (currentRead == writeIndex_.load(std::memory_order_acquire)) {
        return nullptr;  // 队列空
    }
    return &records_[currentRead];
}

// 弹出队首元素（已通过 frontPtr 访问过）
void popFront() {
    auto const currentRead = readIndex_.load(std::memory_order_relaxed);
    assert(currentRead != writeIndex_.load(std::memory_order_acquire));
    
    auto nextRecord = currentRead + 1;
    if (nextRecord == size_) {
        nextRecord = 0;
    }
    records_[currentRead].~T();
    readIndex_.store(nextRecord, std::memory_order_release);
}
```

**使用场景：** 需要先查看元素再决定是否弹出

## 内存序详解

### 为什么需要内存序？

在 SPSC 场景下，虽然只有一个生产者和一个消费者，但需要确保：
1. **生产者写入的元素**在更新 `writeIndex_` 之前完全构造
2. **消费者读取的元素**在更新 `readIndex_` 之前完全析构

### 内存序的作用

```
生产者线程：
┌─────────────────────────────────────┐
│ 1. 构造元素                          │
│    new (&records_[i]) T(...)        │
│                                      │
│ 2. 更新 writeIndex_ (release)        │
│    └─ 确保步骤 1 在步骤 2 之前完成   │
└─────────────────────────────────────┘
              ↓ (release 建立 happens-before)
┌─────────────────────────────────────┐
│ 消费者线程：                          │
│ 1. 读取 writeIndex_ (acquire)        │
│    └─ 确保看到步骤 2 的结果           │
│                                      │
│ 2. 读取元素                          │
│    └─ 此时元素已完全构造              │
└─────────────────────────────────────┘
```

### 内存序选择

| 操作 | 内存序 | 原因 |
|------|--------|------|
| 读取自己的索引 | `relaxed` | 不需要同步，只读自己的状态 |
| 读取对方的索引 | `acquire` | 需要看到对方的最新更新 |
| 更新自己的索引 | `release` | 确保之前的操作完成后再更新 |

## 性能优化

### 1. 缓存行对齐

```cpp
char pad0_[hardware_destructive_interference_size];
const uint32_t size_;
T* const records_;

alignas(hardware_destructive_interference_size) AtomicIndex readIndex_;
alignas(hardware_destructive_interference_size) AtomicIndex writeIndex_;

char pad1_[hardware_destructive_interference_size - sizeof(AtomicIndex)];
```

**目的：** 避免 `readIndex_` 和 `writeIndex_` 在同一个缓存行，减少 false sharing

### 2. 无锁设计

- 无需互斥锁
- 无需 CAS 循环
- 只需简单的原子加载/存储

### 3. 最小化内存屏障

- 只在必要时使用 `acquire/release`
- 自己的索引使用 `relaxed`（最快）

## 使用示例

```cpp
// 创建队列（容量 = 7）
ProducerConsumerQueue<int> queue(8);

// 生产者线程
void producer() {
    for (int i = 0; i < 100; ++i) {
        while (!queue.write(i)) {
            // 队列满，等待或重试
            std::this_thread::yield();
        }
    }
}

// 消费者线程
void consumer() {
    int value;
    while (true) {
        if (queue.read(value)) {
            // 处理 value
            process(value);
        } else {
            // 队列空，等待或退出
            if (should_exit) break;
            std::this_thread::yield();
        }
    }
}
```

## 限制和注意事项

### 1. 必须是 SPSC

- ❌ 不能有多个生产者
- ❌ 不能有多个消费者
- ✅ 只能有一个生产者和一个消费者

### 2. 容量限制

- 实际可用容量 = `size - 1`
- 如果 `size = 8`，只能存储 7 个元素

### 3. 非阻塞

- `write()` 和 `read()` 都是非阻塞的
- 如果队列满/空，立即返回 `false`
- 需要调用者自己处理重试

### 4. 析构顺序

```cpp
~ProducerConsumerQueue() {
    // 需要手动析构剩余元素
    if (!std::is_trivially_destructible<T>::value) {
        size_t readIndex = readIndex_;
        size_t endIndex = writeIndex_;
        while (readIndex != endIndex) {
            records_[readIndex].~T();
            if (++readIndex == size_) {
                readIndex = 0;
            }
        }
    }
    std::free(records_);
}
```

## 与其他队列的对比

### ProducerConsumerQueue vs MPMCQueue (SPSC)

| 特性 | ProducerConsumerQueue | MPMCQueue (SPSC) |
|------|----------------------|------------------|
| 实现复杂度 | 简单 | 复杂 |
| 性能 | 更高 | 稍低 |
| 内存使用 | 更少 | 更多（padding） |
| 功能 | 基础 | 丰富（阻塞、超时等） |

**选择建议：**
- 如果确定是 SPSC 场景 → 使用 `ProducerConsumerQueue`
- 如果需要阻塞、超时等功能 → 使用 `MPMCQueue` 或 `UnboundedQueue`

## 总结

**ProducerConsumerQueue 的核心优势：**

1. **极简设计**：环形缓冲区 + 两个索引
2. **无锁高效**：最小化同步开销
3. **SPSC 专用**：针对单生产者单消费者优化
4. **内存友好**：缓存行对齐，避免 false sharing

**适用场景：**
- ✅ 单生产者单消费者
- ✅ 需要最高性能
- ✅ 容量可预估
- ✅ 可以接受非阻塞设计

**不适用场景：**
- ❌ 多生产者或多消费者
- ❌ 需要阻塞操作
- ❌ 需要超时机制

这是 Folly 队列家族中最简单但性能最高的实现！

