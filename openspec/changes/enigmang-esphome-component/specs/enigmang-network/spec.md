## ADDED Requirements

### Requirement: Component registration as network provider
The `enigmang` component SHALL register itself with ESPHome's network subsystem as the active network provider, replacing `wifi:` or `ethernet:`. All ESPHome TCP-based components (`mqtt:`, `http_request:`, etc.) SHALL obtain their socket connections through the EnigmaNG mesh interface without any additional configuration.

#### Scenario: MQTT connects over mesh after enigmang is declared
- **WHEN** a user declares `enigmang:` and `mqtt:` in the same YAML without `wifi:`
- **THEN** ESPHome SHALL route all MQTT TCP traffic through the EnigmaNG mesh interface (`mesh0`)

#### Scenario: No WiFi component required
- **WHEN** `enigmang:` is declared as the only network component
- **THEN** the firmware SHALL compile and run without `wifi:` declared
- **THEN** the firmware SHALL NOT attempt to initialize the ESP32 WiFi STA interface

---

### Requirement: Mesh join and connectivity lifecycle
The component SHALL manage the full EnigmaNG mesh join lifecycle: channel discovery, ECDH key exchange with a parent node, and IP assignment. It SHALL report connectivity state to ESPHome and block dependent components until the mesh is connected.

#### Scenario: Component blocks until mesh is connected
- **WHEN** the node boots and `enigmang:` is configured
- **THEN** ESPHome's network-dependent components SHALL NOT activate until `MeshNetwork::isConnected()` returns true

#### Scenario: Mesh connection lost
- **WHEN** the mesh connection is lost (parent timeout, key rotation failure, etc.)
- **THEN** the component SHALL report the network as disconnected to ESPHome
- **THEN** ESPHome's `mqtt:` component SHALL attempt reconnection once the mesh is restored

#### Scenario: Auto channel discovery
- **WHEN** `channel: 0` is configured (default)
- **THEN** the node SHALL scan for a JOIN_BEACON matching its configured PSK-derived Network ID
- **THEN** the node SHALL join on the channel where the beacon was found

#### Scenario: Fixed channel configured
- **WHEN** `channel` is set to a value between 1 and 14
- **THEN** the node SHALL operate exclusively on that channel without scanning

---

### Requirement: YAML configuration schema
The component SHALL expose the following configuration parameters in the ESPHome YAML schema:

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `psk` | string | yes | — | Pre-shared key for the EnigmaNG mesh network |
| `mode` | enum | no | `node` | `node` (relay enabled) or `battery` (no relay, deep sleep compatible) |
| `channel` | int 0–14 | no | `0` | Mesh channel. `0` = auto-discover |
| `static_ip` | block | no | DHCP | Fixed IP assignment within mesh subnet |
| `static_ip.ip` | IP string | yes (if block) | — | IPv4 address for this node |
| `static_ip.gateway` | IP string | no | mesh gateway | Mesh gateway IP |
| `relay_enabled` | bool | no | `true` | Whether this node relays frames for other nodes. Ignored in battery mode (always false) |
| `rssi_connect` | int dBm | no | `-75` | Minimum RSSI to connect to a parent |
| `rssi_disconnect` | int dBm | no | `-85` | RSSI below which parent is considered lost |
| `key_rotation` | duration | no | `24h` | Interval for ECDH link key rotation |
| `sleep_duration` | duration | no | — | Required if `mode: battery`. Deep sleep interval between uplinks |

#### Scenario: Minimal valid configuration compiles
- **WHEN** a user declares only `psk` under `enigmang:`
- **THEN** the firmware SHALL compile successfully with all other parameters at their defaults

#### Scenario: Battery mode requires sleep_duration
- **WHEN** `mode: battery` is declared without `sleep_duration`
- **THEN** ESPHome's config validation SHALL raise a compile-time error

#### Scenario: Static IP configuration
- **WHEN** `static_ip.ip` is declared
- **THEN** the node SHALL call `MeshNetwork::begin(psk, IPAddress(...), MESH_NODE)` with the specified IP
- **THEN** the node SHALL NOT request a DHCP-assigned address

---

### Requirement: Diagnostic sensors
The component SHALL optionally expose diagnostic information as ESPHome sensors.

#### Scenario: Connected binary sensor reports mesh state
- **WHEN** the user declares `enigmang_connected` binary sensor
- **THEN** it SHALL report `true` when `MeshNetwork::isConnected()` is true and `false` otherwise

#### Scenario: RSSI sensor reports link quality to gateway
- **WHEN** the user declares `enigmang_rssi` sensor
- **THEN** it SHALL report the value of `MeshNetwork::getRssiFromGateway()` in dBm

---

### Requirement: Battery mode compatibility with ESPHome deep_sleep
In `mode: battery`, the component SHALL initialize EnigmaNG with `MESH_BATTERY` mode and cooperate with ESPHome's `deep_sleep:` component for the sleep cycle. The component SHALL NOT independently manage deep sleep.

#### Scenario: Battery mode disables relay
- **WHEN** `mode: battery` is configured
- **THEN** `MeshNetwork::setRelayEnabled(false)` SHALL be called during setup
- **THEN** the node SHALL NOT relay frames for other mesh nodes

#### Scenario: Wake, send, sleep cycle
- **WHEN** the node wakes from deep sleep with `mode: battery`
- **THEN** the component SHALL rejoin the mesh using the cached parent list from NVS (EnigmaNG §7.5)
- **THEN** ESPHome SHALL publish sensor values via MQTT
- **THEN** ESPHome's `deep_sleep:` component SHALL put the node back to sleep

---

### Requirement: OTA via HTTP outbound
The component documentation SHALL specify that OTA updates are performed via ESPHome's `http_request`-based update mechanism. The Native ESPHome OTA (inbound TCP port 3232) SHALL NOT be used with this component because inbound TCP connections are blocked by the EnigmaNG gateway NAT.

#### Scenario: HTTP outbound OTA is documented
- **WHEN** a user consults the component README
- **THEN** they SHALL find an example YAML using `update:` with `platform: http_request` pointing to a LAN HTTP server

#### Scenario: Native API is documented as unsupported
- **WHEN** a user declares both `enigmang:` and `api:` in the same YAML
- **THEN** the component README SHALL document that `api:` requires inbound TCP which is blocked by the gateway NAT
