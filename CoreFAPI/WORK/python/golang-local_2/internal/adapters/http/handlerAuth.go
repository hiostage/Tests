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

// Обработчик, выполняющий операции регистрации и логина
// использование -> создается в server.go, а конкретные методы привязываются к url-путям в initRouters.go
type HandlerAuth struct {
	baseH  *BaseHandler
	authUC usecase.IAuthUseCase
}

type HandlerAuthDeps struct {
	*BaseHandler
	usecase.IAuthUseCase
}

func NewHandlerAuth(deps *HandlerAuthDeps) *HandlerAuth {
	return &HandlerAuth{
		baseH:  deps.BaseHandler,
		authUC: deps.IAuthUseCase,
	}
}

// @Summary Registration
// @Description Register new user with provided data. All fields are required except "phone"
// @Tags auth
// @Accept json
// @Produce json
// @Param data body dto.RegisterRequest true "Register user request body"
// @Success 201 {object} dto.RegisterResponce
// @Failure 400 {object} httpAdapter.BaseHandlerResponce "Bad request"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Router /register [post]
func (h *HandlerAuth) Register() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get the query body and the required data model from dto and check that the body contains all the required fields
		data, err := h.baseH.Handle(w, r, func(body io.Reader) (any, error) {
			return utils.DecodeBody[dto.RegisterRequest](r.Body)
		})
		if err != nil {
			// the error in the response has already been written to h.baseH.Handle
			return
		}

		// Matching data to the correct type
		registerData, ok := data.(*dto.RegisterRequest)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrTypeConversion)
			return
		}

		// Executing business logic
		resp, err := h.authUC.Register(r.Context(), registerData)
		if err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// Login on registration
		loginResp, err := h.authUC.Login(r.Context(), &dto.LoginRequest{
			Email:    registerData.Email,
			Password: registerData.Password,
		})
		if err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		cookieManager := &cookie.CookieManager{}
		cookieManager.SetCookie(w, &cookie.CookieData{
			Name:     string(SessionIdAndUserId),
			Value:    loginResp.SessionID,
			Path:     "/",
			HttpOnly: true,
			Secure:   false,
			MaxAge:   300, // TODO: переделать, согласовать с сроком жизни записи в Redis
		})

		h.baseH.SendJsonResp(w, 201, resp)
	}
}

// @Summary Login
// @Description User login, user search by mail, user session creation, session data embedded in cookies
// @Tags auth
// @Accept json
// @Produce json
// @Param data body dto.LoginRequest true "Login user request body"
// @Success 200 {object} dto.RegisterResponce
// @Failure 400 {object} httpAdapter.BaseHandlerResponce "Bad request"
// @Failure 404 {object} httpAdapter.BaseHandlerResponce "User not found"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Router /login [post]
func (h *HandlerAuth) Login() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get the query body and the required data model from dto and check that the body contains all the required fields
		data, err := h.baseH.Handle(w, r, func(body io.Reader) (any, error) {
			return utils.DecodeBody[dto.LoginRequest](r.Body)
		})
		if err != nil {
			// the error in the response has already been written to h.baseH.Handle
			return
		}

		// Matching data to the correct type
		loginData, ok := data.(*dto.LoginRequest)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrTypeConversion)
			return
		}

		// Executing business logic
		resp, err := h.authUC.Login(r.Context(), loginData)
		if err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// Cookie settings
		cookieManager := &cookie.CookieManager{}
		cookieManager.SetCookie(w, &cookie.CookieData{
			Name:     string(SessionIdAndUserId),
			Value:    resp.SessionID,
			Path:     "/",
			HttpOnly: true,
			Secure:   false,
			MaxAge:   300, // TODO: переделать, согласовать с сроком жизни записи в Redis
		})

		h.baseH.SendJsonResp(w, 200, resp)
	}
}

// @Summary Logout
// @Description User logout and session deletion
// @Tags auth
// @Success 204
// @Failure 401 {object} httpAdapter.BaseHandlerResponce "Unauthorized"
// @Failure 500 {object} httpAdapter.BaseHandlerResponce "Internal server error"
// @Failure 504 {object} httpAdapter.BaseHandlerResponce "Gateway timeout"
// @Security SessionAuth
// @Router /logout [post]
func (h *HandlerAuth) Logout() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Get session id from context, AuthMiddleware put it there earlier
		sessionID, ok := r.Context().Value(SessionIdAndUserId).(string)
		if !ok {
			h.baseH.HandleError(w, myErr.ErrNoSessionID)
			return
		}

		// Delete session
		if err := h.authUC.SessionDel(r.Context(), sessionID); err != nil {
			h.baseH.HandleError(w, err)
			return
		}

		// Clearing cookies on the client side
		cookieManager := &cookie.CookieManager{}
		cookieManager.DeleteCookie(w, string(SessionIdAndUserId))
		h.baseH.Log.Debug("user session successfully closed")

		// There's no JSON in the response, just the code to send it
		w.WriteHeader(204)
	}
}
