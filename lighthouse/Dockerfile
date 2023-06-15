FROM rust:1.68.2-bullseye AS builder

ARG PORTABLE
ENV PORTABLE $PORTABLE

RUN git clone https://github.com/sigp/lighthouse src
WORKDIR /src

RUN apt-get update && apt-get install -y cmake libclang-dev protobuf-compiler

ARG TAG="v4.2.0"
RUN git fetch && git checkout $TAG
RUN make


FROM debian:bullseye-20230411-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
	libssl-dev \
	ca-certificates \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1000 lighthouse && adduser --system -uid 1000 lighthouse --gid 1000
USER lighthouse

COPY --from=builder /usr/local/cargo/bin/lighthouse /usr/local/bin/lighthouse

ENTRYPOINT ["lighthouse"]
