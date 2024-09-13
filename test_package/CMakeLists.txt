cmake_minimum_required(VERSION 3.21)
project(PackageTest CXX)

macro(print_all_variables)
    message(STATUS "print_all_variables------------------------------------------{")
    get_cmake_property(_variableNames VARIABLES)
    foreach (_variableName ${_variableNames})
        message(STATUS "${_variableName}=${${_variableName}}")
    endforeach()
    message(STATUS "print_all_variables------------------------------------------}")
endmacro()

# The package provides the includes directly to CMAKE_INCLUDE_PATH
find_package(TBB CONFIG REQUIRED)

print_all_variables()

add_executable(example example.cpp)
target_link_libraries(example TBB::tbb)

set_target_properties(example PROPERTIES CXX_STANDARD 17)
