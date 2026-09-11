[1mdiff --git a/ai/reinforcement-learning.asc b/ai/reinforcement-learning.asc[m
[1mindex 6a68101e..8ae0cceb 100644[m
[1m--- a/ai/reinforcement-learning.asc[m
[1m+++ b/ai/reinforcement-learning.asc[m
[36m@@ -9,9 +9,8 @@[m
 :stem: latexmath[m
 [m
 == 概念[m
[31m-reinforcement-learning:[m
[32m+[m[32m- reinforcement-learning[m
 learning through experience/data to make good decisions under uncertainty[m
[31m-[m
 在强化学习问题中，智能体(agent)在一系列的时间步骤上与环境交互。在每个特定时间点，智能体从环境接收一些观察(observation)，并且必须选择一个动作(action)，然后通过某种机制(有时称为执行器)将其传输回环境，最后智能体从环境中获得奖励(reward)。此后新一轮循环开始，智能体接收后续观察，并选择后续操作，依此类推。[m
 [m
 - Two Problem Categories Where RL is Particularly Powerful[m
[36m@@ -33,7 +32,7 @@[m [mlearning through experience/data to make good decisions under uncertainty[m
         表格法对每个状态独立记忆、不泛化；状态多到存不下或访不全时，才必须靠函数近似跨状态推广。[m
         一般手段：用函数近似器（Function Approximator）共享参数/特征，把已访状态上的价值或策略估计推广到相近、未见过的状态（注意：表示光滑 ≠ 相近状态必须输出相近动作）。形式不限于 DNN——线性 FA、tile coding、RBF 等早已存在，深度网络只是高维观测下的主流选择。过度泛化可能混淆策略上关键的不同状态（state aliasing）；与自举、离策略结合时还可能触发 deadly triad 不稳定。[m
 [m
[31m-强化学习的一些特征：[m
[32m+[m[32m- 强化学习的一些特征：[m
 （1）强化学习会试错探索，它通过探索环境来获取对环境的理解。[m
 （2）强化学习智能体会从环境里面获得延迟的奖励。[m
 （3）在强化学习的训练过程中，时间非常重要。因为得到的是有时间关联的数据（sequential data），而不是独立同分布的数据。在机器学习中，如果观测数据有非常强的关联，会使得训练非常不稳定。[m
[36m@@ -45,7 +44,7 @@[m [mlearning through experience/data to make good decisions under uncertainty[m
 当没有状态、只有一组最初未知回报的可用动作时，这个问题就是经典的多臂赌博机(multi-armed bandit)。[m
 例：一排老虎机，拉哪根杆事先不知道谁吐币多。没有「当前局面」，只有 k 个动作；每次拉完立刻出分，下一把还是同一排机，不因上次拉了哪根而换环境。[m
 [m
[31m-Q: 对于路径规划问题，A*算法与强化学习有哪些区别？[m
[32m+[m[32m- Q: 对于路径规划问题，A*算法与强化学习有哪些区别？[m
 | 维度 | 强化学习 (RL) | A* 算法 |[m
 | 核心目标 | 学一个通用策略，适应动态/不确定环境 | 找一条单次(近似)最优路径（静态、全图已知） |[m
 | 工作方式 | 试错交互，靠奖励信号反馈 | 靠启发式函数 + 实际代价，全图已知 |[m
[36m@@ -70,7 +69,6 @@[m [mGₜ = Rₜ₊₁ + γGₜ₊₁ 或者写成 Gₜ = Rₜ₊₁ + γRₜ₊₂ +[m
 [m
 - 稠密奖励(Dense Reward)与稀疏奖励(Sparse Reward)[m
 | 特性 | 稠密奖励 (Dense Reward) | 稀疏奖励 (Sparse Reward) |[m
[31m-|------|-------------------------|--------------------------|[m
 | 反馈频率 | 几乎每步都有可学习的信号 | 只有成功/失败等关键事件才给 |[m
 | 典型代表 | CartPole（每活一步 +1） | 到达目标才 +1，此前全是 0 |[m
 | 训练难度 | 较低，走一步能修正一步 | 高，容易长时间没有任何反馈 |[m
[36m@@ -101,29 +99,25 @@[m [mQ: 强化学习比深度学习复杂在哪里？[m
         *** 模型要学：MuZero、World Models、Dreamer、MBPO。风险是模型偏差(Model Bias)。[m
 [m
 * 按学习对象（model-free 下的主流划分）[m
[31m-[m
 | 流派 | 学习对象 | 核心问题 | 典型算法 |[m
[31m-|------|----------|----------|----------|[m
 | Value-based | 价值函数（V 或 Q） | 哪个动作价值最高？ | Q-learning、DQN、Double DQN |[m
 | Policy-based | 策略函数 π | 该怎么做？（直接学动作分布） | REINFORCE |[m
 | Actor-Critic | 价值 + 策略 | 价值评估 + 策略改进 | A2C、PPO、SAC |[m
[31m-[m
[31m-PPO 是带 clip 的策略梯度，实现上几乎总是 Actor-Critic（用 critic 算优势）。SAC 同样是带价值网络的 Actor-Critic。二者与「纯策略梯度」（如不带 critic 的 REINFORCE）有交叉，不是互斥标签。[m
[32m+[m[32mPPO 是带 clip 的策略梯度，实现上几乎总是 Actor-Critic（用 critic 算优势）。SAC 同样是带价值网络的 Actor-Critic。二者与「纯策略梯度」（如不带 critic 的 REINFORCE）有交叉，不是互斥。[m
 [m
 * 按经验来自哪条策略（≠ 还能不能和环境交互）[m
     ** 在策略 (On-policy)：只用当前策略采到的数据更新。例子：SARSA、PPO。[m
     ** 离策略 (Off-policy)：可用其他策略（旧策略、行为策略、别人的轨迹）的数据。例子：Q-learning、DQN、DDPG。[m
     ** 在线 (Online) vs 离线 (Offline / batch RL)：还能不能继续与环境交互。DQN 是离策略且在线（一边玩一边从 replay 学）。CQL、IQL 才是离线强化学习。[m
 [m
[31m-Q: 什么时候用 Q，什么时候用 V？[m
[32m+[m[32m- Q: 什么时候用 Q，什么时候用 V？[m
 假设站在悬崖边，面前有一个问号块：[m
[31m-[m
 | 函数 | 值 | 含义 |[m
 |------|-----|------|[m
 | V(s) | 10 分 | 站在这个位置，不管怎么玩，平均能拿 10 分 |[m
 | Q(s, 跳) | 15 分 | 若选择跳，预期能拿 15 分 |[m
 | Q(s, 跑) | −100 分 | 若选择跑，预期掉悬崖得 −100 分 |[m
[31m-[m
[32m+[m[32m|------|--------|------|[m
 | 场景 | 用什么 | 原因 |[m
 |------|--------|------|[m
 | 需要选动作（决策） | Q | 比较每个动作的 Q，选最大 |[m
