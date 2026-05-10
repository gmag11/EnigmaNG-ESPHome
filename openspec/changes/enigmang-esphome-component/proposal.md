## Why

ESPHome nodes currently require WiFi connectivity, which is impractical in environments where radio interference, range limitations, or infrastructure constraints make WiFi unreliable. EnigmaNG provides a mesh network over ESP-NOW with AES-128-GCM encryption and multi-hop routing — a natural fit as a drop-in transport replacement for WiFi in ESPHome deployments.

## What Changes

- A new ESPHome external component `enigmang` is created that integrates the EnigmaNG C++ library as a network provider.
- The component replaces `wifi:` as the network transport for ESP32 nodes — ESPHome's MQTT, OTA, and other TCP-based components work transparently over the mesh without modification.
- The component registers itself with ESPHome's network subsystem, exposing the EnigmaNG lwIP netif (`mesh0`) as the active network interface.
- A `mode: node` (default) and `mode: battery` configuration are supported. Gateway mode is explicitly out of scope — the EnigmaNG gateway runs as a dedicated firmware, not under ESPHome.
- OTA updates are delivered via HTTP outbound (ESPHome `http_request` update component) since the NAT boundary at the gateway prevents inbound TCP connections from the LAN to mesh nodes. The ESPHome Native API (port 6053) is not supported for the same reason.
- MQTT integration uses the standard ESPHome `mqtt:` component pointing to an external broker on the LAN or internet. The EnigmaNG gateway acts as a pure NAT router — it does not host an MQTT broker.
- DNS resolution for MQTT broker hostnames depends on the EnigmaNG `dns-proxy-cache` feature being active on the gateway. Without it, broker must be configured as an IP address.

## Capabilities

### New Capabilities

- `enigmang-network`: ESPHome network provider component backed by the EnigmaNG mesh library. Handles mesh join, key exchange, routing, and exposes a lwIP socket interface compatible with `WiFiClient`. Configurable parameters: PSK, mode (node/battery), channel, static IP, RSSI thresholds, relay enabled, key rotation interval, sleep duration (battery mode).

### Modified Capabilities

<!-- No existing ESPHome capabilities are modified. The component integrates as an additive external component. -->

## Impact

- **New repository:** `EnigmaNG-ESPHome` — standalone ESPHome external component repository.
- **New source files:** `components/enigmang/__init__.py` (YAML schema + codegen), `components/enigmang/enigmang.h`, `components/enigmang/enigmang.cpp`, `components/enigmang/CMakeLists.txt`.
- **Dependency:** EnigmaNG Arduino library (fetched via CMake or as a git submodule).
- **Target platform:** ESP32 with Arduino Core (same as EnigmaNG library). ESP8266 is explicitly out of scope — it lacks an IP stack and uses a different proxy-based architecture in EnigmaNG.
- **No changes to EnigmaNG library:** The component consumes the public API (`MeshNetwork::begin()`, `MeshNetwork::loop()`, `MeshNetwork::getClient()`, `MeshNetwork::isConnected()`, `MeshNetwork::getLocalIP()`) without modification.
- **No changes to ESPHome core:** Distributed as an external component, installable via `external_components:` in the user's YAML.
