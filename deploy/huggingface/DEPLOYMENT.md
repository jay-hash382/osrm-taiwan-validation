# Hugging Face deployment

- Space SDK: Docker
- Intended hardware: `cpu-basic` (hardware has no hourly price, but Hugging Face now requires a paid account plan to create a Docker Space)
- OSRM port: 7860
- Graph source: latest Geofabrik Taiwan PBF at image-build time
- Profile/algorithm: official `car.lua` / MLD
- Visibility: public test service

The multi-stage build keeps the source PBF and extraction intermediates out of the final runtime image where possible. The generated OSRM graph remains about 1.05 GiB.

This is an independent validation deployment. Do not configure the App or production backend to use it until external smoke, endpoint-policy and load tests pass.

Current status: blocked before Space creation by Hugging Face HTTP 402 account-plan requirement. No Space or billable resource was created.
