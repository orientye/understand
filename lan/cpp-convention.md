# 说明
- 规范与建议以Google代码规范为基础, 以Effective系列等作为补充(去掉了重合的, 过时的, 基本可以省略的内容)
- Google代码规范的注释及格式等部分考虑使用cpplint工具来完成
- 版本: 1.0.0  最后更新: 2021-09-01 13:01

# Google代码规范
- https://google.github.io/styleguide/cppguide.html
- 中文版: https://google-styleguide.readthedocs.io/zh_CN/latest/google-cpp-styleguide/contents.html (注意:有些并不准确)

# Effective C++ 3rd
- Item 04.  确定对象被使用前已被初始化
- Item 07.  为多态基类声明virtual析构函数
- Item 09.  绝不在构造函数和析构函数中调用virtual函数
- Item 11.  operator=处理好自我赋值
- Item 12.  复制对象时勿忘其每一个成分
- Item 16.  成对使用new和delete要采取相同形式
- Item 21.  绝不返回局部变量(local stack)的指针或引用
- Item 26.  尽可能延后变量定义的出现时间
- Item 28.  避免返回handles(包括引用指针迭代器)指向对象内部
- Item 35.  考虑virtual以外的其它选择  TIPS: 函数指针; std::bind, std::function; CRTP; MFC消息映射表等
- Item 53.  重视编译器警告

# More Effective C++
- Item M3.  不要对数组使用多态
- Item M4.  避免无用的缺省构造函数
- Item M5.  谨慎定义类型转换函数
- Item M6.  尽量使用前缀自增自减
- Item M13. 通过引用(reference)捕获异常
- Item M24. 理解虚拟函数、多继承、虚基类和RTTI所需的代价

# Effective STL
- 条款04.  用empty来代替检查size()是否为0
- 条款05.  区间成员函数优先于与之对应的单元素成员函数
- 条款09.  慎重选择删除元素的方法
- 条款14.  使用reserve来避免不必要的重新分配
- 条款22.  切勿直接修改set或multiset中的键
- 条款32.  如果确实需要删除元素, 则需要在remove这一类算法之后调用erase
- 条款33.  对包含指针的容器使用remove这一类算法时要特别小心
- 条款44.  容器的成员函数优先于同名的算法

# Effective Modern C++
1. __类型推导__
	1. [Item 1:理解模板类型推导](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/1.DeducingTypes/item1.md) 已修订
	2. [Item 2:理解auto类型推导](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/1.DeducingTypes/item2.md)
	3. [Item 3:理解decltype](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/1.DeducingTypes/item3.md)
	4. [Item 4:学会查看类型推导结果](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/1.DeducingTypes/item4.md)
2. __auto__
	1. [Item 5:优先考虑auto而非显式类型声明](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/2.Auto/item5.md)
	2. [Item 6:auto推导若非己愿，使用显式类型初始化惯用法](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/2.Auto/item6.md)
3. __移步现代C++__
	1. [Item 7:区别使用()和{}创建对象](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item7.md)
	2. [Item 8:优先考虑nullptr而非0和NULL](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item8.md)
	3. [Item 9:优先考虑别名声明而非typedefs](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item9.md)
	4. [Item 10:优先考虑限域枚举而非未限域枚举](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item10.md) 已修订
	5. [Item 11:优先考虑使用deleted函数而非使用未定义的私有声明](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item11.md)
	6. [Item 12:使用override声明重载函数](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item12.md)
	7. [Item 13:优先考虑const_iterator而非iterator](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item13.md)
	8. [Item 14:如果函数不抛出异常请使用noexcept](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item14.md)
	9. [Item 15:尽可能的使用constexpr](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item15.md)
	10. [Item 16:让const成员函数线程安全](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item16.md) 由 @windski贡献
	11. [Item 17:理解特殊成员函数函数的生成](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/3.MovingToModernCpp/item17.md) 
4. __智能指针__
	1. [Item 18:对于独占资源使用std::unique_ptr](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/4.SmartPointers/item18.md) 由 @wendajiang贡献
	2. [Item 19:对于共享资源使用std::shared_ptr](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/4.SmartPointers/item19.md) 已修订
	3. [Item 20:当std::shard_ptr可能悬空时使用std::weak_ptr](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/4.SmartPointers/item20.md) 更新完成
	4. [Item 21:优先考虑使用std::make_unique和std::make_shared而非new](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/4.SmartPointers/item21.md) 由 @pusidun贡献
	5. [Item 22:当使用Pimpl惯用法，请在实现文件中定义特殊成员函数](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/4.SmartPointers/item22.md) 由 @BlurryLight贡献
5. __右值引用，移动语义，完美转发__
	1. [Item 23:理解std::move和std::forward](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item23.md) 由 @BlurryLight贡献
	2. [Item 24:区别通用引用和右值引用](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item24.md) 由 @BlurryLight贡献
	3. [Item 25:对于右值引用使用std::move，对于通用引用使用std::forward](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item25.md)由 @wendajiang贡献
	4. [Item 26:避免重载通用引用](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item26.md) 由 @wendajiang贡献
	5. [Item 27:熟悉重载通用引用的替代品](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item27.md) 由 @wendajiang贡献
	6. [Item 28:理解引用折叠](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item28.md) 由 @wendajiang贡献
	7. [Item 29:认识移动操作的缺点](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item29.md) 由 @wendajiang贡献
	8. [Item 30:熟悉完美转发失败的情况](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/5.RRefMovSemPerfForw/item30.md) 由 @wendajiang贡献
