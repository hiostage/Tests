package sessionsRepo

import (
	"context"
	"fmt"
	"log/slog"
	"strings"

	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/pkg/db/redis"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
)

//go:generate mockgen -source=$GOFILE -destination=../mocks/mock_sessionRepo.go -package=mocksRepository
type ISessionsRepo interface {
	CreateSession(ctx context.Context, payload *dto.SessionPayload) (string, error)
	GetSession(ctx context.Context, sessionID string) (*dto.SessionPayload, error)
	DeleteSession(ctx context.Context, sessionID string) error
}

type SessionsRepo struct {
	log  *slog.Logger
	repo *redis.Redis
}

type SessionsRepoDeps struct {
	*slog.Logger
	*redis.Redis
}

func NewSessionsRepo(deps *SessionsRepoDeps) *SessionsRepo {
	return &SessionsRepo{log: deps.Logger, repo: deps.Redis}
}

func (r *SessionsRepo) CreateSession(ctx context.Context, payload *dto.SessionPayload) (string, error) {
	op := "SessionsRepo: create session"
	log := r.log.With(slog.String("operation", op))
	log.Debug("CreateSession func call", "payload", payload)

	// ID сессии это UUID пользователя
	sessionID := payload.UserUUID

	cmd := r.repo.Client.HSet(ctx, sessionID,
		"user_id", payload.UserUUID,
		"user_name", payload.UserName,
		"user_roles", strings.Join(payload.UserRoles, ","),
	)
	if err := cmd.Err(); err != nil {
		r.log.Error("failed to save session in Redis", "error", err)
		return "", err
	}

	// Устанавливаем TTL
	if result := r.repo.Client.Expire(ctx, sessionID, r.repo.TTLKeys); result.Err() != nil {
		r.log.Error("failed to set TTL for session", "error", result.Err())
		return "", result.Err()
	}

	log.Info("session successfully created", "sessionID", sessionID)
	return sessionID, nil
}

func (r *SessionsRepo) GetSession(ctx context.Context, sessionID string) (*dto.SessionPayload, error) {
	op := "SessionsRepo: get session"
	log := r.log.With(slog.String("operation", op))
	log.Debug("GetSession func call", "sessionID", sessionID)

	result, err := r.repo.Client.HGetAll(ctx, sessionID).Result()
	if err != nil {
		if result == nil {
			log.Warn("session not found")
			return nil, myErr.ErrSessionNotFound
		}
		log.Error("failed to get session", "error", err)
		return nil, err
	}

	if len(result) == 0 {
		log.Warn("session is empty")
		return nil, myErr.ErrSessionNotFound
	}

	// Парсим результат
	userUUID, ok := result["user_id"]
	if !ok {
		log.Error("missing 'user_id' field in session data")
		return nil, fmt.Errorf("missing 'user_id' field in session data, current value - %s", userUUID)
	}

	userName, ok := result["user_name"]
	if !ok {
		log.Error("missing 'user_name' field in session data")
		return nil, fmt.Errorf("missing 'user_name' field in session data, current value - %s", userName)
	}

	rolesStr, ok := result["user_roles"]
	if !ok {
		log.Error("missing 'user_roles' field in session data")
		return nil, fmt.Errorf("missing 'user_roles' field in session data, current value - %s", rolesStr)
	}

	roles := strings.Split(rolesStr, ",")

	payload := &dto.SessionPayload{
		UserUUID:  userUUID,
		UserName:  userName,
		UserRoles: roles,
	}

	log.Info("session successfully received")
	return payload, nil
}

func (r *SessionsRepo) DeleteSession(ctx context.Context, sessionID string) error {
	op := "SessionsRepo: delete session"
	log := r.log.With(slog.String("operation", op))
	log.Debug("DeleteSession func call", "sessionID", sessionID)

	deletedKeys, err := r.repo.Client.Del(ctx, sessionID).Result()
	if err != nil {
		log.Error("failed to delete session", "error", err)
		return err
	}

	if deletedKeys == 0 {
		log.Warn("session not found")
		return myErr.ErrSessionNotFound
	}

	log.Info("session successfully deleted")
	return nil
}
