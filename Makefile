.PHONY: build run test clean vet fmt

APP_NAME = porter

build:
	go build -o bin/$(APP_NAME) ./cmd/porter

run: build
	./bin/$(APP_NAME)

test:
	go test -v ./...

clean:
	rm -rf bin/

vet:
	go vet ./...

fmt:
	go fmt ./...
