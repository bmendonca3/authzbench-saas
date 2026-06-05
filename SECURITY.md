# Security Policy

AuthZBench-SaaS contains intentionally vulnerable applications for local
benchmarking. The vulnerable behavior is expected and should not be reported as
a vulnerability in this repository unless it escapes the benchmark boundary.

## Scope For Reports

Report issues such as:

- benchmark code that attacks systems outside the local test environment
- unintended credential disclosure
- unsafe default network behavior
- scorer bypasses that produce a false passing result without satisfying the
  backend oracle
- container or runner behavior that persists beyond the benchmark run

Do not report the intentional BOLA/BFLA behavior in the target apps unless the
issue also affects the benchmark host or another unintended system.

## Safe Use

- Run only in local, isolated, or CI test environments.
- Do not expose target apps to the public internet.
- Do not run untrusted agent commands unless they are sandboxed by your own
  environment.
- Review generated submissions before sharing them publicly.

