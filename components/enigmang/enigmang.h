#pragma once

#include "esphome/core/component.h"
#include "esphome/components/network/ip_address.h"

// Forward declaration — full include is in enigmang.cpp to avoid pulling
// Arduino WiFi headers into every file that includes enigmang.h
class MeshNetwork;

namespace esphome {
namespace enigmang {

enum class EnigmaNGMode : uint8_t {
  NODE = 0,
  BATTERY = 1,
};

class EnigmaNGComponent : public Component {
 public:
  EnigmaNGComponent();

  // ESPHome Component interface
  void setup() override;
  void loop() override;
  void dump_config() override;
  float get_setup_priority() const override;

  // Network provider interface (convention, not base class)
  bool is_connected();
  network::IPAddresses get_ip_addresses();
  network::IPAddress get_dns_address(uint8_t num);
  const char *get_use_address() const;
  void set_use_address(const char *use_address);

  // Configuration setters (called from codegen)
  void set_psk(const char *psk) { psk_ = psk; }
  void set_mode(EnigmaNGMode mode) { mode_ = mode; }
  void set_channel(uint8_t channel) { channel_ = channel; }
  void set_static_ip(uint32_t ip) { static_ip_ = ip; has_static_ip_ = true; }
  void set_gateway_ip(uint32_t gw) { gateway_ip_ = gw; }
  void set_relay_enabled(bool enabled) { relay_enabled_ = enabled; }
  void set_rssi_connect(int8_t dbm) { rssi_connect_ = dbm; }
  void set_rssi_disconnect(int8_t dbm) { rssi_disconnect_ = dbm; }
  void set_key_rotation(uint32_t seconds) { key_rotation_sec_ = seconds; }
  void set_sleep_duration(uint32_t seconds) { sleep_duration_sec_ = seconds; }

  // State accessors
  int8_t get_rssi_from_gateway();

 protected:
  MeshNetwork *mesh_{nullptr};

  const char *psk_{nullptr};
  EnigmaNGMode mode_{EnigmaNGMode::NODE};
  uint8_t channel_{0};
  uint32_t static_ip_{0};
  uint32_t gateway_ip_{0};
  bool has_static_ip_{false};
  bool relay_enabled_{true};
  int8_t rssi_connect_{-75};
  int8_t rssi_disconnect_{-85};
  uint32_t key_rotation_sec_{86400};
  uint32_t sleep_duration_sec_{0};

  char use_address_[20]{};
  bool was_connected_{false};
};

extern EnigmaNGComponent *global_enigmang_component;  // NOLINT(cppcoreguidelines-avoid-non-const-global-variables)

}  // namespace enigmang
}  // namespace esphome
