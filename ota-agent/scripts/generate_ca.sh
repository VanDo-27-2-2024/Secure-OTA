#!/bin/bash
set -e

mkdir -p ca
echo "Generating Root CA private key..."
openssl genrsa -out ca/ca.key 4096

echo "Generating Root CA certificate..."
openssl req -x509 -new -nodes -key ca/ca.key -sha256 -days 3650 -out ca/ca.crt -subj "/CN=OTA_Root_CA"

echo "CA generated in ca/ directory."