6. __Lambda表达式__
	1. [Item 31:避免使用默认捕获模式](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/6.LambdaExpressions/item31.md) 由 @LucienXian贡献
	2. [Item 32:使用初始化捕获来移动对象到闭包中](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/6.LambdaExpressions/item32.md) 由 @LucienXian贡献
	3. [Item 33:对于std::forward的auto&&形参使用decltype](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/6.LambdaExpressions/item33.md) 由 @LucienXian贡献
	4. [Item 34:优先考虑lambda表达式而非std::bind](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/6.LambdaExpressions/item34.md) 由 @LucienXian贡献
7. __并发API__
	1. [Item 35:优先考虑基于任务的编程而非基于线程的编程](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/Item35.md) 由 @wendajiang贡献
	2. [Item 36:如果有异步的必要请指定std::launch::threads](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/item36.md) 由 @wendajiang贡献
	3. [Item 37:从各个方面使得std::threads unjoinable](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/item37.md) 由 @wendajiang贡献
	4. [Item 38:关注不同线程句柄析构行为](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/item38.md) 由 @wendajiang贡献
	5. [Item 39:考虑对于单次事件通信使用void](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/item39.md) 由 @wendajiang贡献
	6. [Item 40:对于并发使用std::atomic，volatile用于特殊内存区](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/7.TheConcurrencyAPI/item40.md) 由 @wendajiang贡献
8. __微调__
	1. [Item 41:对于那些可移动总是被拷贝的形参使用传值方式](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/8.Tweaks/item41.md) 由 @wendajiang贡献
	2. [Item 42:考虑就地创建而非插入](https://github.com/kelthuzadx/EffectiveModernCppChinese/blob/master/8.Tweaks/item42.md) 由 @wendajiang贡献

# C++ Coding Standards
- Item004. 在代码审查上投入
- Item039. 考虑将虚拟函数声明为非公用的, 将公用函数声明为非虚拟的(TIPS: 基类析构函数除外)
- Item054. 避免切片
- Item054. 使用赋值的标准形式
- Item060. 要避免在不同的模块中分配和释放内存
- Item061. 不要在头文件中定义具有链接的实体
- Item062. 不要允许异常跨越边界传播
- Item063. 在模块的接口中使用具有良好的可移植性的类型
- Item090. 避免使用类型分支, 多使用多态
- Item096. 不要对非POD进行memcpy/memcmp

# 内存
- [强制] 严禁两次及以上的free/delete(同时, 应当优先选择智能指针)  Q: 会出现什么问题?
- [建议] 不要重载全局::operator new()等函数

# STL
- vector: push_back/[]/emplace/emplace_back/at
- map: find/[]/insert/at/emplace

# 并发
- [建议] 优先使用消息传递而不是共享内存(使用通信来共享内存, 而不是通过共享内存来通信)/尽量无状态/尽量不可变(immutable)状态
- [建议] 优先使用Socket(TCP)
- [建议] 如果必须共享状态, 尽量使用消息队列/任务队列等公用组件
- [建议] 互斥尽量使用Mutex, 并尽量使用非递归锁
- [建议] 深入理解condition-variable
- [建议] 深入理解rwlock
- [建议] 深入理解spinlock
- [建议] 深入理解volatile, 一般情况下不应使用volatile
- [建议] 一般只有基础库才需要使用atomic与memory-order
- [建议] 一般只有基础库才需要使用lock-free, lock-free的正确性应当得到充分验证
- [建议] signal要考虑异步信号安全, 可以考虑libuv的处理方式
- linux async-signal-safe系统函数 http://man7.org/linux/man-pages/man7/signal-safety.7.html
- linux 非线程安全函数 https://man7.org/linux/man-pages/man7/pthreads.7.html
- [建议] 借助工具/库来检测锁缺失, 死锁等并发问题

# 工具
- cpplint
    - [建议] cpplint标准比较严格, 可以保持代码风格的一致性
    - [建议] 可以添加少量的filter, 让所有检查通过
- Sanitizer
- cmake
    - [建议] Effective Modern CMake: https://gist.github.com/mbinna/c61dbb39bca0e4fb7d1f73b0d66a4fd1
    - [建议] 使用unity build: 如set(CMAKE_UNITY_BUILD ON)加速编译
    - 加速技术 https://onqtam.comf/programming/2019-12-20-pch-unity-cmake-3-16/
    - https://github.com/onqtam/awesome-cmake

# 参考
- 《Effective C++ 3rd》
- 《More Effective C++》
- 《Effective STL》
- 《Effective Modern C++》
- 《C++ Coding Standards》
-  https://github.com/kelthuzadx/EffectiveModernCppChinese
