## 1. Repository Setup

- [x] 1.1 Initialize `EnigmaNG-ESPHome` repository structure: `components/enigmang/`, `example/`, `lib/`, `test/`
- [x] 1.2 Add EnigmaNG as a git submodule: `git submodule add https://github.com/gmag11/EnigmaNG lib/EnigmaNG` and pin to a specific commit/tag
- [x] 1.3 Create `components/enigmang/CMakeLists.txt` linking against `lib/EnigmaNG/src/`
- [x] 1.4 Create `manifest.json` with component metadata, ESPHome version range, and target platform (ESP32 only)
- [x] 1.5 Create `README.md` documenting NAT constraint, supported modes, OTA approach, and DNS dependency for hostnames

## 2. YAML Schema (`__init__.py`)

- [x] 2.1 Research ESPHome network provider registration API (how `esp32_ethernet` or `wifi` registers as network provider in the target ESPHome version range)
- [x] 2.2 Create patched `components/network/` override: copy ESPHome's `util.h`, `util.cpp`, `__init__.py` and add `#ifdef USE_ENIGMANG` blocks to `is_connected()`, `get_ip_addresses()`, `get_use_address()`, and `is_disabled()`
- [x] 2.3 Define `CONFIG_SCHEMA` with all parameters: `psk`, `mode`, `channel`, `static_ip`, `relay_enabled`, `rssi_connect`, `rssi_disconnect`, `key_rotation`, `sleep_duration`
- [x] 2.4 Implement validation: `mode: battery` requires `sleep_duration`; `static_ip.ip` required when `static_ip` block is present; `channel` in range 0–14
- [x] 2.5 Implement `to_code()` codegen function that emits `EnigmaNG::get_singleton()->set_psk(...)` calls and registers the component with ESPHome's network stack
- [x] 2.6 Add optional `enigmang_connected` binary sensor and `enigmang_rssi` sensor to schema

## 3. C++ Component (`enigmang.h` / `enigmang.cpp`)

- [x] 3.1 Define `EnigmaNG` class inheriting from `esphome::Component` and implementing the network provider interface
- [x] 3.2 Implement `setup()`: call `MeshNetwork::begin(psk, mode)`, apply RSSI thresholds, relay flag, key rotation interval
- [x] 3.3 Implement `setup()` static IP path: call `MeshNetwork::begin(psk, IPAddress(...), mode)` when `static_ip` is configured
- [x] 3.4 Implement `loop()`: call `MeshNetwork::loop()` and update `network_is_connected()` state
- [x] 3.5 Implement `network_is_connected()`: return `MeshNetwork::isConnected()`
- [x] 3.6 Implement `getClient()` delegation: return `MeshNetwork::getClient()` so ESPHome's `mqtt:` obtains a valid `WiFiClient`
- [x] 3.7 Implement `mode: battery` path: call `MeshNetwork::setBatteryMode(true, sleepIntervalSec)` during setup
- [x] 3.8 Implement optional diagnostic sensors: `EnigmaNGConnectedSensor` (binary) and `EnigmaNGRSSISensor` (float, dBm)

## 4. Build System Integration

- [ ] 4.1 Verify ESPHome's PlatformIO build picks up `lib/EnigmaNG/src/` correctly via `CMakeLists.txt`
- [ ] 4.2 Confirm EnigmaNG's dependencies (`QuickESPNow`, `mbedTLS Curve25519`) are available in the ESP32 Arduino Core toolchain
- [ ] 4.3 Add `idf_component.yml` or `library.json` references for any missing transitive dependencies

## 5. Example Configuration

- [x] 5.1 Create `example/node-basic.yaml`: minimal node with `enigmang:` + `mqtt:` (broker as IP) + DHT sensor
- [x] 5.2 Create `example/node-hostname.yaml`: same as above but `mqtt: broker: homeassistant.local` with a note about `dns-proxy-cache` dependency
- [x] 5.3 Create `example/node-battery.yaml`: `mode: battery` + `deep_sleep:` + temperature sensor publishing on wake
- [x] 5.4 Create `example/node-ota.yaml`: HTTP OTA via `update: platform: http_request` with example HA local URL

## 6. Testing

- [ ] 6.1 Flash `example/node-basic.yaml` to an ESP32, verify mesh join and MQTT publish reaches broker
- [ ] 6.2 Verify `enigmang_rssi` sensor updates on each `loop()` cycle
- [ ] 6.3 Verify `enigmang_connected` sensor goes false when parent node is switched off and true again on reconnect
- [ ] 6.4 Flash `example/node-battery.yaml`, verify wake→publish→sleep cycle and NVS parent recovery after power cycle
- [ ] 6.5 Verify OTA from `example/node-ota.yaml` successfully downloads and flashes firmware via HTTP outbound
- [ ] 6.6 Verify that declaring `api:` alongside `enigmang:` compiles but README warns about NAT incompatibility
