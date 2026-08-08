# Public test-host evaluation

Evaluation date: 2026-08-08

Measured OSRM requirements:

- graph: about 1.05 GiB;
- runtime memory: about 809 MiB;
- recommended test allocation: at least 2 GiB RAM;
- generated graph should be built in CI, not on a small runtime host.

## Current options

| Platform | Free/test capacity | Decision |
|---|---|---|
| Hugging Face Docker Space | CPU Basic has 2 vCPU / 16 GB, but creating compute Spaces now requires a PRO/Team/Enterprise plan | Technically suitable, blocked by subscription |
| Render Free | 512 MB RAM | Insufficient |
| Koyeb Free | 512 MB RAM, 0.1 vCPU | Insufficient |
| Google Cloud Run | Configurable 2 GiB request-based instance, scale-to-zero and monthly free allowance | Recommended next candidate; billing account required |

The attempted Hugging Face repository creation returned HTTP 402 before any Space was created. No Hugging Face compute resource exists and no charge was incurred.

## Google Cloud Run guardrails if approved

- request-based billing;
- `min-instances=0`;
- `max-instances=1`;
- 2 GiB RAM and 2 vCPU for the first external test;
- concurrency capped at 16;
- deploy in Taiwan or Tokyo only after comparing region pricing/free-tier treatment;
- create a budget alert before deployment;
- delete the test service after external validation if it is not retained.

Cloud Run has a monthly free allowance, but enabling it requires a billing account and does not constitute a hard zero-cost cap. Deployment must not proceed without explicit billing authorization.

