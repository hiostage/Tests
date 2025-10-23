package usecase

import (
	"context"
	"log/slog"

	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/sessionsRepo"
	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/userRepo"
	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/internal/entity"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
	"gitea.youteam.space/YouTeam/go/pkg/utils"
)

type IAuthUseCase interface {
	Register(ctx context.Context, data *dto.RegisterRequest) (*dto.RegisterResponce, error)
	Login(ctx context.Context, data *dto.LoginRequest) (*dto.LoginResponce, error)
	Session(ctx context.Context, uuid string) (*dto.SessionPayload, error)
	SessionDel(ctx context.Context, uuid string) error
}

type AuthUseCase struct {
	log       *slog.Logger
	repo      userRepo.IUserRepository
	sessionDB sessionsRepo.ISessionsRepo
}

type AuthUseCaseDeps struct {
	*slog.Logger
	userRepo.IUserRepository
	sessionsRepo.ISessionsRepo
}

func NewAuthUseCase(deps *AuthUseCaseDeps) *AuthUseCase {
	return &AuthUseCase{log: deps.Logger, repo: deps.IUserRepository, sessionDB: deps.ISessionsRepo}
}

func (uc *AuthUseCase) Register(ctx context.Context, data *dto.RegisterRequest) (*dto.RegisterResponce, error) {
	op := "usecase auth: user registration"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("Register func call", "requets data", data)

	passwordHash, err := utils.Hashing(data.Password)
	if err != nil {
		return nil, err
	}

	newUser := entity.NewUserBuilder().
		WithFirstName(data.FirstName).
		WithLastName(data.LastName).
		WithUserName(data.Email).
		WithEmail(data.Email).
		WithPassword(passwordHash).
		WithPhone(data.Phone).
		Build()

	id, err := uc.repo.CreateUser(ctx, newUser)
	if err != nil {
		return nil, err
	}

	log.Info("successful registration")
	return &dto.RegisterResponce{UUID: id}, nil
}

func (uc *AuthUseCase) Login(ctx context.Context, data *dto.LoginRequest) (*dto.LoginResponce, error) {
	op := "usecase auth: user login"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("Login func call", "requets data", data)

	user, err := uc.repo.FindUser(ctx, &dto.UserRequest{Mode: "email", Email: data.Email})
	if err != nil {
		return nil, err
	}

	if ok := user.CheckPassword(data.Password); !ok {
		return nil, myErr.ErrInvalidPassword
	}

	session, err := uc.sessionDB.CreateSession(ctx, &dto.SessionPayload{
		UserUUID:  user.UUID,
		UserRoles: []string{"user"}, // TODO: переделать! какие будут роли?
		UserName:  user.UserName,
	})
	if err != nil {
		return nil, err
	}

	log.Info("successful authentication")
	return &dto.LoginResponce{SessionID: session}, nil
}

func (uc *AuthUseCase) Session(ctx context.Context, uuid string) (*dto.SessionPayload, error) {
	op := "usecase auth: find session"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("Session func call", "uuid", uuid)

	token, err := uc.sessionDB.GetSession(ctx, uuid)
	if err != nil {
		return nil, err
	}

	log.Info("session successfully received")
	return token, nil
}

func (uc *AuthUseCase) SessionDel(ctx context.Context, uuid string) error {
	op := "usecase auth: delete session"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("SessionDel func call", "uuid", uuid)

	if err := uc.sessionDB.DeleteSession(ctx, uuid); err != nil {
		return err
	}

	log.Info("session successfully deleted")
	return nil
}
