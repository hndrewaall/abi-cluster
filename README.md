# abi-cluster

An Ethereum **mainnet staking node**: [go-ethereum](https://github.com/ethereum/go-ethereum)
as the execution client and [Lighthouse](https://github.com/sigp/lighthouse) as
the consensus client, run as three `docker compose` services.

| service     | image        | role                                              |
|-------------|--------------|---------------------------------------------------|
| `geth`      | `geth`       | execution client (JSON-RPC, engine API, metrics)  |
| `beacon`    | `lighthouse` | beacon node (`lighthouse beacon_node`)            |
| `validator` | `lighthouse` | validator client (`lighthouse validator_client`)  |

`beacon` and `validator` share one image, so a release builds **two** images.

> **This node has real ETH at stake.** The one hard rule is that the validator
> keys must never be live in two places at once — that double-signs and gets the
> stake slashed. A rolling `docker compose up -d` recreate of the single
> `validator` service is safe (a few missed attestations); a second validator
> anywhere is not.

## Layout

```
geth/Dockerfile         execution client build   (ARG TAG = the go-ethereum release)
lighthouse/Dockerfile   consensus client build   (ARG TAG = the Lighthouse release)
docker-compose.yml      the deployment manifest  (pins the image tags it runs)
controller/             S3-backed lock helper for coordinating a single active node
.gitea/workflows/       CI: builds and publishes the images on a release tag
```

## Versioning and releases

Images are **built and published only by CI**, and only ever with a semver tag.
There is no `latest`: a mutable tag means two machines can resolve the same
name to different code, which is the wrong property for something that signs
blocks. The registry also refuses to overwrite an existing tag — a mistake gets
a new patch number, never a re-cut.

Two independent version numbers are in play, and it is worth keeping them
straight:

* the **upstream client versions** — `ARG TAG` in each Dockerfile, e.g. geth
  `v1.17.5`, Lighthouse `v8.2.2`;
* the **release version of this repo** — `vX.Y.Z`, which names the pair of
  images built from a particular commit. It is not derived from either client's
  version.

### Cutting a release

1. Bump what you are changing — usually `ARG TAG` in `geth/Dockerfile` and/or
   `lighthouse/Dockerfile`.

   Check the builder toolchains at the same time: if the new geth needs a newer
   Go than the `FROM golang:...` line (see go-ethereum's `go.mod`), or the new
   Lighthouse needs a newer Rust than the `FROM rust:...` line (see its
   `rust-toolchain.toml`), bump those too — the build fails otherwise, and it
   fails late.

2. Pin the new release version in `docker-compose.yml` (all three `image:`
   lines). The compose file is the deployment manifest, so the version that
   will run is reviewable in the diff.

3. Land it on `main` via a pull request.

4. Tag it. The tag is the only thing that triggers a build:

   ```sh
   make release VERSION=v1.0.1
   ```

   which checks the version shape, checks that `docker-compose.yml` really pins
   it, then tags and pushes.

5. CI builds both images and pushes `geth:v1.0.1` and `lighthouse:v1.0.1`.
   A push notification says *published* — that is not *deployed*.

CI refuses the release if the tag is not a bare `vX.Y.Z`, if it is not an
ancestor of `main`, or if either image already exists at that tag.

### Deploying

Publishing does not roll the node. Once CI is green:

```sh
docker compose pull
docker compose up -d
```

Then verify, because a node that fails to start is the failure mode that costs
attestations continuously:

```sh
docker compose ps
docker compose exec geth   geth       version
docker compose exec beacon lighthouse --version
docker compose logs geth      --tail 30   # importing blocks, no fatal
docker compose logs beacon    --tail 40   # engine API reachable, syncing
docker compose logs validator --tail 40   # keys loaded, attesting
```

The beacon node may log execution-endpoint errors for a minute or two after a
recreate while geth's engine API comes up; `restart: unless-stopped` rides that
out. Escalate only if it persists.

## Local builds

`make images` (or `make geth-image` / `make lighthouse-image`) builds locally
and tags `:local`. These do not push — the registry accepts writes from CI
alone, so a release cannot be made from a workstation even by accident.

## CI

`.gitea/workflows/release.yml` runs on a self-hosted runner with no Docker
socket; it builds with rootless [buildah](https://buildah.io/). The workflow
lives under `.gitea/` rather than `.github/` deliberately — **the GitHub remote
is a read-only public mirror** so that anyone staking alongside this node can
read the configuration, and nothing there builds, publishes, or deploys.

Because the runner's filesystem rules out an overlay-backed image store, builds
use the `vfs` storage driver and run without a layer cache: a release compiles
both clients from scratch, a few minutes for geth and roughly half an hour for
Lighthouse. That is affordable precisely because the workflow fires on release
tags only.
