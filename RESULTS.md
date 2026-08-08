# Taiwan OSRM validation results

首次完整驗證：2026-08-08

- GitHub Actions run: [31264777667](https://github.com/jay-hash382/osrm-taiwan-validation/actions/runs/31264777667)
- OSM extract: Geofabrik `taiwan-latest.osm.pbf`
- OSRM image digest: `sha256:3ac496ff8fd7e1af53846179d73d06a97f719c8ad2217d008ed868942398665c`
- Algorithm/profile: MLD / official `car.lua`
- Build time: 76 seconds
- Generated graph: 1,124,890,264 bytes (1.05 GiB)
- Idle runtime memory snapshot: 799.3 MiB

## Route results

| Case | Distance | Duration | API latency | Endpoint snap | Result |
|---|---:|---:|---:|---:|---|
| Kaohsiung–Taichung cross-city | 199.696 km | 146.5 min | 22.6 ms | 2.9 / 12.2 m | Pass |
| Kaohsiung urban roads | 3.082 km | 5.7 min | 2.7 ms | 68.5 / 45.1 m | Pass |
| Urban–interchange connection | 5.960 km | 11.5 min | 1.9 ms | 27.2 / 38.3 m | Pass |
| Residential–primary road | 3.098 km | 5.9 min | 2.4 ms | 19.9 / 11.9 m | Pass |

## Nearest-road results

| Case | Nearest routable road | Result |
|---|---:|---|
| Campus/service-road access | 2.0 m | Pass |
| Motorway service-area vicinity | 206.5 m | Pass with review required |

All six automated cases passed. The service-area result is below its initial 1,000 m safety threshold, but 206.5 m is too far for silent production snapping. Before App integration, the endpoint policy should return snap distance and require confirmation or reject an endpoint when it exceeds the final threshold.

## What this proves

- A complete Taiwan OSM car graph can be built successfully in GitHub Actions.
- Motorway and general-road networks are connected for the tested routes.
- Residential and eligible service-road locations can be snapped by the official car profile.
- Runtime size is feasible for a small dedicated routing service, subject to load testing.

## What remains unproven

- Route quality across private roads, parking aisles, alleys and restricted campuses.
- Correct handling of Taiwan-specific turn restrictions and unusual interchanges.
- Runtime memory and latency under concurrent rerouting load.
- Long-running service stability, deployment cost and cold-start behaviour.
- Integration with existing weather-risk segmentation and navigation progress.

No App, weather backend or map-tile integration was performed in this validation.

The follow-up route-quality audit is documented in [QUALITY_RESULTS.md](QUALITY_RESULTS.md).

Runtime concurrency and rerouting measurements are documented in [LOAD_RESULTS.md](LOAD_RESULTS.md).
