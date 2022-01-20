FROM golang:1.16.7-alpine3.14 as builder

ARG TAG="v1.10.15"

RUN apk add --no-cache gcc musl-dev linux-headers git

RUN git clone https://github.com/ethereum/go-ethereum.git

WORKDIR /go/go-ethereum
RUN git checkout $TAG
RUN go run build/ci.go install ./cmd/geth


FROM alpine:3.14.1

RUN apk add --no-cache ca-certificates

RUN addgroup ethereum -g 1000 && adduser -D -u 1000 ethereum -G ethereum

COPY --from=builder /go/go-ethereum/build/bin/geth /usr/local/bin/

USER ethereum
ENTRYPOINT ["geth"]
