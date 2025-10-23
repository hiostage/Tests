package userRepo

import (
	"context"
	"fmt"
	"log/slog"
	"strings"
	"sync"

	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/internal/entity"
	"gitea.youteam.space/YouTeam/go/pkg/db/postgres"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
)

const tableName = "users"

//go:generate mockgen -source=$GOFILE -destination=../mocks/mock_userRepo.go -package=mocksRepository
type IUserRepository interface {
	CreateUser(ctx context.Context, user *entity.User) (string, error)
	FindUser(ctx context.Context, param *dto.UserRequest) (*entity.User, error)
	UpdateUser(ctx context.Context, user *entity.User) error
	DeleteUser(ctx context.Context, id string) error
}

type PostgresUserRepo struct {
	log  *slog.Logger
	repo *postgres.PostgresDB
	mu   sync.Mutex
}

type PostgresUserRepoDeps struct {
	*slog.Logger
	*postgres.PostgresDB
}

func NewPostgresUserRepo(deps *PostgresUserRepoDeps) *PostgresUserRepo {
	return &PostgresUserRepo{repo: deps.PostgresDB, log: deps.Logger}
}

func (r *PostgresUserRepo) CreateUser(ctx context.Context, user *entity.User) (string, error) {
	op := "Database: create user"
	log := r.log.With(slog.String("operation", op))
	log.Debug("Create func call", "user", user)

	query := fmt.Sprintf(`
        INSERT INTO %s (first_name, last_name, user_name, email, password_hash)
        VALUES ($1, $2, $3, $4, $5) RETURNING id
        `, tableName)

	var id string
	err := r.repo.DB.QueryRow(
		ctx,
		query,
		user.FirstName,
		user.LastName,
		user.UserName,
		user.Email,
		user.PasswordHash,
	).Scan(&id)

	if err != nil {
		if strings.Contains(err.Error(), "unique") {
			log.Warn("failed to create a record in the database, mail or user_name already exists", "error", err.Error())
			return "", myErr.ErrUserAlreadyExists
		}
		log.Error("failed to create a record in the database", "error", err.Error())
		return "", err
	}

	log.Info("user successfully created", "user_id", id)
	return id, nil
}

func (r *PostgresUserRepo) FindUser(ctx context.Context, param *dto.UserRequest) (*entity.User, error) {
	op := "Database: find user"
	log := r.log.With(slog.String("operation", op))
	log.Debug("FindUser func call", "param", param)

	var user entity.User

	switch param.Mode {
	case "email":
		query := fmt.Sprintf(`
		SELECT id, first_name, last_name, user_name, email, phone, password_hash 
		FROM %s 
		WHERE email = $1
		`, tableName)

		err := r.repo.DB.QueryRow(ctx, query, param.Email).Scan(
			&user.UUID,
			&user.FirstName,
			&user.LastName,
			&user.UserName,
			&user.Email,
			&user.Phone,
			&user.PasswordHash,
		)

		if err != nil {
			if strings.Contains(err.Error(), "no rows") {
				log.Warn("user not found")
				return nil, myErr.ErrUserNotFound
			}
			log.Error("failed to execute the database user search request", "error", err)
			return nil, err
		}
	case "id":
		query := fmt.Sprintf(`
		SELECT id, first_name, last_name, user_name, email, phone, password_hash 
		FROM %s 
		WHERE id = $1
		`, tableName)

		err := r.repo.DB.QueryRow(ctx, query, param.ID).Scan(
			&user.UUID,
			&user.FirstName,
			&user.LastName,
			&user.UserName,
			&user.Email,
			&user.Phone,
			&user.PasswordHash,
		)

		if err != nil {
			if strings.Contains(err.Error(), "no rows") {
				log.Warn("user not found")
				return nil, myErr.ErrUserNotFound
			}
			log.Error("failed to execute the database user search request", "error", err)
			return nil, err
		}
	default:
		log.Error("incorrect user search mode")
		return nil, myErr.ErrModeSearch
	}

	log.Info("user successfully found")
	return &user, nil
}

func (r *PostgresUserRepo) UpdateUser(ctx context.Context, user *entity.User) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	op := "Database: update user"
	log := r.log.With(slog.String("operation", op))
	log.Debug("UpdateUser func call", "user", user)

	query := fmt.Sprintf(`
		UPDATE %s 
		SET first_name = $1, last_name = $2, user_name = $3, email = $4, phone = $5, password_hash = $6
		WHERE id = $7
		`, tableName)

	result, err := r.repo.DB.Exec(
		ctx,
		query,
		user.FirstName,
		user.LastName,
		user.UserName,
		user.Email,
		user.Phone,
		user.PasswordHash,
		user.UUID,
	)

	if err != nil {
		if strings.Contains(err.Error(), "unique") {
			log.Warn("failed to create a record in the database, mail or user_name already exists", "error", err.Error())
			return myErr.ErrUserAlreadyExists
		}
		log.Error("failed to execute the database user update request", "error", err)
		return err
	}

	if rowsAffected := result.RowsAffected(); rowsAffected == 0 {
		log.Error("failed to find user on update")
		return myErr.ErrUserNotFound
	}

	log.Info("user data successfully updated")
	return nil
}

func (r *PostgresUserRepo) DeleteUser(ctx context.Context, id string) error {
	op := "Database: delete user"
	log := r.log.With(slog.String("operation", op))
	log.Debug("DeleteUser func call", "userID", id)

	query := fmt.Sprintf(`
        DELETE FROM %s 
        WHERE id = $1
        `, tableName)

	result, err := r.repo.DB.Exec(ctx, query, id)
	if err != nil {
		log.Error("failed to execute the database user delete request", "error", err)
		return err
	}

	if rowsAffected := result.RowsAffected(); rowsAffected == 0 {
		log.Warn("user not found for deletion")
		return myErr.ErrUserNotFound
	}

	log.Info("user successfully deleted")
	return nil
}
