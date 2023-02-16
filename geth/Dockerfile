FROM golang:1.20-alpine3.17 as builder

RUN apk add --no-cache gcc musl-dev linux-headers git

RUN git clone https://github.com/ethereum/go-ethereum.git

WORKDIR /go/go-ethereum

ARG TAG="v1.11.1"
RUN git fetch && git checkout $TAG
RUN go run build/ci.go install ./cmd/geth


FROM alpine:3.17.2 as runner

RUN apk add --no-cache ca-certificates

RUN addgroup ethereum -g 1000 && adduser -D -u 1000 ethereum -G ethereum

USER ethereum
ENTRYPOINT ["geth"]

COPY --from=builder /go/go-ethereum/build/bin/geth /usr/local/bin/
