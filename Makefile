.phony: lighthouse-image
lighthouse-image:
	docker buildx build --push -t docker.gbre.org/lighthouse --cache-to=type=inline --cache-from=docker.gbre.org/lighthouse lighthouse

.phony: geth-image
geth-image:
	docker buildx build --push -t docker.gbre.org/geth --cache-to=type=inline --cache-from=docker.gbre.org/geth geth
