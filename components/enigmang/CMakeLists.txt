cmake_minimum_required(VERSION 3.16)

# Register the EnigmaNG library source files
set(ENIGMANG_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../lib/EnigmaNG/src")

idf_component_register(
    SRCS
        "enigmang.cpp"
    INCLUDE_DIRS
        "."
        "${ENIGMANG_LIB_DIR}"
    REQUIRES
        esp_wifi
        esp_netif
        nvs_flash
        mbedtls
)
