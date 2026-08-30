# Local image builds. PUBLISHING IS CI'S JOB, NOT THIS FILE'S.
#
# These targets used to end in `docker buildx build --push -t <registry>/geth`,
# which published an untagged (i.e. `:latest`) image straight from a developer
# machine. Two things were wrong with that and both are now fixed elsewhere:
# the registry accepts writes only from CI, so the push simply fails; and
# `:latest` is a mutable pointer, which is the wrong shape for something a
# mainnet validator pulls. Releases are semver tags built by CI — see README.md.
#
# What is left here is what it says: a LOCAL build, tagged `:local`, for trying
# a Dockerfile change before it goes near a release.

REGISTRY ?= docker.gbre.org

.PHONY: images geth-image lighthouse-image release

images: geth-image lighthouse-image

geth-image:
	docker build -t $(REGISTRY)/geth:local geth

lighthouse-image:
	docker build -t $(REGISTRY)/lighthouse:local lighthouse

# Cut a release: tag the current commit and push the tag, which is the only
# thing that triggers a CI build+publish. Everything else about the release is
# gated in CI (bare semver, tag must be on main, tag must not already exist in
# the registry), so this target stays deliberately thin — it does not try to
# re-implement those checks and then disagree with them.
#
#   make release VERSION=v1.0.1
release:
	@test -n "$(VERSION)" || { echo "usage: make release VERSION=vX.Y.Z" >&2; exit 2; }
	@printf '%s' "$(VERSION)" | grep -Eq '^v[0-9]+\.[0-9]+\.[0-9]+$$' \
		|| { echo "VERSION must be vMAJOR.MINOR.PATCH, got '$(VERSION)'" >&2; exit 2; }
	@grep -q "$(REGISTRY)/geth:$(VERSION)" docker-compose.yml \
		|| { echo "docker-compose.yml does not pin geth:$(VERSION) — bump it first" >&2; exit 2; }
	@grep -q "$(REGISTRY)/lighthouse:$(VERSION)" docker-compose.yml \
		|| { echo "docker-compose.yml does not pin lighthouse:$(VERSION) — bump it first" >&2; exit 2; }
	git tag -a "$(VERSION)" -m "abi-cluster $(VERSION)"
	git push origin "$(VERSION)"
	@echo "pushed $(VERSION) — CI builds and publishes; you get a push notification"
