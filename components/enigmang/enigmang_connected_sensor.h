#pragma once

#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/core/component.h"
#include "enigmang.h"

namespace esphome {
namespace enigmang {

class EnigmaNGConnectedSensor : public binary_sensor::BinarySensor, public PollingComponent {
 public:
  void set_parent(EnigmaNGComponent *parent) { parent_ = parent; }

  void update() override {
    bool connected = parent_->is_connected();
    this->publish_state(connected);
  }

 protected:
  EnigmaNGComponent *parent_{nullptr};
};

}  // namespace enigmang
}  // namespace esphome
