package postgres

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"github.com/jackc/pgx/v5/pgxpool"
)

type PostgresDB struct {
	DB  *pgxpool.Pool
	log *slog.Logger
}

func New(storagePath string, log *slog.Logger) (*PostgresDB, error) {
	log.Debug("database: connection to Postgres started")

	DB, err := pgxpool.New(context.Background(), storagePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	if err := DB.Ping(context.Background()); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	log.Info("database: connect to Postgres successfully")
	return &PostgresDB{DB: DB, log: log}, nil
}

func (s *PostgresDB) Close() error {
	s.log.Debug("database: stop started")

	if s.DB == nil {
		return errors.New("database connection is already closed")
	}

	s.DB.Close()

	s.DB = nil

	s.log.Info("database: stop successful")
	return nil
}
