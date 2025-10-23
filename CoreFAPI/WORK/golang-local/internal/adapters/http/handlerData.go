/*
Это входная точка для других сервисов, которые хотят забрать данные через HTTP от этого сервиса
*/
package httpAdapter

import (
	"net/http"

	"gitea.youteam.space/YouTeam/go/internal/usecase"
)

type HandlerData struct {
	baseH  *BaseHandler
	userUC usecase.IUserUseCase
}

type HandlerDataDeps struct {
	*BaseHandler
	usecase.IUserUseCase
}

func NewHandlerData(deps *HandlerDataDeps) *HandlerData {
	return &HandlerData{
		baseH:  deps.BaseHandler,
		userUC: deps.IUserUseCase,
	}
}

// @Summary Get user info
// @Description Searches for a user by id and returns it
// @Tags data
// @Produce json
// @Param uuid path string true "User UUID" Format(uuid) Example(123e4567-e89b-12d3-a456-426614174000)
// @Success 200 {object} entity.User
// @Failure 400 {object} httpAdapter.BaseHandlerResponce "Uuid is required"
// @Failure 400 {object} httpAdapter.BaseHandlerResponce "Incorrect uuid format"
// @Failure 404 {object} httpAdapter.BaseHandlerResponce "User not found"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Router /data/u/{uuid} [get]
func (h *HandlerData) User() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {

		// Вытаскиваем id пользователя из url
		userID, ok := h.baseH.CheckUUID(w, r)
		if !ok {
			// если была ошибка, то она уже записана в ответ
			return
		}

		resp, err := h.userUC.User(r.Context(), userID)
		if err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		h.baseH.SendJsonResp(w, 200, resp)
	}
}
