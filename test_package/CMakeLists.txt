cmake_minimum_required(VERSION 3.21)
project(PackageTest CXX)

# The package provides the includes directly to CMAKE_INCLUDE_PATH
find_package(lz4 CONFIG REQUIRED)

add_executable(example example.cpp)
target_link_libraries(example lz4::lz4)

set_target_properties(example PROPERTIES CXX_STANDARD 17)
