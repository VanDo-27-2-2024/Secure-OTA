# Database Schema: Secure OTA Framework

This document outlines the PostgreSQL database schema for the OTA Server project.

## 1. ENUM Data Types
To optimize storage and standardize data:

- `update_state`: `('pending', 'downloading', 'installing', 'success', 'failed', 'rolled_back')`

## 2. Tables

### `devices`
Stores identification information and the current status of embedded devices.

| Column | Type | Constraints / Default | Description |
|--------|------|-----------------------|-------------|
| `id` | UUID | PRIMARY KEY, default `gen_random_uuid()` | Unique identifier |
| `device_id` | VARCHAR(100) | UNIQUE, NOT NULL | Self-assigned ID from the device |
| `current_firmware_version` | VARCHAR(50) | | Currently running version (e.g., v1.0.0) |
| `last_seen` | TIMESTAMP WITH TIME ZONE | | Last time the device pinged the server |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT `CURRENT_TIMESTAMP` | Creation time |

### `firmwares`
Stores update metadata. Physical files and signatures are stored in the file system/storage.

| Column | Type | Constraints / Default | Description |
|--------|------|-----------------------|-------------|
| `id` | UUID | PRIMARY KEY, default `gen_random_uuid()` | Unique identifier |
| `version` | VARCHAR(50) | UNIQUE, NOT NULL | Example: 'v1.1.0' |
| `release_notes` | TEXT | | Notes about the firmware update |
| `file_path` | VARCHAR(255) | NOT NULL | File path of the firmware binary |
| `signature_path` | VARCHAR(255) | NOT NULL | File path of the firmware signature |
| `file_size` | BIGINT | NOT NULL | File size in bytes |
| `checksum_sha256` | VARCHAR(64) | NOT NULL | SHA256 checksum for Client to verify integrity |
| `is_active` | BOOLEAN | DEFAULT `true` | Indicates whether firmware is allowed |
| `created_at` | TIMESTAMP WITH TIME ZONE | DEFAULT `CURRENT_TIMESTAMP` | Creation time |

### `device_update_logs`
Stores telemetry and update logs reported from devices.

| Column | Type | Constraints / Default | Description |
|--------|------|-----------------------|-------------|
| `id` | UUID | PRIMARY KEY, default `gen_random_uuid()` | Unique identifier |
| `device_id` | UUID | NOT NULL, REFERENCES `devices(id)` | Associated device |
| `firmware_id` | UUID | NOT NULL, REFERENCES `firmwares(id)` | Associated firmware |
| `status` | update_state | DEFAULT 'pending' | Status of the update |
| `error_message` | TEXT | | Notes if failed or rolled back |
| `started_at` | TIMESTAMP WITH TIME ZONE | | Time update started |
| `completed_at` | TIMESTAMP WITH TIME ZONE | | Time update completed |

*Index: `idx_logs_device` on `device_id`*

## 3. Raw SQL Script
The complete raw SQL dump used to initialize this schema can be found at:
[init.sql](file:///home/okai/workspace/Pet_project/ota-server/be-api/app/db/init.sql)
