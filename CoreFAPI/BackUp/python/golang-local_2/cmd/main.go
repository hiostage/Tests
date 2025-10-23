package main

import (
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"gitea.youteam.space/YouTeam/go/config"
	"gitea.youteam.space/YouTeam/go/internal/app"
	"gitea.youteam.space/YouTeam/go/pkg/logs"
)

// @title           Registration and authorisation services
// @version         0.2
// @description		The service allows you to create a user, edit, delete
// @description		You can log in and log out and sessions will be created and deleted

// @contact.name   Evans Trein
// @contact.email  evanstrein@icloud.com
// @contact.url    https://github.com/EvansTrein

// @host      localhost:8010
// @schemes   http

// @securityDefinitions.apikey SessionAuth
// @in cookie
// @name session_id

// @externalDocs.description  OpenAPI
// @externalDocs.url          https://swagger.io/resources/open-api/
func main() {
	var conf *config.Config
	var log *slog.Logger

	conf = config.MustLoad()
	log = logs.InitLog(conf.Env, conf.IsFileLogOutput)

	serverApp := app.New(&app.AppDeps{
		Config: conf,
		Logger: log,
	})

	go func() {
		serverApp.MustStart()
	}()

	done := make(chan os.Signal, 1)
	signal.Notify(done, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)

	<-done
	if err := serverApp.Stop(); err != nil {
		log.Error("an error occurred when stopping the application", "error", err)
		panic(err)
	}
}
