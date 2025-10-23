package redis

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/redis/go-redis/v9"
)

type Redis struct {
	Client   *redis.Client
	log      *slog.Logger
	TTLKeys  time.Duration
	numberDb int
}

func New(log *slog.Logger, host, port, password string, ttlKeys time.Duration, numberDb int) (*Redis, error) {
	log.Debug("Redis: connection to Redis started")

	client := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%s", host, port),
		Password: password,
		DB:       numberDb,
	})

	if _, err := client.Ping(context.TODO()).Result(); err != nil {
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}

	log.Info("Redis: connect to Redis successfully")
	return &Redis{Client: client, TTLKeys: ttlKeys, log: log, numberDb: numberDb}, nil
}

func (r *Redis) Close() error {
	r.log.Debug("Redis: stop started")

	if r.Client == nil {
		return errors.New("redis connection is already closed")
	}

	if err := r.Client.Close(); err != nil {
		return fmt.Errorf("failed to close Redis connection: %w", err)
	}

	r.Client = nil

	r.log.Info("Redis: stop successful")
	return nil
}
