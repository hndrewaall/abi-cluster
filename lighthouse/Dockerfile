FROM rust:1.58.0-bullseye AS builder

ARG TAG="v2.1.0"
ARG PORTABLE
ENV PORTABLE $PORTABLE

RUN git clone https://github.com/sigp/lighthouse src
WORKDIR /src

RUN apt-get update && apt-get install -y cmake libclang-dev

RUN git fetch && git checkout $TAG
RUN make


FROM debian:bullseye-20211220-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
	libssl-dev \
	ca-certificates \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse

RUN addgroup --system --gid 1000 lighthouse && adduser --system -uid 1000 lighthouse --gid 1000
USER lighthouse

ENTRYPOINT ["lighthouse"]
