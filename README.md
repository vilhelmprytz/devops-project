# dgadetect

MLOps pipeline for a deliberately simple DGA (domain generation algorithm) domain classifier, built for the KTH DevOps course (see `project-proposal.md`). The model is treated as the build artifact: every pull request retrains it and gates it against the latest release, and every merge releases and deploys it.

See [report.pdf](report.pdf) for the project report.

## Pipeline examples

- [PR #5](https://github.com/vilhelmprytz/devops-project/pull/5): A model regression fails the metrics gate, blocking merge.
- [PR #6](https://github.com/vilhelmprytz/devops-project/pull/6): A model change passes the metrics gate and all required CI checks.

## Pipeline

`.github/workflows/ci.yml` runs on every pull request and on `main`:

| Job       | What it does                                                                                                                     |
| --------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `test`    | ruff, black and the unit tests                                                                                                   |
| `model`   | builds the data, runs the data tests, trains, and runs the metrics gate; the gate table is in the job summary                    |
| `image`   | builds the arm64 image with that exact model, checks `/health`, and on `main` pushes it to `ghcr.io/vilhelmprytz/devops-project` |
| `release` | `main` only: creates the GitHub release `vX.Y.Z` with `model.skops` and `metrics.json`                                           |
| `deploy`  | `main` only: deploys the new version to the Raspberry Pi and rolls back if it isn't healthy                                      |

`.github/workflows/semgrep.yml` runs Semgrep static analysis on every pull request, on `main` and weekly.

**Metrics gate:** the gate fails if the false-positive rate or any family's false-negative rate breaks its limit in `config.toml`, or is more than `gate.regression_tolerance` worse than in the latest release's `metrics.json`.

**Merging:** a ruleset on `main` requires `test`, `model`, `image` and `semgrep` to pass and one approving review. GitHub Copilot also reviews every pull request. Direct pushes to `main` are blocked.

**Versioning:** every merge to `main` is a release. Label the pull request `release:major` or `release:minor` to bump that part of the version; otherwise the patch number goes up. The image is tagged with the version, and `/health` reports it.

## Quality and security

- Semgrep on every pull request, as a required check.
- Dependabot (`.github/dependabot.yml`): weekly updates for the Python packages, GitHub Actions and the Docker base image, each going through the full pipeline.
- Secret scanning with push protection.
- GitHub Actions pinned by commit SHA, the base image by digest, and Python packages installed with `--require-hashes`.

## Deployment

`infra/playbook.yml` (Ansible) sets up the Raspberry Pi from a fresh OS: Docker, Tailscale, a `deploy` user and the deploy script. The API runs on the Pi at `http://devops-project.local2.hejduk.se:8000`.

The `deploy` job joins the tailnet with an ephemeral auth key and runs `dgadetect-deploy VERSION` on the Pi over SSH. The script swaps the container and waits for `/health` to report the new version; `/health` passes only if the model classifies a known benign and a known DGA domain correctly. Otherwise the previous version is started again and the job fails. The SSH key can only run that script, and both secrets live in the `production` environment, which only `main` can use.

One-time setup:

1. Create a Tailscale auth key (not reusable) and run `make pi-setup`, entering the key when asked. Then disable key expiry for the Pi in the Tailscale admin console.
2. Create a reusable, ephemeral auth key for CI and store it with `gh secret set TS_AUTHKEY --env production`.
3. Store the private half of `infra/deploy_key.pub` with `gh secret set DEPLOY_SSH_KEY --env production`.

## Running locally

Requires Python 3.14, pipenv and Docker.

```bash
make install
make lint test                        # the test job
make data test-data train compare     # the model job
make serve                            # API on http://localhost:8000
```

## Credits and license

The DGA generators in `dgadetect/dga/` are ported from [baderj/domain_generation_algorithms](https://github.com/baderj/domain_generation_algorithms) (GPL-2.0), so this repository is GPL-2.0 as well; see `LICENSE.txt`.

## Authors

- Vilhelm Prytz (vprytz@kth.se)
- Filip Dimitrijevic (filipdi@kth.se)

## Use of AI-assisted tools

We used Claude Code (Anthropic) to help with the boilerplate for the DGA generator, the CI/CD and infrastructure is our own work. GitHub Copilot code review runs on every pull request through the repository ruleset.
