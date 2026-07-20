# AGENTS.md

Guidance for agents working in this public Python template repository.

## Repository Purpose

Keep this template portable, minimal, and useful for small Python applications and services. Do not add host-specific paths, personal configuration, secrets, private infrastructure details, or generated machine state.

The main project surfaces are `src/` for application code, `tests/` for unit and contract tests, `script/` for stable developer and CI entrypoints, `vendor/cache/` for committed dependency wheels, and `.github/workflows/` for CI and releases.

## Working Principles

- Prefer the smallest complete change and avoid speculative abstractions.
- Start with the Python standard library and add a dependency only when it clearly earns its maintenance and trust cost.
- Keep `script/*` as the shared interface used by developers, CI, builds, and releases.
- Preserve offline bootstrap, test, lint, and build paths by using the lockfile and committed wheel caches.
- Add focused tests for behavior changes and regression tests for bug fixes.
- Keep runtime logs useful without recording secrets or sensitive request data.

## Versions and Dependencies

- `.python-version` is the exact supported Python version and must agree with `pyproject.toml`.
- `.uv-version` is the exact bootstrap and lock-management version.
- Keep direct dependencies exact-version pinned, `uv.lock` current, exported requirements hash-locked, and matching wheels committed for every supported platform.
- Use `script/vendor` only for intentional networked dependency refreshes. Commit the manifest, lock, exports, and wheel changes together.
- Pin Git dependencies to full 40-character commit SHAs and container images to immutable manifest digests.

## Scripts and Testing

- `script/bootstrap` installs only from the committed wheel cache.
- `script/test` enforces 100% line, branch, and first-party function coverage.
- `script/lint` verifies Ruff checks and formatting.
- `script/build` creates release archives and checksums without changing tracked files.
- `script/acceptance` exercises the packaged application through its containerized public interface.
- `script/vendor` is the sole dependency update path that requires network access.

Keep unit tests fast, deterministic, and independent of live services. Cover successful behavior, failures, edge cases, and every meaningful branch. Do not weaken coverage or repository contract checks to make a change pass.

## CI and Documentation

- Keep external GitHub Actions pinned to full commit SHAs, Fence first in every job, permissions minimal, and checkout credentials disabled.
- Keep Markdown prose unwrapped.
- Update the README, scripts, workflows, tests, and this file together when their contracts change.
