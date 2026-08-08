# Hugging Face deployment

- Space SDK: Docker
- Intended hardware: free `cpu-basic`
- OSRM port: 7860
- Graph source: latest Geofabrik Taiwan PBF at image-build time
- Profile/algorithm: official `car.lua` / MLD
- Visibility: public test service

The multi-stage build keeps the source PBF and extraction intermediates out of the final runtime image where possible. The generated OSRM graph remains about 1.05 GiB.

This is an independent validation deployment. Do not configure the App or production backend to use it until external smoke, endpoint-policy and load tests pass.

