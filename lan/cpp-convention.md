# 规范
- https://google.github.io/styleguide/cppguide.html
- 中文版: https://google-styleguide.readthedocs.io/zh_CN/latest/google-cpp-styleguide/contents.html (注意:有些并不准确)

# Effective C++ 3rd
- Item 53:  重视编译器警告

# More Effective C++
- Item M3:  不要对数组使用多态  
- Item M4:  避免无用的缺省构造函数
- Item M5:  谨慎定义类型转换函数
- Item M6:  尽量使用前缀自增自减

# Effective STL
- 条款4:  用empty来代替检查size()是否为0
- 条款5:  区间成员函数优先于与之对应的单元素成员函数
- 条款9:  慎重选择删除元素的方法
- 条款14: 使用reserve来避免不必要的重新分配
- 条款22. 切勿直接修改set或multiset中的键
- 条款32. 如果确实需要删除元素，则需要在remove这一类算法之后调用erase
- 条款33. 对包含指针的容器使用remove这一类算法时要特别小心
- 条款44. 容器的成员函数优先于同名的算法

# Effective Modern C++

# 补充

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
-  https://github.com/kelthuzadx/EffectiveModernCppChinese
