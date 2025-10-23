package server

import (
	"net/http"

	_ "gitea.youteam.space/YouTeam/go/docs"
	httpAdapter "gitea.youteam.space/YouTeam/go/internal/adapters/http"
	"gitea.youteam.space/YouTeam/go/internal/adapters/http/httpMiddleware"
	"gitea.youteam.space/YouTeam/go/pkg/middleware"
	httpSwagger "github.com/swaggo/http-swagger"
)

// Группировка используемых обработчиков
type ActiveHandlers struct {
	*httpAdapter.HandlerAuth
	*httpAdapter.HandlerUser
	*httpAdapter.HandlerData
}

// Группировка используемых промежуточных обработчиков
type ActiveMiddlewares struct {
	*httpMiddleware.MiddlewareAuth
}

func InitRouters(router *http.ServeMux, handlers *ActiveHandlers, middlewares *ActiveMiddlewares) {
	// Auth
	router.Handle("POST /register", handlers.HandlerAuth.Register())

	router.Handle("POST /login", handlers.HandlerAuth.Login())

	router.Handle("POST /logout", middleware.ChainMiddleware(
		middlewares.MiddlewareAuth.Session(), // защищенная ручка
	)(handlers.HandlerAuth.Logout()))

	// Users
	router.Handle("GET /user", middleware.ChainMiddleware(
		middlewares.MiddlewareAuth.Session(), // защищенная ручка
	)(handlers.HandlerUser.User()))

	router.Handle("PUT /user", middleware.ChainMiddleware(
		middlewares.MiddlewareAuth.Session(), // защищенная ручка
	)(handlers.HandlerUser.UserUpd()))

	router.Handle("DELETE /user", middleware.ChainMiddleware(
		middlewares.MiddlewareAuth.Session(), // защищенная ручка
	)(handlers.HandlerUser.UserDel()))

	// Data
	router.Handle("GET /data/u/{uuid}", handlers.HandlerData.User())

	// Swagger
	router.HandleFunc("/swagger/", httpSwagger.WrapHandler)
}
