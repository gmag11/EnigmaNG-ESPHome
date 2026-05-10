cmake_minimum_required(VERSION 3.16)

# ESPHome/PlatformIO Arduino builds: library dependencies are declared
# in __init__.py via cg.add_library(). This CMakeLists.txt is only used
# when building as a native IDF component (not the normal ESPHome path).

idf_component_register(
    SRCS
        "enigmang.cpp"
    INCLUDE_DIRS
        "."
    REQUIRES
        esp_wifi
        esp_netif
        nvs_flash
        mbedtls
)
