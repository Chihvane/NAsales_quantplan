#!/usr/bin/env bash
set -euo pipefail

TARGET_TAG="${1:?target image tag required}"
echo "Rolling back Decision OS release to ${TARGET_TAG}"
echo "docker compose pull && docker compose up -d --force-recreate"
