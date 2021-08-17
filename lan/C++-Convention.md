# 规范
- https://google.github.io/styleguide/cppguide.html
- https://google-styleguide.readthedocs.io/zh_CN/latest/google-cpp-styleguide/contents.html

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
