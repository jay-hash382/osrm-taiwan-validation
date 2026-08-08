FROM ghcr.io/project-osrm/osrm-backend:latest AS builder

USER root
WORKDIR /build
ADD https://download.geofabrik.de/asia/taiwan-latest.osm.pbf /build/taiwan-latest.osm.pbf
RUN mkdir -p /build/osrm \
    && osrm-extract -p /opt/car.lua --output /build/osrm/taiwan.osrm /build/taiwan-latest.osm.pbf \
    && osrm-partition /build/osrm/taiwan.osrm \
    && osrm-customize /build/osrm/taiwan.osrm \
    && rm /build/taiwan-latest.osm.pbf

FROM ghcr.io/project-osrm/osrm-backend:latest

USER root
RUN groupadd --gid 1000 user \
    && useradd --uid 1000 --gid 1000 --create-home user
COPY --from=builder --chown=user:user /build/osrm /data/osrm

USER user
EXPOSE 7860
CMD ["osrm-routed", "--algorithm", "mld", "--port", "7860", "/data/osrm/taiwan.osrm"]

