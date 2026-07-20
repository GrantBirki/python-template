# python-template

A small, production-shaped template for Python applications and services. It provides a JSON web service while keeping the dependency graph, build path, and maintenance surface deliberately small.

## Requirements

- [pyenv](https://github.com/pyenv/pyenv) with Python `3.14.0`
- Docker for the container build and acceptance suite

The repository bootstraps its exact uv version and Python packages from committed wheels. Normal development, testing, linting, and builds do not download packages.

## Quick Start

```console
$ pyenv install 3.14.0
$ script/bootstrap
$ script/server
```

The server listens on `127.0.0.1:8000` by default. `HOST`, `PORT`, and `LOG_LEVEL` provide environment defaults, while `--host`, `--port`, and `--log-level` take precedence.

```console
$ curl http://127.0.0.1:8000/health
{"status":"ok"}
$ curl 'http://127.0.0.1:8000/hello?name=Grant'
{"message":"Hello, Grant!"}
```

Every response includes an `X-Request-ID`. A valid caller-provided ID is preserved; otherwise the service generates one.

## Scripts

- `script/bootstrap` creates the local environment entirely from committed wheels.
- `script/server` runs the Waitress service.
- `script/test` runs the unit suite and enforces 100% line, branch, and function coverage.
- `script/lint` checks the code with Ruff.
- `script/build` creates a wheel, source distribution, and checksums under `dist/`.
- `script/docker-build` creates the pinned Linux amd64 application image.
- `script/acceptance` exercises the built wheel through the running container.
- `script/vendor` is the intentional networked path for refreshing locked dependencies and both supported wheel caches.

Developers and CI use these same entrypoints.

## Dependencies

Waitress is the only runtime dependency. The test and lint toolchain adds coverage.py and Ruff. All direct dependencies use exact versions, `uv.lock` records the complete resolution, exported requirements include hashes, and binary wheels are committed for macOS arm64 and Linux x86_64.

To update dependencies, edit the exact versions in `pyproject.toml` or `.uv-version`, then run:

```console
$ script/vendor
```

Review and commit the manifest, lockfile, exported requirements, and wheel-cache changes together. All other scripts fail on unsupported platforms or missing vendored artifacts instead of reaching the network.

## Testing and Builds

```console
$ script/test
$ script/lint
$ script/build
$ script/acceptance
```

The unit suite is deterministic and does not call live services. The acceptance suite builds the deployment-shaped container and tests the public HTTP interface. The Docker build may need to pull the pinned base image once, but Python packages are installed from committed wheels with build networking disabled.

## Releases

`VERSION` is the release source of truth. A stable, increasing `vMAJOR.MINOR.PATCH` change merged into `main` builds the exact commit, creates checksummed wheel and source archives, attests their provenance, and publishes them to a GitHub Release. This template does not publish to PyPI or a container registry.

## Customizing the Template

Replace the sample routes and package metadata while preserving the repository scripts, exact language version, offline dependency path, tests, immutable workflow references, and release integrity checks.
