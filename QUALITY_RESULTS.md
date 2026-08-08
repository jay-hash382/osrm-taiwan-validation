# Taiwan OSRM route-quality audit

Audit date: 2026-08-08

- GitHub Actions run: [31265204495](https://github.com/jay-hash382/osrm-taiwan-validation/actions/runs/31265204495)
- OSM source: Geofabrik `taiwan-latest.osm.pbf`
- Algorithm/profile: OSRM MLD / official `car.lua`
- Build time: 89 seconds
- Graph size: 1,125,052,056 bytes (1.05 GiB)
- Idle runtime memory snapshot: 804.4 MiB
- Profile policy tokens: all present

## Summary

| Status | Count |
|---|---:|
| Pass | 4 |
| Manual review | 4 |
| Hard failure | 0 |

The audit treats `review` as a successful but unresolved route. It only fails the workflow for no route, endpoint snapping over 300 m, invalid geometry/distance, missing guidance, or implausible annotation speed.

## Results

| Case | Result | Route | Endpoint snap | Main finding |
|---|---|---:|---:|---|
| NCKU campus exit | Review | 1.485 km | 25.8 / 36.9 m | Short route detour ratio 3.60; inspect campus exits and one-way layout |
| Dream Mall parking exit | Review | 2.117 km | 82.6 / 11.3 m | Place centre is not a suitable driving entrance |
| Xiluo service-area exit | Review | 21.571 km | 11.0 / 8.0 m | Directional motorway access produces a 9.41 detour ratio |
| Qingshui service-area exit | Pass | 8.185 km | 16.8 / 3.0 m | Service-area and local network are connected |
| Dingjin interchange | Review | 4.613 km | 2.5 / 82.6 m | Destination coordinate is too far from a routable segment for silent snapping |
| Puli–Cingjing | Pass | 29.938 km | 11.8 / 22.1 m | Mountain route connected; maximum annotation speed 69.1 km/h |
| Hualien–Suao | Pass | 85.449 km | 25.0 / 0.8 m | Suhua corridor connected; maximum annotation speed 68.4 km/h |
| Kaohsiung short urban | Pass | 0.810 km | 5.4 / 5.9 m | No excessive one-way detour detected |

## Profile-policy audit

The exact `car.lua` used by the build contained the expected handling markers for:

- access blacklist and `private` access;
- service-road access restrictions;
- `emergency_access` exclusion;
- `steps`, `construction` and `proposed` avoidance;
- penalties for parking aisles and driveways.

This confirms the official profile contains these policies. It does not prove every Taiwan OSM road has correct tags.

## Decisions before integration

1. Keep the display-road filter separate from the OSRM routing graph.
2. Do not remove all `service` roads; campus, service-area and destination access depends on them.
3. Use a place entrance or OSRM snapped waypoint instead of blindly routing from a geocoder's polygon centre.
4. Return endpoint snap distance to the backend/App contract:
   - up to 75 m: normally acceptable;
   - 75–300 m: show the selected road/entrance and require review where appropriate;
   - over 300 m: reject or ask the user to choose another point.
5. Do not reject a service-area route based only on aerial detour ratio; divided motorways and one-way exits legitimately require long detours.
6. Before public navigation, visually review the emitted `quality-routes.geojson`, then run concurrency and rerouting load tests on the selected host.

No App, weather backend or map-tile changes were made.

