cmake_minimum_required(VERSION 3.16)
project(ota-agent LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(CURL REQUIRED)

add_executable(ota-agent src/main.cpp)

target_link_libraries(ota-agent PRIVATE CURL::libcurl)

target_link_options(ota-agent PRIVATE
    -static-libstdc++
    -static-libgcc
)