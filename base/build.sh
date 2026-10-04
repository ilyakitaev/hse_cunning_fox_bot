#!/bin/bash
set -e

echo "Building base image..."
docker build --no-cache -f base/Dockerfile -t hse_cunning_fox_bot_base:latest . \
#  --build-arg HTTP_PROXY=http://192.168.171.30:2080 \
#  --build-arg HTTPS_PROXY=http://192.168.171.30:2080

echo "Base image built successfully!"
