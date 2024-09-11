cmake_minimum_required(VERSION 3.12)
project(PackageTest CXX)

# The package provides the includes directly to CMAKE_INCLUDE_PATH
find_package(lz4 CONFIG REQUIRED)


add_executable(example example.cpp)
target_link_libraries(example ${lz4_LIBRARIES})
message(STATUS "include dir is ${lz4_INCLUDE_DIR} - library is ${lz4_LIBRARIES}")
target_include_directories(example PRIVATE ${lz4_INCLUDE_DIR})

set_target_properties(example PROPERTIES CXX_STANDARD 17)
