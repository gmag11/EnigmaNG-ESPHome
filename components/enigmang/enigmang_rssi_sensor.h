#pragma once

#include "esphome/components/sensor/sensor.h"
#include "esphome/core/component.h"
#include "enigmang.h"

namespace esphome {
namespace enigmang {

class EnigmaNGRSSISensor : public sensor::Sensor, public PollingComponent {
 public:
  void set_parent(EnigmaNGComponent *parent) { parent_ = parent; }

  void update() override {
    int8_t rssi = parent_->get_rssi_from_gateway();
    this->publish_state(static_cast<float>(rssi));
  }

 protected:
  EnigmaNGComponent *parent_{nullptr};
};

}  // namespace enigmang
}  // namespace esphome
