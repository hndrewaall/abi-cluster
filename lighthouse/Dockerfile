FROM rust:1.80.0-bullseye AS builder

ARG PORTABLE
ARG PROFILE=release

ENV PORTABLE $PORTABLE
ENV PROFILE $PROFILE

RUN git clone https://github.com/sigp/lighthouse src
WORKDIR /src

RUN apt-get update && apt-get install -y cmake libclang-dev

ARG TAG="v6.0.1"
RUN git fetch && git checkout $TAG
RUN make


FROM debian:bullseye-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
	libssl-dev \
	ca-certificates \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1000 lighthouse && adduser --system -uid 1000 lighthouse --gid 1000
USER lighthouse

COPY --from=builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse

ENTRYPOINT ["lighthouse"]
