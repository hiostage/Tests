package httpAdapter

import (
	"io"
	"net/http"

	"gitea.youteam.space/YouTeam/go/internal/adapters/http/cookie"
	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/internal/usecase"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
	"gitea.youteam.space/YouTeam/go/pkg/utils"
)

// Обработчик, отвечающий за действия с пользователем
// использование -> создается в server.go, а конкретные методы привязываются к url-путям в initRouters.go
type HandlerUser struct {
	baseH  *BaseHandler
	userUC usecase.IUserUseCase
	authUC usecase.IAuthUseCase
}

type HandlerUserDeps struct {
	*BaseHandler
	usecase.IUserUseCase
	usecase.IAuthUseCase
}

func NewHandlerUser(deps *HandlerUserDeps) *HandlerUser {
	return &HandlerUser{
		baseH:  deps.BaseHandler,
		userUC: deps.IUserUseCase,
		authUC: deps.IAuthUseCase,
	}
}

// @Summary Get user info
// @Description Searches for a user by id (pulls it from the session load) and returns it
// @Tags user
// @Produce json
// @Success 200 {object} entity.User
// @Failure 401 {object} httpAdapter.BaseHandlerResponce "Unauthorized"
// @Failure 404 {object} httpAdapter.BaseHandlerResponce "User not found"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Security SessionAuth
// @Router /user [get]
func (h *HandlerUser) User() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get user id from context, AuthMiddleware put it there earlier
		userID, ok := r.Context().Value(SessionIdAndUserId).(string)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrNoUserID)
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

// @Summary Update user info
// @Description Searches for a user by id (pulls it from the session load) and updates it
// @Tags user
// @Accept json
// @Param data body dto.UpdateRequest true "ALL user data"
// @Success 204
// @Failure 400 {object} httpAdapter.BaseHandlerResponce "Bad request"
// @Failure 401 {object} httpAdapter.BaseHandlerResponce "Unauthorized"
// @Failure 404 {object} httpAdapter.BaseHandlerResponce "User not found"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Security SessionAuth
// @Router /user [put]
func (h *HandlerUser) UserUpd() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get user id from context, AuthMiddleware put it there earlier
		userID, ok := r.Context().Value(SessionIdAndUserId).(string)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrNoUserID)
			return
		}

		data, err := h.baseH.Handle(w, r, func(body io.Reader) (any, error) {
			return utils.DecodeBody[dto.UpdateRequest](r.Body)
		})
		if err != nil {
			// the error in the response has already been written to h.baseH.Handle
			return
		}

		// Matching data to the correct type
		updData, ok := data.(*dto.UpdateRequest)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrTypeConversion)
			return
		}

		// Executing business logic
		if err := h.userUC.UserUpd(r.Context(), userID, updData); err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// There's no JSON in the response, just the code to send it
		w.WriteHeader(204)
	}
}

// @Summary Delete user
// @Description Searches for a user by id (takes it from the session load) and deletes it and its session
// @Tags user
// @Success 204
// @Failure 401 {object} httpAdapter.BaseHandlerResponce "Unauthorized"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Security SessionAuth
// @Router /user [delete]
func (h *HandlerUser) UserDel() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get  id from context, AuthMiddleware put it there earlier
		sessionIdAndUserId, ok := r.Context().Value(SessionIdAndUserId).(string)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrNoSessionID)
			return
		}

		// Executing business logic
		if err := h.userUC.UserDel(r.Context(), sessionIdAndUserId); err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// Delete session
		if err := h.authUC.SessionDel(r.Context(), sessionIdAndUserId); err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// Clearing cookies on the client side
		cookieManager := &cookie.CookieManager{}
		cookieManager.DeleteCookie(w, string(SessionIdAndUserId))
		h.baseH.Log.Info("user session successfully closed")

		// There's no JSON in the response, just the code to send it
		w.WriteHeader(204)
	}
}
