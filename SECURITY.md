# Security policy

How to report vulnerabilities and where to find deployment security guidance.

## Reporting a vulnerability

Please do **not** report security vulnerabilities in public issues or pull requests.

- **Preferred:** Use [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/creating-a-repository-security-advisory) for this repository to report vulnerabilities privately.
- **Alternative:** If you cannot use GitHub, contact the maintainers through a private channel (e.g. the email or contact method listed in the repository profile) and include a clear description and steps to reproduce.

We will acknowledge your report and aim to respond within a reasonable window. We may ask for clarification or more detail. If the issue is accepted, we will work on a fix and coordinate disclosure (e.g. after a release that includes the fix).

## Deployment security

For production deployment (secrets, CORS, rate limiting, worker isolation), see [docs/deployment.md](docs/deployment.md) and [docs/running.md](docs/running.md). Never commit `.env` or real API keys; use [.env.example](.env.example) as a template only.

**See also:** [docs/deployment.md](docs/deployment.md), [docs/running.md](docs/running.md), [CONTRIBUTING.md](CONTRIBUTING.md).
