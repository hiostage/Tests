package httpMiddleware

import (
	"context"
	"errors"
	"log/slog"
	"net/http"

	httpAdapter "gitea.youteam.space/YouTeam/go/internal/adapters/http"
	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/sessionsRepo"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
)

type MiddlewareAuth struct {
	baseH     *httpAdapter.BaseHandler
	sessionDB sessionsRepo.ISessionsRepo
}

type MiddlewareAuthDeps struct {
	*httpAdapter.BaseHandler
	sessionsRepo.ISessionsRepo
}

func NewMiddlewareAuth(deps *MiddlewareAuthDeps) *MiddlewareAuth {
	return &MiddlewareAuth{
		baseH:     deps.BaseHandler,
		sessionDB: deps.ISessionsRepo,
	}
}

func (m *MiddlewareAuth) Session() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			op := "MiddlewareAuth: authorisation"
			log := m.baseH.Log.With(slog.String("operation", op))

			cookie, err := r.Cookie("sessionId")
			if err != nil {
				if errors.Is(err, http.ErrNoCookie) {
					log.Warn("failed to retrieve the required key from the cookie")
					m.baseH.HandleError(w, myErr.ErrSessionNotFound)
					return
				}
				log.Warn("failed to retrieve a cookie from the request")
				m.baseH.HandleError(w, myErr.ErrSessionNotFound)
				return
			}

			// TODO: переделать проверка некорректная
			// Проверка времени жизни куки
			// if ok := cookie.Expires.Before(time.Now()); !ok {

			// }

			sessionID := cookie.Value
			if sessionID == "" {
				log.Warn("Invalid session ID", "sessionID", sessionID)
				m.baseH.HandleError(w, myErr.ErrSessionNotFound)
				return
			}

			// Извлекаем сессию из Redis
			payload, err := m.sessionDB.GetSession(r.Context(), sessionID)
			if err != nil {
				if errors.Is(err, myErr.ErrSessionNotFound) {
					log.Warn("session not found")
					m.baseH.HandleError(w, err)
					return
				}
				log.Error("failed to get a session", "error", err)
				m.baseH.HandleError(w, err)
				return
			}

			ctx := r.Context()
			// Тут можно передать sessionID, так как sessionID == payload.UserUUID
			ctx = context.WithValue(ctx, httpAdapter.SessionIdAndUserId, payload.UserUUID)

			r = r.WithContext(ctx)

			log.Info("authorisation successful")
			next.ServeHTTP(w, r)
		})
	}
}
