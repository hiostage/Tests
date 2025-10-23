package app

import (
	"log/slog"

	"gitea.youteam.space/YouTeam/go/config"
	"gitea.youteam.space/YouTeam/go/internal/server"
	"gitea.youteam.space/YouTeam/go/pkg/db/postgres"
	"gitea.youteam.space/YouTeam/go/pkg/db/redis"
)

// Сущность всего приложения, тут содержаться все внешние сервисы: БД, Redis, брокер, HTTP, gRPC и т.п.
type App struct {
	conf   *config.Config
	log    *slog.Logger
	server *server.HttpServer
	db     *postgres.PostgresDB
	redis  *redis.Redis
}

type AppDeps struct {
	*config.Config
	*slog.Logger
}

// При создании устанавливает соединение с всеми нужными сущностями
func New(deps *AppDeps) *App {
	db, err := postgres.New(deps.StoragePath, deps.Logger)
	if err != nil {
		panic(err)
	}

	redis, err := redis.New(deps.Logger, deps.Redis.Address, deps.Redis.Port, deps.Redis.Password, deps.Redis.TTLKeys, deps.Redis.NumberDB)
	if err != nil {
		panic(err)
	}

	// Создание основного ядра приложения
	httpServer := server.New(&server.HttpServerDeps{
		HTTPServer: &deps.HTTPServer,
		Logger:     deps.Logger,
		PostgresDB: db,
		Redis:      redis,
	})

	return &App{
		conf:   deps.Config,
		log:    deps.Logger,
		server: httpServer,
		db:     db,
		redis:  redis,
	}
}

// При запуске, запускается не само приложение, а конкретно http-сервер. Это инкапусуляция
func (a *App) MustStart() {
	a.log.Debug("app: started")

	a.log.Info("app: successfully started", "port", a.conf.HTTPServer.Port)
	if err := a.server.Start(); err != nil {
		panic(err)
	}
}

// При остановке, начинается закрытие соединений с всеми сущностями
func (a *App) Stop() error {
	a.log.Debug("app: stop started")

	if err := a.server.Stop(); err != nil {
		a.log.Error("failed to stop HTTP server")
		return err
	}

	if err := a.db.Close(); err != nil {
		a.log.Error("failed to close the database connection")
		return err
	}

	if err := a.redis.Close(); err != nil {
		a.log.Error("failed to close redis connection")
		return err
	}

	a.redis = nil
	a.server = nil
	a.log.Info("app: stop successful")

	return nil
}
