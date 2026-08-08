# Endpoint snapping policy

Decision date: 2026-08-08

This policy is fixed for the future routing adapter. The current validation repository enforces the same thresholds, but does not integrate them into the App.

| Snap distance | Required behaviour |
|---|---|
| 0–75 m | Normally acceptable. Return both the requested coordinate and snapped waypoint for diagnostics. |
| Over 75 m, up to 300 m | Return the actual snapped road/waypoint and surface the difference to the user; require confirmation when the place or entrance is ambiguous. |
| Over 300 m | Reject route planning or ask the user to select another point. Never silently route from the distant road. |

Additional rules:

- Apply the policy independently to origin and destination.
- A geocoder polygon centre is not automatically a driving entrance.
- Service areas and divided motorways may have valid long route detours even when snapping is close; snap distance and route detour are separate checks.
- The backend contract must preserve requested coordinates, snapped coordinates, snap distances and road names.
- Automatic rerouting from a live GPS point may use the same 300 m hard ceiling, but should additionally consider GPS accuracy and map-matching confidence.

