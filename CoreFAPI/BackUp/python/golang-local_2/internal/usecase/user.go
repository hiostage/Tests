package usecase

import (
	"context"
	"log/slog"

	"gitea.youteam.space/YouTeam/go/internal/adapters/repository/userRepo"
	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/internal/entity"
	"gitea.youteam.space/YouTeam/go/pkg/utils"
)

type IUserUseCase interface {
	User(ctx context.Context, id string) (*entity.User, error)
	UserUpd(ctx context.Context, id string, data *dto.UpdateRequest) error
	UserDel(ctx context.Context, id string) error
}

type UserUseCase struct {
	log  *slog.Logger
	repo userRepo.IUserRepository
}

type UserUseCaseDeps struct {
	*slog.Logger
	userRepo.IUserRepository
}

func NewUserUseCase(deps *UserUseCaseDeps) *UserUseCase {
	return &UserUseCase{repo: deps.IUserRepository, log: deps.Logger}
}

func (uc *UserUseCase) User(ctx context.Context, id string) (*entity.User, error) {
	op := "usecase user: user creation"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("User func call", "id", id)

	user, err := uc.repo.FindUser(ctx, &dto.UserRequest{Mode: "id", ID: id})
	if err != nil {
		return nil, err
	}

	log.Info("user successfully created")
	return user, nil
}

func (uc *UserUseCase) UserUpd(ctx context.Context, id string, data *dto.UpdateRequest) error {
	op := "usecase user: user data update"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("UserUpd func call", "data", data)

	// When updating we get a new password, not a hash, so we turn it into a hash
	passwordHash, err := utils.Hashing(data.Password)
	if err != nil {
		return err
	}

	newUser := entity.NewUserBuilder().
		WithUUID(id).
		WithFirstName(data.FirstName).
		WithLastName(data.LastName).
		WithUserName(data.Email).
		WithEmail(data.Email).
		WithPassword(passwordHash).
		WithPhone(data.Phone).
		Build()

	if err := uc.repo.UpdateUser(ctx, newUser); err != nil {
		return err
	}

	log.Info("user successfully updated")
	return nil
}

func (uc *UserUseCase) UserDel(ctx context.Context, id string) error {
	op := "usecase user: user deletion"
	log := uc.log.With(slog.String("operation", op))
	log.Debug("UserDel func call", "id", id)

	if err := uc.repo.DeleteUser(ctx, id); err != nil {
		return err
	}

	log.Info("user successfully deleted")
	return nil
}
