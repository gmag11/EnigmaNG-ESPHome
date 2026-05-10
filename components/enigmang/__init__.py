"""EnigmaNG mesh network component for ESPHome."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    CONF_CHANNEL,
)
from esphome.core import coroutine_with_priority, CoroPriority

CODEOWNERS = ["@gmag11"]
DEPENDENCIES = []
AUTO_LOAD = ["network"]
CONFLICTS_WITH = ["wifi", "ethernet"]

enigmang_ns = cg.esphome_ns.namespace("enigmang")
EnigmaNGComponent = enigmang_ns.class_("EnigmaNGComponent", cg.Component)
EnigmaNGMode = enigmang_ns.enum("EnigmaNGMode", is_class=True)

ENIGMANG_MODES = {
    "node": EnigmaNGMode.NODE,
    "battery": EnigmaNGMode.BATTERY,
}

CONF_PSK = "psk"
CONF_MODE = "mode"
CONF_STATIC_IP = "static_ip"
CONF_IP = "ip"
CONF_GATEWAY = "gateway"
CONF_RELAY_ENABLED = "relay_enabled"
CONF_RSSI_CONNECT = "rssi_connect"
CONF_RSSI_DISCONNECT = "rssi_disconnect"
CONF_KEY_ROTATION = "key_rotation"
CONF_SLEEP_DURATION = "sleep_duration"

STATIC_IP_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_IP): cv.ipv4,
        cv.Optional(CONF_GATEWAY): cv.ipv4,
    }
)


def _validate_battery_sleep(config):
    if config.get(CONF_MODE, "node") == "battery":
        if CONF_SLEEP_DURATION not in config:
            raise cv.Invalid("'sleep_duration' is required when mode is 'battery'")
    return config


CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(EnigmaNGComponent),
            cv.Required(CONF_PSK): cv.string_strict,
            cv.Optional(CONF_MODE, default="node"): cv.enum(ENIGMANG_MODES, lower=True),
            cv.Optional(CONF_CHANNEL, default=0): cv.int_range(min=0, max=14),
            cv.Optional(CONF_STATIC_IP): STATIC_IP_SCHEMA,
            cv.Optional(CONF_RELAY_ENABLED, default=True): cv.boolean,
            cv.Optional(CONF_RSSI_CONNECT, default=-75): cv.int_range(min=-127, max=0),
            cv.Optional(CONF_RSSI_DISCONNECT, default=-85): cv.int_range(min=-127, max=0),
            cv.Optional(CONF_KEY_ROTATION, default="24h"): cv.positive_time_period_seconds,
            cv.Optional(CONF_SLEEP_DURATION): cv.positive_time_period_seconds,
        }
    ).extend(cv.COMPONENT_SCHEMA),
    _validate_battery_sleep,
    cv.only_on_esp32,
)


@coroutine_with_priority(CoroPriority.COMMUNICATION)
async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add_define("USE_ENIGMANG")

    cg.add(var.set_psk(config[CONF_PSK]))
    cg.add(var.set_mode(config[CONF_MODE]))
    cg.add(var.set_channel(config[CONF_CHANNEL]))
    cg.add(var.set_relay_enabled(config[CONF_RELAY_ENABLED]))
    cg.add(var.set_rssi_connect(config[CONF_RSSI_CONNECT]))
    cg.add(var.set_rssi_disconnect(config[CONF_RSSI_DISCONNECT]))
    cg.add(var.set_key_rotation(config[CONF_KEY_ROTATION].total_seconds))

    if CONF_STATIC_IP in config:
        static_ip = config[CONF_STATIC_IP]
        ip = static_ip[CONF_IP]
        cg.add(var.set_static_ip(int(ip)))
        if CONF_GATEWAY in static_ip:
            cg.add(var.set_gateway_ip(int(static_ip[CONF_GATEWAY])))

    if CONF_SLEEP_DURATION in config:
        cg.add(var.set_sleep_duration(config[CONF_SLEEP_DURATION].total_seconds))
