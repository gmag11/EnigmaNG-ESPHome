"""EnigmaNG RSSI sensor."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    UNIT_DECIBEL_MILLIWATT,
)

from . import EnigmaNGComponent, enigmang_ns

DEPENDENCIES = ["enigmang"]

EnigmaNGRSSISensor = enigmang_ns.class_(
    "EnigmaNGRSSISensor", sensor.Sensor, cg.PollingComponent
)

CONF_ENIGMANG_ID = "enigmang_id"

CONFIG_SCHEMA = (
    sensor.sensor_schema(
        EnigmaNGRSSISensor,
        unit_of_measurement=UNIT_DECIBEL_MILLIWATT,
        device_class=DEVICE_CLASS_SIGNAL_STRENGTH,
        state_class=STATE_CLASS_MEASUREMENT,
        entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
        accuracy_decimals=0,
    )
    .extend(
        {
            cv.GenerateID(CONF_ENIGMANG_ID): cv.use_id(EnigmaNGComponent),
        }
    )
    .extend(cv.polling_component_schema("30s"))
)


async def to_code(config):
    var = await sensor.new_sensor(config)
    await cg.register_component(var, config)
    parent = await cg.get_variable(config[CONF_ENIGMANG_ID])
    cg.add(var.set_parent(parent))
