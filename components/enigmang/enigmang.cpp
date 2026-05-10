#include <MeshNetwork.h>  // Must come first — provides WiFiClient.h chain
#include "enigmang.h"
#include "esphome/core/log.h"
#include "esphome/core/application.h"

namespace esphome {
namespace enigmang {

static const char *const TAG = "enigmang";

EnigmaNGComponent *global_enigmang_component = nullptr;  // NOLINT(cppcoreguidelines-avoid-non-const-global-variables)

EnigmaNGComponent::EnigmaNGComponent() {
  global_enigmang_component = this;
  mesh_ = new MeshNetwork();
}

float EnigmaNGComponent::get_setup_priority() const { return setup_priority::WIFI; }

void EnigmaNGComponent::setup() {
  ESP_LOGCONFIG(TAG, "Setting up EnigmaNG...");

  // Apply configuration before begin()
  if (channel_ != 0) {
    mesh_->setChannel(channel_);
  }

  mesh_->setRssiThreshold(rssi_connect_, rssi_disconnect_);
  mesh_->setKeyRotationInterval(key_rotation_sec_);

  MeshMode mesh_mode;
  if (mode_ == EnigmaNGMode::BATTERY) {
    mesh_mode = MESH_BATTERY;
    mesh_->setRelayEnabled(false);
    mesh_->setBatteryMode(true, sleep_duration_sec_);
  } else {
    mesh_mode = MESH_NODE;
    mesh_->setRelayEnabled(relay_enabled_);
  }

  bool ok;
  if (has_static_ip_) {
    IPAddress ip(static_ip_);
    ok = mesh_->begin(psk_, ip, mesh_mode);
  } else {
    ok = mesh_->begin(psk_, mesh_mode);
  }

  if (!ok) {
    ESP_LOGE(TAG, "MeshNetwork::begin() failed");
    this->mark_failed();
    return;
  }

  ESP_LOGI(TAG, "EnigmaNG mesh started (mode=%s, channel=%u)",
           mode_ == EnigmaNGMode::BATTERY ? "battery" : "node", channel_);
}

void EnigmaNGComponent::loop() {
  mesh_->loop();

  bool connected = mesh_->isConnected();
  if (connected && !was_connected_) {
    ESP_LOGI(TAG, "Mesh connected, IP: %s", mesh_->getLocalIP().toString().c_str());
    // Update use_address with current IP
    strncpy(use_address_, mesh_->getLocalIP().toString().c_str(), sizeof(use_address_) - 1);
    use_address_[sizeof(use_address_) - 1] = '\0';
  } else if (!connected && was_connected_) {
    ESP_LOGW(TAG, "Mesh connection lost");
  }
  was_connected_ = connected;
}

void EnigmaNGComponent::dump_config() {
  ESP_LOGCONFIG(TAG, "EnigmaNG:");
  ESP_LOGCONFIG(TAG, "  Mode: %s", mode_ == EnigmaNGMode::BATTERY ? "battery" : "node");
  ESP_LOGCONFIG(TAG, "  Channel: %u%s", channel_, channel_ == 0 ? " (auto)" : "");
  ESP_LOGCONFIG(TAG, "  Relay: %s", relay_enabled_ ? "enabled" : "disabled");
  ESP_LOGCONFIG(TAG, "  RSSI connect: %d dBm", rssi_connect_);
  ESP_LOGCONFIG(TAG, "  RSSI disconnect: %d dBm", rssi_disconnect_);
  ESP_LOGCONFIG(TAG, "  Key rotation: %u s", key_rotation_sec_);
  if (has_static_ip_) {
    IPAddress ip(static_ip_);
    ESP_LOGCONFIG(TAG, "  Static IP: %s", ip.toString().c_str());
  } else {
    ESP_LOGCONFIG(TAG, "  IP: DHCP");
  }
  if (mode_ == EnigmaNGMode::BATTERY) {
    ESP_LOGCONFIG(TAG, "  Sleep duration: %u s", sleep_duration_sec_);
  }
}

bool EnigmaNGComponent::is_connected() { return mesh_->isConnected(); }

network::IPAddresses EnigmaNGComponent::get_ip_addresses() {
  network::IPAddresses addresses{};
  if (mesh_->isConnected()) {
    addresses[0] = network::IPAddress(mesh_->getLocalIP());
  }
  return addresses;
}

network::IPAddress EnigmaNGComponent::get_dns_address(uint8_t num) {
  // DNS is provided by the gateway's dns-proxy-cache if available
  // Return the gateway IP as DNS server (standard for mesh nodes)
  if (num == 0 && mesh_->isConnected()) {
    return network::IPAddress(mesh_->getGatewayIP());
  }
  return {};
}

const char *EnigmaNGComponent::get_use_address() const { return use_address_; }

void EnigmaNGComponent::set_use_address(const char *use_address) {
  strncpy(use_address_, use_address, sizeof(use_address_) - 1);
  use_address_[sizeof(use_address_) - 1] = '\0';
}

int8_t EnigmaNGComponent::get_rssi_from_gateway() { return mesh_->getRssiFromGateway(); }

}  // namespace enigmang
}  // namespace esphome
