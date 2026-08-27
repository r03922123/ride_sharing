# Devcontainer notes

## Base image is pinned to `-bookworm`

`mcr.microsoft.com/devcontainers/python:3.11` now resolves to a Debian **trixie**
base, on which the `docker-in-docker` feature fails (`moby-cli` packages are not
in trixie). We pin `:3.11-bookworm` to keep feature compatibility.

## Re-adding Docker for Phase 1 (`docker compose` stack)

When Phase 1 introduces the compose stack, add back to `features`:

```jsonc
"ghcr.io/devcontainers/features/docker-in-docker:2": {}
```

On bookworm the default (`moby: true`) works. If the base image is ever bumped to
trixie, either keep it on bookworm or set `{ "moby": false }` (Docker CE instead
of Moby), or switch to `docker-outside-of-docker` (shares the host socket).
