package main

import (
	"errors"
	"flag"
	"log"

	"github.com/golang-migrate/migrate/v4"
	_ "github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
)

func main() {
	var mode string
	var pathDB string
	var fileMigrationPath string

	flag.StringVar(&mode, "mode", "", "migrate mode up or down")
	flag.StringVar(&pathDB, "storage-path", "", "table creation path")
	flag.StringVar(&fileMigrationPath, "migrations-path", "", "path to migration file")
	flag.Parse()

	if mode == "" || pathDB == "" || fileMigrationPath == "" {
		panic("the path of the file with migrations or mode migration or the path for database creation is not specified")
	}

	migrateDb, err := migrate.New("file://"+fileMigrationPath, pathDB)
	if err != nil {
		panic(err)
	}

	switch mode {
	case "up":
		if err := migrateDb.Up(); err != nil {
			if errors.Is(err, migrate.ErrNoChange) {
				log.Println("no migrations to apply")
				return
			}
			panic(err)
		}
	case "down":
		if err := migrateDb.Down(); err != nil {
			if errors.Is(err, migrate.ErrNoChange) {
				log.Println("no migrations to apply")
				return
			}
			panic(err)
		}
	default:
		panic("incorrect migration mode")

	}

	log.Println("migrations have been successfully applied")
}
