#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="$ROOT/data"
IMAGE="ghcr.io/project-osrm/osrm-backend:v26.7.3"

mkdir -p "$DATA/osrm"
if [ ! -f "$DATA/taiwan-latest.osm.pbf" ]; then
  curl --fail --location --retry 3 \
    --output "$DATA/taiwan-latest.osm.pbf" \
    https://download.geofabrik.de/asia/taiwan-latest.osm.pbf
fi

docker run --rm -t -v "$DATA:/data" "$IMAGE" \
  osrm-extract -p /opt/car.lua --output /data/osrm/taiwan.osrm /data/taiwan-latest.osm.pbf
docker run --rm -t -v "$DATA:/data" "$IMAGE" osrm-partition /data/osrm/taiwan.osrm
docker run --rm -t -v "$DATA:/data" "$IMAGE" osrm-customize /data/osrm/taiwan.osrm

docker rm -f osrm-taiwan-validation >/dev/null 2>&1 || true
docker run -d --rm --name osrm-taiwan-validation -p 5000:5000 \
  -v "$DATA:/data:ro" "$IMAGE" osrm-routed --algorithm mld /data/osrm/taiwan.osrm
