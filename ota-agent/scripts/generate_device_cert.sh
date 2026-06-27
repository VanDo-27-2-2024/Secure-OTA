#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <device_name>"
    exit 1
fi

DEVICE_NAME=$1
mkdir -p "certs/${DEVICE_NAME}"

echo "Generating private key for ${DEVICE_NAME}..."
openssl genrsa -out "certs/${DEVICE_NAME}/device.key" 2048

echo "Generating CSR for ${DEVICE_NAME}..."
openssl req -new -key "certs/${DEVICE_NAME}/device.key" -out "certs/${DEVICE_NAME}/device.csr" -subj "/CN=${DEVICE_NAME}"

echo "Signing certificate for ${DEVICE_NAME} with CA..."
openssl x509 -req -in "certs/${DEVICE_NAME}/device.csr" -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial -out "certs/${DEVICE_NAME}/device.crt" -days 3650

echo "Certificate generated in certs/${DEVICE_NAME}/ directory."
