# OTA Agent

This is a simple C++ OTA agent skeleton that runs as a daemon and periodically calls the healthcheck endpoint of the OTA server.

## Build

Requirements:
- CMake 3.16+
- A C++ compiler supporting C++23
- libcurl development headers

From `ota-agent`:

```bash
mkdir -p build && cd build
cmake ..
cmake --build .
```

## Run

```bash
./ota-agent [HEALTHCHECK_URL] [INTERVAL_SECONDS]
```

Defaults:
- `HEALTHCHECK_URL`: `http://127.0.0.1:8000/health`
- `INTERVAL_SECONDS`: `30`

Example:

```bash
./ota-agent http://127.0.0.1:8000/health 15
```

## Behavior

- Runs in the foreground and handles `SIGINT`/`SIGTERM` gracefully.
- Performs an HTTP GET to the health endpoint.
- Prints HTTP status and response body.
- Sleeps between checks.

## Install as a Systemd Service

To run the `ota-agent` automatically in the background as a system service:

1. **Copy the binary:**
   After building the project, copy the compiled binary to `/usr/bin/`:
   ```bash
   sudo cp build/ota-agent /usr/bin/ota-agent
   ```

2. **Copy the service file:**
   Copy the provided systemd service file to the systemd directory:
   ```bash
   sudo cp systemd/ota-agent.service /etc/systemd/system/
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ota-agent
   sudo systemctl start ota-agent
   ```

4. **Check status and logs:**
   ```bash
   sudo systemctl status ota-agent
   sudo journalctl -u ota-agent -f
   ```

# TLS / mTLS Support

The `ota-agent` now supports HTTPS and Mutual TLS (mTLS) for secure communication with the OTA server.

## Overview

- **HTTPS**: Encrypts the traffic between the agent and the server and verifies the server's identity using a Certificate Authority (CA).
- **mTLS**: Adds an extra layer by requiring the agent to present its own client certificate to the server, proving its identity before communication is allowed.

## Certificate Generation

Two scripts are provided in the `scripts/` directory to help you generate the necessary certificates.

### 1. Generate a Root CA
Run the following script to create a self-signed Certificate Authority (CA):
```bash
./scripts/generate_ca.sh
```
This generates `ca/ca.key` and `ca/ca.crt`.

### 2. Generate a Device Certificate
Run the following script to generate a client certificate for a specific device, signed by the CA generated in the previous step:
```bash
./scripts/generate_device_cert.sh <device_name>
# Example: ./scripts/generate_device_cert.sh raspberrypi4
```
This generates `certs/<device_name>/device.key` and `certs/<device_name>/device.crt`.

## Using Certificates on the Target Device

1. Create the `/etc/ota` directory on the target device:
   ```bash
   sudo mkdir -p /etc/ota
   ```
2. Copy the generated certificates to the device:
   ```bash
   sudo cp ca/ca.crt /etc/ota/
   sudo cp certs/<device_name>/device.crt /etc/ota/
   sudo cp certs/<device_name>/device.key /etc/ota/
   ```

## Running with HTTPS/mTLS

The `ota-agent` uses libcurl with `CURLOPT_USE_SSL` when connecting to `https://` URLs. For security, strict certificate and hostname verification are explicitly enabled. Insecure TLS modes (disabling peer or host verification) are intentionally not supported to ensure production-grade security.

By default, the agent looks for certificates in `/etc/ota/`. You can override these paths using command-line arguments:

```bash
./ota-agent [URL] [INTERVAL] [CA_CERT_PATH] [CLIENT_CERT_PATH] [CLIENT_KEY_PATH]
```

### Example

To run the agent connecting to an HTTPS endpoint:

```bash
./ota-agent https://ota-server:8443/health 15 /etc/ota/ca.crt /etc/ota/device.crt /etc/ota/device.key
```

### Systemd Deployment

When deploying via Systemd, make sure your certificates are correctly placed in `/etc/ota/` as documented above. Update the `ExecStart` line in your `ota-agent.service` file to include your HTTPS URL and cert paths. For example:

```ini
[Service]
ExecStart=/usr/bin/ota-agent https://ota-server:8443/health 30 /etc/ota/ca.crt /etc/ota/device.crt /etc/ota/device.key
```
