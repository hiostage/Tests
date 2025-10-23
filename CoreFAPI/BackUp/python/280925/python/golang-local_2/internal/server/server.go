package server

import (
	"context"
	"log/slog"
	"net/http"
	"time"

	"gitea.youteam.space/YouTeam/go/config"
	httpAdapter "gitea.youteam.space/YouTeam/go/internal/adapters/http"
	"gitea.youteam.space/YouTeam/go/internal/adapters/http/httpMiddleware"
	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/sessionsRepo"
	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/userRepo"
	"gitea.youteam.space/YouTeam/go/internal/usecase"
	"gitea.youteam.space/YouTeam/go/pkg/db/postgres"
	"gitea.youteam.space/YouTeam/go/pkg/db/redis"
	"gitea.youteam.space/YouTeam/go/pkg/middleware"
)

const (
	gracefulShutdownTimer = time.Second * 10
)

type HttpServer struct {
	conf   *config.HTTPServer
	log    *slog.Logger
	server *http.Server
}

type HttpServerDeps struct {
	*config.HTTPServer
	*slog.Logger
	*postgres.PostgresDB
	*redis.Redis
}

// Место сборки http-сервера и всего, с чем он работает
func New(deps *HttpServerDeps) *HttpServer {
	router := http.NewServeMux()

	// Initialize repository
	userRepo := userRepo.NewPostgresUserRepo(&userRepo.PostgresUserRepoDeps{
		Logger:     deps.Logger,
		PostgresDB: deps.PostgresDB,
	})

	sessionRepo := sessionsRepo.NewSessionsRepo(&sessionsRepo.SessionsRepoDeps{
		Logger: deps.Logger,
		Redis:  deps.Redis,
	})

	// Initialize use case
	authUC := usecase.NewAuthUseCase(&usecase.AuthUseCaseDeps{
		Logger:          deps.Logger,
		IUserRepository: userRepo,
		ISessionsRepo:   sessionRepo,
	})

	userUC := usecase.NewUserUseCase(&usecase.UserUseCaseDeps{
		Logger:          deps.Logger,
		IUserRepository: userRepo,
	})

	// Initialize handler
	baseHandler := httpAdapter.NewBaseHandler(&httpAdapter.BaseHandlerDeps{
		Logger: deps.Logger,
	})

	authHandler := httpAdapter.NewHandlerAuth(&httpAdapter.HandlerAuthDeps{
		BaseHandler:  baseHandler,
		IAuthUseCase: authUC,
	})

	userHandler := httpAdapter.NewHandlerUser(&httpAdapter.HandlerUserDeps{
		BaseHandler:  baseHandler,
		IUserUseCase: userUC,
		IAuthUseCase: authUC,
	})

	dataHandler := httpAdapter.NewHandlerData(&httpAdapter.HandlerDataDeps{
		BaseHandler:  baseHandler,
		IUserUseCase: userUC,
	})

	// Initialize middlewares
	loggingMiddleware := httpMiddleware.NewMiddlewareLogging(&httpMiddleware.MiddlewareLoggingDeps{
		Logger: deps.Logger,
	})

	authMiddleware := httpMiddleware.NewMiddlewareAuth(&httpMiddleware.MiddlewareAuthDeps{
		BaseHandler:   baseHandler,
		ISessionsRepo: sessionRepo,
	})

	// Initialize Routers
	activeHandlers := &ActiveHandlers{
		HandlerAuth: authHandler,
		HandlerUser: userHandler,
		HandlerData: dataHandler,
	}

	activeMiddlewares := &ActiveMiddlewares{
		MiddlewareAuth: authMiddleware,
	}

	InitRouters(router, activeHandlers, activeMiddlewares)

	server := &http.Server{
		Addr: deps.Address + ":" + deps.Port,
		Handler: middleware.ChainMiddleware(
			middleware.Timeout(deps.WriteTimeout),
			middleware.CORS(deps.AllowedDomainsCORS),
			loggingMiddleware.HandlersLog(),
		)(router),
		ReadHeaderTimeout: deps.ReadHeaderTimeout,
		ReadTimeout:       deps.ReadTimeout,
		WriteTimeout:      deps.WriteTimeout,
		IdleTimeout:       deps.IdleTimeout,
	}

	return &HttpServer{
		conf:   deps.HTTPServer,
		log:    deps.Logger,
		server: server,
	}
}

func (s *HttpServer) Start() error {
	log := s.log.With(slog.String("Address", s.server.Addr))

	log.Info("HTTP server: successfully started")
	if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		return err
	}

	return nil
}

func (s *HttpServer) Stop() error {
	s.log.Debug("HTTP server: stop started")

	ctx, cancel := context.WithTimeout(context.Background(), gracefulShutdownTimer)
	defer cancel()

	if err := s.server.Shutdown(ctx); err != nil {
		s.log.Error("Server shutdown failed", "error", err)
		return err
	}

	s.server = nil
	s.log.Info("HTTP server: stop successful")

	return nil
}
