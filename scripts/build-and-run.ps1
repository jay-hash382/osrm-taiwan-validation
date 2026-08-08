$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Data = Join-Path $Root "data"
$Pbf = Join-Path $Data "taiwan-latest.osm.pbf"
$Image = "ghcr.io/project-osrm/osrm-backend:v26.7.3"

New-Item -ItemType Directory -Force (Join-Path $Data "osrm") | Out-Null
if (-not (Test-Path $Pbf)) {
    Invoke-WebRequest -Uri "https://download.geofabrik.de/asia/taiwan-latest.osm.pbf" -OutFile $Pbf
}

docker run --rm -t -v "${Data}:/data" $Image osrm-extract -p /opt/car.lua --output /data/osrm/taiwan.osrm /data/taiwan-latest.osm.pbf
if ($LASTEXITCODE -ne 0) { throw "osrm-extract failed" }
docker run --rm -t -v "${Data}:/data" $Image osrm-partition /data/osrm/taiwan.osrm
if ($LASTEXITCODE -ne 0) { throw "osrm-partition failed" }
docker run --rm -t -v "${Data}:/data" $Image osrm-customize /data/osrm/taiwan.osrm
if ($LASTEXITCODE -ne 0) { throw "osrm-customize failed" }

docker rm -f osrm-taiwan-validation 2>$null | Out-Null
docker run -d --rm --name osrm-taiwan-validation -p 5000:5000 -v "${Data}:/data:ro" $Image osrm-routed --algorithm mld /data/osrm/taiwan.osrm
