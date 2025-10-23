default: go-run
.PHONY: go-run

# PATH_DB=postgres://evans:evans@localhost:8012/postgres?sslmode=disable
PATH_DB=postgres://registr:registr@192.168.1.114:5432/registr?sslmode=disable
FILE_MIGRATIONS =./migrations
MIGRATION_MODE=up

# Golang
go-run:
	go run cmd/main.go -config ./configLocal.yaml

go-run-dev:
	go run cmd/main.go -config ./configDev.yaml

go-migrate:	
	go run cmd/migrator/migrator.go -mode $(MIGRATION_MODE) -storage-path $(PATH_DB) -migrations-path $(FILE_MIGRATIONS)

go-fmt:
	go fmt ./...

go-lint:
	golangci-lint run ./... -c .golangci.yml

go-memory-check:
	fieldalignment ./...

go-memory-fix:
	fieldalignment -fix ./...

go-mock:
	go generate ./...

go-cover:
	go test -cover ./...

go-swag:
	swag init -g cmd/main.go

# go-cover-html:
# 	go test -cover -coverprofile=coverage.out ./internal/users && go tool cover -html=coverage.out -o coverage.html


# cmd //c tree "%cd%" //F