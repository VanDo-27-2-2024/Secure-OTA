# OTA Server — API Specification

Scope: minimal APIs required for the end-to-end OTA flow (upload → sign → distribute → download → status reporting). Aligned with the simplified schema: `firmwares`, `devices`, `device_update_logs`.

---

## Full Flow Summary

```
Developer → POST /admin/firmware
                 ├─→ be-api → POST /sign (KMS)
                 ├─→ File Storage
                 └─→ DB: firmwares

Device   → POST /device/register
         → GET  /device/latest?current_version=v1.0.0
         → POST /device/update-log {status: "pending"}
         → GET  /device/firmware/v1.2.0
         → PATCH /device/update-log/{id} {status: "downloading"}
         → (verify signature locally, out of server scope)
         → PATCH /device/update-log/{id} {status: "installing"}
         → PATCH /device/update-log/{id} {status: "success" | "failed" | "rolled_back"}
```

---

---

## 1. Admin API

### `POST /admin/firmware`

Developer uploads a new firmware version.

**Input**
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | binary (multipart/form-data) | Yes | Firmware binary |
| `version` | string | Yes | e.g. `v1.2.0` |
| `release_notes` | string | No | Description of changes |

**Action**
1. Validate `version` does not already exist in `firmwares`
2. Call KMS `POST /sign` with the firmware binary → receive signature
3. Compute `checksum_sha256` of the binary
4. Store `firmware.bin` + `firmware.sig` in File Storage (`/storage/firmware/{version}/`)
5. Insert row into `firmwares`: `version`, `release_notes`, `file_path`, `signature_path`, `file_size`, `checksum_sha256`, `is_active=true`

**Output**
```json
{
  "firmware_id": "uuid",
  "version": "v1.2.0",
  "status": "uploaded",
  "checksum_sha256": "..."
}
```

**Error cases**
- `409 Conflict` — version already exists
- `502 Bad Gateway` — KMS unreachable or signing failed

---

### `PATCH /admin/firmware/{firmware_id}`

Deactivate a firmware version (e.g. found to be faulty after release).

**Input**
```json
{ "is_active": false }
```

**Action**
1. Update `firmwares.is_active`

**Output**
```json
{ "firmware_id": "uuid", "is_active": false }
```

---

## 2. Device API

### `POST /device/register`

Device registers itself on first contact (upsert — safe to call repeatedly).

**Input**
```json
{
  "device_id": "rpi-001",
  "current_firmware_version": "v1.0.0"
}
```

**Action**
1. If `device_id` does not exist in `devices` → insert
2. If it exists → update `current_firmware_version`, `last_seen`

**Output**
```json
{ "id": "uuid", "device_id": "rpi-001" }
```

---

### `GET /device/latest`

Device checks whether a newer firmware version is available.

**Input**
| Field | Type | Required | Description |
|---|---|---|---|
| `current_version` | string (query param) | Yes | Version currently running on device |

**Action**
1. Query `firmwares` WHERE `is_active = true` ORDER BY `created_at` DESC LIMIT 1
2. Compare against `current_version`
3. If no newer version → `update_available: false`

**Output**
```json
{
  "update_available": true,
  "firmware_id": "uuid",
  "version": "v1.2.0",
  "checksum_sha256": "...",
  "download_url": "/device/firmware/v1.2.0"
}
```

---

### `GET /device/firmware/{version}`

Device downloads the firmware binary.

**Input**
| Field | Type | Required | Description |
|---|---|---|---|
| `version` | string (path param) | Yes | Version to download |

**Action**
1. Look up `firmwares` by `version`; reject if not found or `is_active = false`
2. Read binary from File Storage
3. Return binary stream + signature header

**Output**
- Body: binary stream (`application/octet-stream`)
- Header: `X-Firmware-Signature: <hex string>`

**Error cases**
- `404 Not Found` — version does not exist
- `403 Forbidden` — version is inactive (rejected/revoked)

---

### `POST /device/update-log`

Device creates a new update attempt record. Called once, right before starting download.

**Input**
```json
{
  "device_id": "rpi-001",
  "firmware_id": "uuid",
  "status": "pending"
}
```

**Action**
1. Resolve `devices.id` from `device_id`
2. Insert row into `device_update_logs`: `status="pending"`, `started_at=now()`

**Output**
```json
{ "log_id": "uuid", "status": "pending" }
```

---

### `PATCH /device/update-log/{log_id}`

Device reports progress/result of an ongoing update. Called multiple times during one update cycle (downloading → installing → success/failed/rolled_back).

**Input**
```json
{
  "status": "downloading",
  "error_message": null
}
```
| Field | Type | Required | Description |
|---|---|---|---|
| `status` | enum (`downloading`, `installing`, `success`, `failed`, `rolled_back`) | Yes | Current stage |
| `error_message` | string | No | Required when `status = failed` |

**Action**
1. Update `device_update_logs.status`
2. If `status` is a terminal state (`success`, `failed`, `rolled_back`) → set `completed_at = now()`
3. If `status = success` → also update `devices.current_firmware_version`

**Output**
```json
{ "log_id": "uuid", "status": "downloading" }
```

---

## 3. KMS API (internal only — not exposed through the Gateway)

### `POST /sign`

Called only by the BE API to sign firmware.

**Input**
```json
{ "data": "<hex string of firmware binary>" }
```

**Action**
1. Sign `data` with the private key (never leaves KMS)

**Output**
```json
{ "signature": "<hex string>" }
```


## Out of Scope

- Authentication/Authorization detail (handled at API Gateway)
- Campaign / rollout percentage / hardware-targeted rollout
- Pagination, search, filter on any list endpoint