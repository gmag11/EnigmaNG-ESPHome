## Context

ESPHome is a declarative firmware framework for ESP32/ESP8266 that generates C++ firmware from YAML configuration. Its network abstraction is built around the concept of a **network component** (e.g., `wifi:`, `ethernet:`) that registers itself as the active transport. All other components — `mqtt:`, `api:`, `ota:`, `http_request:` — obtain a `WiFiClient`-compatible socket from whichever network component is active.

EnigmaNG is a mesh networking library for ESP32 (and a separate derivative for ESP8266) that provides a virtual IP interface (`mesh0`) via lwIP over ESP-NOW. Its public API exposes `MeshNetwork::getClient()` which returns a `WiFiClient` wrapping an lwIP socket — the exact interface ESPHome's network subsystem expects.

The integration point is therefore clean and non-invasive: the EnigmaNG component registers itself as ESPHome's network provider and routes all TCP traffic through the mesh.

**Connectivity constraint:** The EnigmaNG gateway performs NAT between the mesh subnet (`10.200.0.0/16`) and the LAN. Inbound TCP connections from the LAN to mesh nodes are blocked by NAT. Only outbound connections from the node are possible.

**Scope constraint:** This component targets ESP32 only. ESP8266 uses a fundamentally different proxy-based architecture in EnigmaNG (no IP stack, PROXY_* frame protocol) and is a separate effort.

## Goals / Non-Goals

**Goals:**
- Implement a minimal ESPHome external component that registers `MeshNetwork` as a network provider.
- Support `mode: node` (relay enabled) and `mode: battery` (deep sleep cycle, no relay).
- Expose all relevant EnigmaNG configuration parameters in the YAML schema.
- Work transparently with ESPHome's `mqtt:` component (outbound TCP to external broker).
- Work transparently with ESPHome's `http_request:` update component (outbound HTTP for OTA).
- Provide a `connected` binary sensor and `rssi` sensor as optional diagnostic entities.

**Non-Goals:**
- `mode: gateway` — gateway runs as dedicated EnigmaNG firmware, not under ESPHome.
- ESPHome Native API (`api:` component, port 6053) — requires inbound TCP, blocked by NAT.
- OTA via the standard ESPHome OTA mechanism — requires inbound TCP, blocked by NAT.
- ESP8266 support — different architecture, separate effort.
- Hosting or managing an MQTT broker — the component is pure transport.
- mDNS / `_esphomelib._tcp` discovery — requires inbound connections, not viable with NAT.

## Decisions

### D1: External component, not a fork of ESPHome

**Decision:** Distribute as an ESPHome external component installable via `external_components:` in the user YAML.

**Rationale:** External components require no changes to ESPHome core, are independently versioned, and can be published without upstream approval. The ESPHome external component system is mature and supports C++ + Python schema definitions.

**Alternative considered:** Upstreaming to ESPHome core. Rejected because it requires ESPHome maintainer review, has a long timeline, and couples the EnigmaNG release cycle to ESPHome's.

---

### D2: Implement as a `Component` + `WiFiInterface` (network provider)

**Decision:** The C++ class `EnigmaNG` inherits from `esphome::Component` and registers with ESPHome's network stack by implementing the `WiFiInterface`-compatible contract (or the equivalent network provider registration mechanism used by `ethernet:` components).

**Rationale:** This is the same pattern used by the ESPHome Ethernet component (`esp32_ethernet`). It makes the component transparent to `mqtt:`, `http_request:`, and all other TCP-based components without any modification.

**Alternative considered:** Standalone component that just calls `MeshNetwork::begin()` and lets the user manually provide the client. Rejected because it would require users to wire up the client manually instead of relying on ESPHome's automatic network selection.

---

### D3: MQTT broker is external — no broker in the component

**Decision:** The component does not provide or manage an MQTT broker. The user configures the `mqtt:` component separately pointing to an external broker (Mosquitto in HA, cloud broker, etc.).

**Rationale:** The EnigmaNG gateway performs NAT routing to the LAN — outbound TCP from the node reaches any IP on the LAN or internet. The broker address is a user concern, not a transport concern.

**DNS note:** If the broker is configured as a hostname (e.g., `homeassistant.local`), DNS resolution requires the EnigmaNG `dns-proxy-cache` feature to be active on the gateway. Without it, an IP address must be used. This is documented in the component README but is not enforced — the component cannot know at build time whether DNS is available.

---

### D4: OTA via HTTP outbound only

**Decision:** OTA is performed using ESPHome's `http_request`-based update mechanism. The user configures an HTTP endpoint on the LAN (e.g., HA's update server) and the node pulls firmware updates by outbound HTTP.

**Rationale:** Standard ESPHome OTA (port 3232) requires inbound TCP from HA to the node, which is blocked by the gateway NAT. HTTP outbound OTA is the only viable mechanism in this topology.

**Alternative considered:** MQTT-based OTA (firmware chunks over MQTT). Rejected for initial version due to complexity; can be added later.

