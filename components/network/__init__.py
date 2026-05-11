"""Patched network component for EnigmaNG support.

This is a copy of ESPHome's built-in network component with USE_ENIGMANG
support added to util.h and util.cpp. The Python schema is unchanged.

Synced from: https://github.com/esphome/esphome (dev branch, 2026-05-10)
"""

import ipaddress
import logging

import esphome.codegen as cg
from esphome.components.esp32 import add_idf_sdkconfig_option
import esphome.config_validation as cv
from esphome.const import CONF_ENABLE_IPV6, CONF_MIN_IPV6_ADDR_COUNT
from esphome.core import CORE, coroutine_with_priority

CODEOWNERS = ["@gmag11"]
AUTO_LOAD = ["mdns"]

_LOGGER = logging.getLogger(__name__)

# High performance networking tracking infrastructure
# Components can request high performance networking and this configures lwip and WiFi settings
KEY_HIGH_PERFORMANCE_NETWORKING = "high_performance_networking"
CONF_ENABLE_HIGH_PERFORMANCE = "enable_high_performance"

network_ns = cg.esphome_ns.namespace("network")
IPAddress = network_ns.class_("IPAddress")


def ip_address_literal(ip):
    """Generate an IPAddress with compile-time initialization."""
    if ip is None:
        return IPAddress(0, 0, 0, 0)
    try:
        ip_obj = ipaddress.ip_address(ip)
    except (ValueError, TypeError):
        pass
    else:
        if isinstance(ip_obj, ipaddress.IPv4Address):
            octets = ip_obj.packed
            return IPAddress(octets[0], octets[1], octets[2], octets[3])
    return IPAddress(str(ip))


def require_high_performance_networking():
    if not CORE.data.get(KEY_HIGH_PERFORMANCE_NETWORKING, False):
        CORE.data[KEY_HIGH_PERFORMANCE_NETWORKING] = True


def has_high_performance_networking():
    return CORE.data.get(KEY_HIGH_PERFORMANCE_NETWORKING, False)


CONFIG_SCHEMA = cv.Schema(
    {
        cv.SplitDefault(
            CONF_ENABLE_IPV6,
            bk72xx=False,
            esp32=False,
            esp8266=False,
            host=False,
            rp2040=False,
        ): cv.All(
            cv.boolean,
            cv.Any(
                cv.require_framework_version(
                    bk72xx_arduino=cv.Version(1, 7, 0),
                    esp_idf=cv.Version(0, 0, 0),
                    esp32_arduino=cv.Version(0, 0, 0),
                    esp8266_arduino=cv.Version(0, 0, 0),
                    host=cv.Version(0, 0, 0),
                    rp2040_arduino=cv.Version(0, 0, 0),
                ),
                cv.boolean_false,
            ),
        ),
        cv.Optional(CONF_MIN_IPV6_ADDR_COUNT, default=0): cv.positive_int,
        cv.Optional(CONF_ENABLE_HIGH_PERFORMANCE): cv.All(cv.boolean, cv.only_on_esp32),
    }
)


@coroutine_with_priority(201.0)
async def to_code(config):
    cg.add_define("USE_NETWORK")

    enable_high_perf = config.get(CONF_ENABLE_HIGH_PERFORMANCE)
    component_requested = CORE.data.get(KEY_HIGH_PERFORMANCE_NETWORKING, False)
    should_enable = (
        enable_high_perf if enable_high_perf is not None else component_requested
    )

    if enable_high_perf is False and component_requested:
        _LOGGER.info(
            "High performance networking disabled by user configuration (overriding component request)"
        )

    if CORE.is_esp32 and should_enable:
        psram_guaranteed = False
        if psram_guaranteed:
            _LOGGER.info(
                "Applying high-performance lwip settings (PSRAM guaranteed): 512KB TCP windows, 512 mailbox sizes"
            )
            add_idf_sdkconfig_option("CONFIG_LWIP_WND_SCALE", True)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_RCV_SCALE", 3)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_SND_BUF_DEFAULT", 65534)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_WND_DEFAULT", 512000)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCPIP_RECVMBOX_SIZE", 512)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_RECVMBOX_SIZE", 512)
            add_idf_sdkconfig_option("CONFIG_LWIP_MAX_ACTIVE_TCP", 16)
            add_idf_sdkconfig_option("CONFIG_LWIP_MAX_LISTENING_TCP", 16)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_MAXRTX", 12)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_SYNMAXRTX", 6)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_MSS", 1436)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_MSL", 60000)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_OVERSIZE_MSS", True)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_QUEUE_OOSEQ", True)
        else:
            _LOGGER.info(
                "Applying optimized lwip settings: 65KB TCP windows, 64 mailbox sizes"
            )
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_SND_BUF_DEFAULT", 65534)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_WND_DEFAULT", 65534)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCP_RECVMBOX_SIZE", 64)
            add_idf_sdkconfig_option("CONFIG_LWIP_TCPIP_RECVMBOX_SIZE", 64)

    if (enable_ipv6 := config.get(CONF_ENABLE_IPV6, None)) is not None:
        cg.add_define("USE_NETWORK_IPV6", enable_ipv6)
        if enable_ipv6:
            cg.add_define(
                "USE_NETWORK_MIN_IPV6_ADDR_COUNT", config[CONF_MIN_IPV6_ADDR_COUNT]
            )
        if CORE.is_esp32:
            if CORE.using_arduino:
                add_idf_sdkconfig_option("CONFIG_LWIP_IPV6", True)
                add_idf_sdkconfig_option("CONFIG_LWIP_IPV6_AUTOCONFIG", True)
            else:
                add_idf_sdkconfig_option("CONFIG_LWIP_IPV6", enable_ipv6)
                add_idf_sdkconfig_option("CONFIG_LWIP_IPV6_AUTOCONFIG", enable_ipv6)
        elif enable_ipv6:
            cg.add_build_flag("-DCONFIG_LWIP_IPV6")
            cg.add_build_flag("-DCONFIG_LWIP_IPV6_AUTOCONFIG")
            if CORE.is_bk72xx:
                cg.add_build_flag("-DCONFIG_IPV6")
            if CORE.is_esp8266:
                cg.add_build_flag("-DPIO_FRAMEWORK_ARDUINO_LWIP2_IPV6_LOW_MEMORY")
            if CORE.is_rp2040:
                cg.add_build_flag("-DPIO_FRAMEWORK_ARDUINO_ENABLE_IPV6")
