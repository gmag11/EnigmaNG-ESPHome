# EnigmaNG ESPHome Component

ESPHome external component that uses [EnigmaNG](https://github.com/gmag11/EnigmaNG) mesh networking as the transport layer, replacing WiFi. Nodes communicate over ESP-NOW with AES-128-GCM encryption and multi-hop routing.

## How It Works

```
[ESPHome Node]              [EnigmaNG Gateway]          [LAN]
 ESP32                       ESP32 + WiFi
 enigmang: psk              NAT routing                 [MQTT Broker]
 mqtt: broker               mesh ←→ LAN                 [Home Assistant]
      │                          │                            │
      └── ESP-NOW mesh ──────────┘── WiFi ────────────────────┘
          10.200.0.x              192.168.1.z               192.168.1.100
```

The component registers EnigmaNG as ESPHome's network provider. All TCP traffic (MQTT, HTTP) routes transparently through the mesh via the gateway's NAT.

## Installation

```yaml
external_components:
  - source: github://gmag11/EnigmaNG-ESPHome
    components: [enigmang, network]
```

Both `enigmang` and `network` must be listed. The `network` component is a patched version that adds EnigmaNG support to ESPHome's connectivity detection.

## Minimal Configuration

```yaml
enigmang:
  psk: !secret enigmang_psk

mqtt:
  broker: 192.168.1.100
  discovery: true
```

## Configuration Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `psk` | string | **yes** | — | Pre-shared key for the mesh network |
| `mode` | `node` / `battery` | no | `node` | Node mode. `battery` disables relay and enables deep sleep support |
| `channel` | 0–14 | no | `0` | Mesh channel. `0` = auto-discover from gateway beacon |
| `static_ip` | block | no | DHCP | Fixed IP within the mesh subnet |
| `static_ip.ip` | IP | yes (if block) | — | IPv4 address |
| `static_ip.gateway` | IP | no | auto | Mesh gateway IP |
| `relay_enabled` | bool | no | `true` | Whether this node relays frames for other nodes |
| `rssi_connect` | int (dBm) | no | `-75` | Minimum RSSI to connect to a parent |
| `rssi_disconnect` | int (dBm) | no | `-85` | RSSI below which parent is considered lost |
| `key_rotation` | duration | no | `24h` | ECDH link key rotation interval |
| `sleep_duration` | duration | no | — | **Required** if `mode: battery`. Deep sleep interval |

## Diagnostic Sensors

```yaml
sensor:
  - platform: enigmang
    name: "Mesh RSSI"

binary_sensor:
  - platform: enigmang
    name: "Mesh Connected"
```

## Important Constraints

### NAT — No Inbound Connections

The EnigmaNG gateway performs NAT between the mesh subnet (`10.200.0.0/16`) and the LAN. **Inbound TCP connections from the LAN to mesh nodes are blocked.** This means:

| Feature | Works? | Why |
|---|---|---|
| `mqtt:` | **Yes** | Node opens outbound TCP to broker |
| `api:` (Native API) | **No** | HA must open inbound TCP to node:6053 |
| Standard `ota:` | **No** | HA must open inbound TCP to node:3232 |
| HTTP OTA (`http_request`) | **Yes** | Node pulls firmware via outbound HTTP |
| `web_server:` | **No** | Requires inbound HTTP to the node |

### DNS Resolution

If the MQTT broker is configured as a hostname (e.g., `homeassistant.local`), the EnigmaNG gateway must have the `dns-proxy-cache` feature active. Without it, use an IP address.

### ESP32 Only

This component targets ESP32 with Arduino Core. ESP8266 uses a fundamentally different proxy-based architecture in EnigmaNG and is not supported.

## Examples

- [node-basic.yaml](example/node-basic.yaml) — Minimal node with DHT sensor
- [node-hostname.yaml](example/node-hostname.yaml) — Broker as hostname (requires DNS proxy)
- [node-battery.yaml](example/node-battery.yaml) — Battery mode with deep sleep
- [node-ota.yaml](example/node-ota.yaml) — HTTP OTA updates

## Gateway Setup

The EnigmaNG gateway runs as **dedicated firmware** (not ESPHome). See the [EnigmaNG repository](https://github.com/gmag11/EnigmaNG) for gateway setup instructions.

## License

MIT