---

### D5: EnigmaNG library included via git submodule (not PlatformIO registry)

**Decision:** The EnigmaNG Arduino library is included as a git submodule under `lib/EnigmaNG/` pointing to `https://github.com/gmag11/EnigmaNG`, and referenced in `components/enigmang/CMakeLists.txt`.

**Rationale:** EnigmaNG is published on GitHub (`https://github.com/gmag11/EnigmaNG`) but is not yet registered in the PlatformIO library registry. A git submodule is therefore the only reliable way to pin a specific commit/tag and ensure reproducible builds. Once EnigmaNG is registered in PlatformIO, the dependency can be migrated to a `lib_deps` entry — but the submodule approach works regardless and avoids any dependency on registry availability.

**Alternative considered:** Fetching directly from GitHub at build time via PlatformIO's `lib_deps = https://github.com/gmag11/EnigmaNG` URL syntax. Rejected because it pulls the latest HEAD on every clean build, making builds non-reproducible without an explicit commit hash. A submodule pins the exact revision intentionally.

---

### D6: Battery mode maps to MeshNetwork MESH_BATTERY

**Decision:** `mode: battery` maps directly to `MeshNetwork::begin(psk, MESH_BATTERY)` and `MeshNetwork::setBatteryMode(true, sleepIntervalSec)`. ESPHome's own `deep_sleep:` component is used for the sleep cycle — the EnigmaNG component does not manage sleep independently.

**Rationale:** ESPHome already has a well-tested `deep_sleep:` component. EnigmaNG's battery mode (§7 of spec) follows a LoRaWAN Class A pattern: wake → TX uplink → RX windows → sleep. ESPHome's `deep_sleep:` controls the wake/sleep cycle; EnigmaNG's `MESH_BATTERY` mode disables relay and manages the RX windows. The two are complementary.

## Risks / Trade-offs

**[Risk] ESPHome network provider API may not be stable across versions**
→ Pin the component to a tested ESPHome version range in `manifest.json`. Document the tested version clearly.

**[Risk] lwIP socket performance over mesh may surprise users expecting WiFi-level throughput**
→ Document expected throughput (limited by ESP-NOW MTU 250B, TCP MSS 176B, multi-hop latency). Set expectations in README.

**[Risk] DNS resolution fails silently if dns-proxy-cache is not active on the gateway**
→ Document this dependency. In a future version, the component could detect DNS failure and log a warning if the broker address is a hostname.

**[Risk] NAT prevents inbound connections — users expect ESPHome Native API**
→ Clearly document that `api:` and standard OTA are not supported with this transport. Provide example YAML with `mqtt:` and `http_request:` update as the recommended configuration.

**[Risk] Deep sleep + mesh reconnection time may cause missed MQTT messages**
→ EnigmaNG stores up to 3 Parent candidates in NVS (§7.5 of spec) for fast reconnection. Documented as a known trade-off of battery mode.

### D7: Override ESPHome `network` component to integrate with `network::is_connected()`

**Decision:** Ship a patched copy of ESPHome's `network` component (`components/network/`) alongside the `enigmang` component. The patched version adds `#ifdef USE_ENIGMANG` blocks to `util.h` and `util.cpp`, enabling `network::is_connected()`, `get_ip_addresses()`, and `get_use_address()` to recognize EnigmaNG as a network provider.

Users include both components via `external_components:`:
```yaml
external_components:
  - source: github://gmag11/EnigmaNG-ESPHome
    components: [enigmang, network]
```

**Rationale:** ESPHome has no pluggable network provider API. The `network::is_connected()` function uses a compile-time `#ifdef` chain that only knows about WiFi, Ethernet, Modem, and OpenThread. Without this patch, MQTT and all other network-dependent components would never detect connectivity. The `network` component is small (~100 lines of logic in `util.h`/`util.cpp`) and changes infrequently in ESPHome upstream.

**Alternative considered:** Impersonating the Ethernet component by defining `USE_ETHERNET` and providing a `global_eth_component` pointer. Rejected because it's fragile, couples to `EthernetComponent`'s internal API, and blocks real Ethernet use.

**Maintenance:** The patched `network` component must be kept in sync with ESPHome upstream. Version pinning in `manifest.json` and CI checks can detect drift.

## Open Questions

- ~~**OQ1:** Does the ESPHome `WiFiInterface` registration API change significantly between ESPHome 2024.x and 2025.x?~~ **RESOLVED**: There is no such API. ESPHome uses hardcoded `#ifdef` chains. Decision D7 addresses this.
- **OQ2:** Should the component expose `getGatewayIP()` and `getNodeCount()` as ESPHome template sensors? Useful for diagnostics but adds schema complexity.
- **OQ3:** Should `relay_enabled` default to `true` for `mode: node` or be explicit? Defaulting to `true` makes nodes relay-capable by default, which is the correct mesh behavior but may surprise users.
