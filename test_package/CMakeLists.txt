cmake_minimum_required(VERSION 3.12)
project(PackageTest CXX)

# The package provides the includes directly to CMAKE_INCLUDE_PATH
find_package(faiss CONFIG REQUIRED)

find_package(OpenMP)
#if (APPLE)
#    find_package(OpenMP)
#    find_package(OpenGL REQUIRED)
#else()
#    find_package(OpenMP REQUIRED)
#endif()

add_executable(example example.cpp)
target_link_libraries(example faiss)

set_target_properties(example PROPERTIES CXX_STANDARD 17)
