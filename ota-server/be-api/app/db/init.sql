-- ==============================================================================
-- DATABASE SCHEMA: SECURE OTA FRAMEWORK (MVP)
-- ==============================================================================

CREATE TYPE update_state AS ENUM ('pending', 'downloading', 'installing', 'success', 'failed', 'rolled_back');

-- ==============================================================================
-- TABLE 1: FIRMWARES
-- ==============================================================================
CREATE TABLE firmwares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) UNIQUE NOT NULL,
    release_notes TEXT,
    file_path VARCHAR(255) NOT NULL,
    signature_path VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TABLE 2: DEVICES
-- ==============================================================================
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id VARCHAR(100) UNIQUE NOT NULL,   -- self-assigned ID từ device
    current_firmware_version VARCHAR(50),
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- TABLE 3: UPDATE LOGS
-- ==============================================================================
CREATE TABLE device_update_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id),
    firmware_id UUID NOT NULL REFERENCES firmwares(id),
    status update_state DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_logs_device ON device_update_logs(device_id);