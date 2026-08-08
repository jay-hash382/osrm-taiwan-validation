---
title: Taiwan OSRM Routing Test
emoji: 🛣️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
startup_duration_timeout: 30m
short_description: Independent Taiwan OSRM routing test API
---

# Taiwan OSRM routing test API

Independent, non-production OSRM MLD service built from the latest Geofabrik Taiwan OpenStreetMap extract and the official OSRM car profile.

This Space is for route-quality, endpoint-snapping and runtime-load validation. It is not connected to the Road Weather Taiwan App or weather backend.

Example endpoint:

```text
/route/v1/driving/120.3014,22.6273;120.6848,24.1477?overview=false
```

Data: © OpenStreetMap contributors, distributed by Geofabrik under ODbL.

