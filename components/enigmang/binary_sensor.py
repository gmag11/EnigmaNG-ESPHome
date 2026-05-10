"""EnigmaNG connected binary sensor."""

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import binary_sensor
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_CONNECTIVITY,
    ENTITY_CATEGORY_DIAGNOSTIC,
)

from . import EnigmaNGComponent, enigmang_ns

DEPENDENCIES = ["enigmang"]

EnigmaNGConnectedSensor = enigmang_ns.class_(
    "EnigmaNGConnectedSensor", binary_sensor.BinarySensor, cg.PollingComponent
)

CONF_ENIGMANG_ID = "enigmang_id"

CONFIG_SCHEMA = (
    binary_sensor.binary_sensor_schema(
        EnigmaNGConnectedSensor,
        device_class=DEVICE_CLASS_CONNECTIVITY,
        entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
    )
    .extend(
        {
            cv.GenerateID(CONF_ENIGMANG_ID): cv.use_id(EnigmaNGComponent),
        }
    )
    .extend(cv.polling_component_schema("10s"))
)


async def to_code(config):
    var = await binary_sensor.new_binary_sensor(config)
    await cg.register_component(var, config)
    parent = await cg.get_variable(config[CONF_ENIGMANG_ID])
    cg.add(var.set_parent(parent))
