# Taiwan OSRM runtime load results

Test date: 2026-08-08

- GitHub Actions run: [31265528096](https://github.com/jay-hash382/osrm-taiwan-validation/actions/runs/31265528096)
- Workload: 1,200 route requests plus warm-up requests
- Request mix: initial planning and GPS-deviation rerouting
- Response shape: full GeoJSON geometry, steps and distance/duration/speed annotations
- Average response body: about 95 KiB
- Error-rate limit: 1%
- p95 limit: 500 ms

## Results

| Concurrency | Requests | Errors | Throughput | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 300 | 0 | 241.53 req/s | 4.76 ms | 6.83 ms | 7.57 ms |
| 4 | 300 | 0 | 479.07 req/s | 8.29 ms | 13.31 ms | 16.94 ms |
| 8 | 300 | 0 | 507.79 req/s | 15.25 ms | 24.23 ms | 32.16 ms |
| 16 | 300 | 0 | 491.76 req/s | 29.78 ms | 56.57 ms | 65.71 ms |

At concurrency 16:

- initial-route p95: 54.17 ms;
- reroute p95: 56.99 ms;
- request errors: 0;
- observed container CPU: up to 116.46%;
- observed container memory: about 808.9 MiB.

OSRM became reachable 1,136 ms after the container start command. The post-test idle memory snapshot was 808.6 MiB.

## Interpretation

- The selected Taiwan MLD graph handled the tested concurrency with substantial latency margin.
- Rerouting was slightly slower than initial-route requests in this workload, but remained below 57 ms p95 at concurrency 16.
- Memory stayed near 809 MiB during the captured load samples, so graph residency dominates this small test rather than per-request growth.
- Building the graph still needs more memory than serving it. Build the graph in CI and deploy the generated files instead of rebuilding on a small production host.

## Limits of this measurement

- Client and OSRM ran on the same GitHub runner. Results exclude public-network latency, TLS and reverse-proxy overhead.
- The test is a short burst, not a multi-hour soak test.
- GitHub runner CPU performance is not equivalent to a future free or low-cost host.
- The requests reuse eight deterministic route pairs and do not represent every Taiwan origin/destination combination.
- No weather-risk join, authentication, rate limiting or backend adapter was included.

## Deployment guidance for the next stage

- Reserve at least 2 GiB RAM for an OSRM-only runtime; 4 GiB provides safer operating-system, proxy and monitoring headroom.
- Prefer at least 2 vCPU for predictable concurrent rerouting.
- Keep OSRM separate from the current Render weather service.
- Put a backend adapter in front of OSRM for endpoint policy, timeouts, observability and weather-risk enrichment.
- Repeat the same workload through the public deployment before connecting any App build.

No App, weather backend or map-tile changes were made.

