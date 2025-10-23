FROM --platform=linux/amd64 golang:1.24-alpine AS builder

WORKDIR /app
COPY go.mod ./
COPY go.sum ./
COPY migrations ./
RUN go mod download

COPY . .

RUN go build -o main ./cmd/main.go
RUN go build -o migrator ./cmd/migrator/migrator.go

FROM alpine:latest
WORKDIR /app

COPY --from=builder /app/main .
COPY --from=builder /app/migrator .
COPY --from=builder /app/configForDocker.yaml .
COPY --from=builder /app/migrations ./migrations

EXPOSE 8010

CMD ["sh", "-c", "sleep 3 && ./migrator -mode up --storage-path postgres://evans:evans@postgres:8012/postgres?sslmode=disable --migrations-path ./migrations && ./main -config ./configForDocker.yaml"]

# CMD ["./main", "-config", "./configDev.yaml"]