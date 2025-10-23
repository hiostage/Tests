package httpAdapter

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net/http"

	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
	"gitea.youteam.space/YouTeam/go/pkg/utils"
	"gitea.youteam.space/YouTeam/go/pkg/validate"
)

// Это общие ключи в констексте http-запросов, которые могут быть получены в любом месте
type contextKey string

const (
	SessionIdAndUserId contextKey = "sessionId" // конкретно этот вшивается в куки
)

// Универсальная структура для отправки ответов
type BaseHandlerResponce struct {
	Message string `json:"message"`
	Error   string `json:"error"`
	Status  int    `json:"status"`
}

// Общий обработчик для всех остальных обработчиков
// нужен, чтобы убрать дублирование кода, как единое место для отправки ответов http и обработки ошибок
// использование -> встраивается в любой обработчик и он получает логгер и возможности валидации, чтения тела запроса, отправки ошибок
type BaseHandler struct {
	Log *slog.Logger
}

type BaseHandlerDeps struct {
	*slog.Logger
}

func NewBaseHandler(deps *BaseHandlerDeps) *BaseHandler {
	return &BaseHandler{Log: deps.Logger}
}

// Записывает в ответ данные и ставит код ответа
func (h *BaseHandler) SendJsonResp(w http.ResponseWriter, status int, data any) {
	jsonResponse, err := json.Marshal(data)
	if err != nil {
		h.Log.Error("failed to marshal JSON", "error", err)
		w.WriteHeader(http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if _, err := w.Write(jsonResponse); err != nil {
		h.Log.Error("!!ATTENTION!! failed to write JSON response", "error", err)
	}
}

func (h *BaseHandler) CheckUUID(w http.ResponseWriter, r *http.Request) (string, bool) {

	uuid := r.PathValue("uuid")

	if uuid == "" {
		h.Log.Warn("no uuid in url")
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "failed to process request due to uuid",
			Error:   myErr.ErrNotUuid.Error(),
		})
		return "", false
	}

	if isUuid := utils.IsUUID(uuid); !isUuid {
		h.Log.Warn("incorrect uuid format in url")
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "failed to process request due to uuid",
			Error:   myErr.ErrIncorrectUuid.Error(),
		})
		return "", false
	}

	return uuid, true
}

// Общая, базовая ручка, занимается чтением тела запроса и его валидацией
func (h *BaseHandler) Handle(w http.ResponseWriter, r *http.Request, decodeFunc func(io.Reader) (any, error)) (any, error) {
	op := "BaseHandler: Handle func"
	log := h.Log.With(slog.String("operation", op))

	// Decoding the request body
	data, err := decodeFunc(r.Body)
	if err != nil {
		log.Warn("failed to decode request body", "error", err)
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "failed to decode request body",
			Error:   err.Error(),
		})
		return nil, err
	}

	// Data validation
	if err := validate.IsValid(data); err != nil {
		log.Warn("request body data failed validation", "error", err)
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "request body data failed validation",
			Error:   err.Error(),
		})
		return nil, err
	}

	log.Debug("data successfully validated", "data", data)
	return data, nil
}

// Общая функция для отправки ошибок, тут собраны ВСЕ ошибки из ВСЕХ МЕСТ
// Если нужно, чтобы в http-ответе была конкретика, вы можете добавить сюда нужную вам ошибку
func (h *BaseHandler) HandleError(w http.ResponseWriter, err error) {
	op := "BaseHandler: HandleError func"
	log := h.Log.With(slog.String("operation", op))

	switch {
	case errors.Is(err, myErr.ErrUserAlreadyExists):
		log.Warn("user already exists", "error", err)
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "user already exists",
			Error:   err.Error(),
		})
	case errors.Is(err, myErr.ErrInvalidPassword):
		log.Warn("invalid password", "error", err)
		h.SendJsonResp(w, 400, &BaseHandlerResponce{
			Status:  http.StatusBadRequest,
			Message: "invalid password",
			Error:   err.Error(),
		})
	case errors.Is(err, myErr.ErrSessionExpired):
		log.Warn("session (cookies) expired", "error", err)
		h.SendJsonResp(w, 401, &BaseHandlerResponce{
			Status:  http.StatusUnauthorized,
			Message: "session (cookies) expired",
			Error:   err.Error(),
		})
	case errors.Is(err, myErr.ErrSessionNotFound):
		log.Warn("Unauthorized / no session", "error", err)
		h.SendJsonResp(w, 401, &BaseHandlerResponce{
			Status:  http.StatusUnauthorized,
			Message: "Unauthorized / no session",
			Error:   err.Error(),
		})
	case errors.Is(err, myErr.ErrUserNotFound):
		log.Warn("failed get user", "error", err)
		h.SendJsonResp(w, 404, &BaseHandlerResponce{
			Status:  http.StatusNotFound,
			Message: "failed get user",
			Error:   err.Error(),
		})
	case errors.Is(err, context.DeadlineExceeded):
		log.Error("request processing exceeded the allowed time limit", "error", err)
		h.SendJsonResp(w, 504, &BaseHandlerResponce{
			Status:  http.StatusGatewayTimeout,
			Message: "request processing exceeded the allowed time limit",
			Error:   err.Error(),
		})
	default:
		log.Error("internal server error", "error", err)
		h.SendJsonResp(w, 500, &BaseHandlerResponce{
			Status:  http.StatusInternalServerError,
			Message: "internal server error",
			Error:   err.Error(),
		})
	}
}
