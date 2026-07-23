# Tau Prime packaging and release

Tau Prime uses a dependency-free in-tree build backend so source distributions and wheels can be built in constrained Python environments.

## a-Shell installation

The supported a-Shell install path is from the GitHub release tarball, not a git checkout:

```sh
python3.13 -m pip install --user ./tau-prime.tar.gz
```

The release workflow publishes `tau-prime.tar.gz`, a versioned tarball, and `SHA256SUMS`.

## CI/release flow

Version tags use `v<version>`. The release workflow checks that the tag matches `pyproject.toml`, runs tests, builds the sdist, smoke-tests installation, and publishes assets.

## Build backend data files

Bundled Markdown data under packages must be included in wheels as well as sdists. Self-knowledge Markdown files are package data and should survive installation from a release tarball.

## Actions cleanup

Actions artifacts, caches, and old runs are pruned aggressively to keep storage bounded.
