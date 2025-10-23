package usecase_test

import (
	"context"
	"errors"
	"reflect"
	"testing"

	mocksRepository "gitea.youteam.space/YouTeam/go/internal/adapters/repository/mocks"
	"gitea.youteam.space/YouTeam/go/internal/dto"
	"gitea.youteam.space/YouTeam/go/internal/entity"
	"gitea.youteam.space/YouTeam/go/internal/usecase"
	myErr "gitea.youteam.space/YouTeam/go/pkg/error"
	"gitea.youteam.space/YouTeam/go/pkg/logs"
	"gitea.youteam.space/YouTeam/go/pkg/utils"
	"github.com/golang/mock/gomock"
)

func TestAuthUseCase_Register(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockUserRepo := mocksRepository.NewMockIUserRepository(ctrl)
	log := logs.NewDiscardLogger()

	authUseCase := usecase.NewAuthUseCase(&usecase.AuthUseCaseDeps{
		Logger:          log,
		IUserRepository: mockUserRepo,
	})

	tests := []struct {
		setup   func()
		args    *dto.RegisterRequest
		want    *dto.RegisterResponce
		name    string
		wantErr bool
	}{
		{
			name: "Successful registration",
			setup: func() {
				mockUserRepo.EXPECT().
					CreateUser(gomock.Any(), gomock.Any()).
					Return("62a16b1d-bbfe-419e-aab7-54e6fb101067", nil).
					Times(1)
			},
			args: &dto.RegisterRequest{
				FirstName: "John",
				LastName:  "Doe",
				Email:     "john.doe@example.com",
				Password:  "password123",
			},
			want: &dto.RegisterResponce{
				UUID: "62a16b1d-bbfe-419e-aab7-54e6fb101067",
			},
			wantErr: false,
		},
		{
			name: "Error user already exists",
			setup: func() {
				mockUserRepo.EXPECT().
					CreateUser(gomock.Any(), gomock.Any()).
					Return("", myErr.ErrUserAlreadyExists).
					Times(1)
			},
			args: &dto.RegisterRequest{
				FirstName: "John",
				LastName:  "Doe",
				Email:     "john.doe@example.com",
				Password:  "password123",
			},
			want:    nil,
			wantErr: true,
		},
		{
			name: "Error database",
			setup: func() {
				mockUserRepo.EXPECT().
					CreateUser(gomock.Any(), gomock.Any()).
					Return("", errors.New("database error")).
					Times(1)
			},
			args: &dto.RegisterRequest{
				FirstName: "John",
				LastName:  "Doe",
				Email:     "john.doe@example.com",
				Password:  "password123",
			},
			want:    nil,
			wantErr: true,
		},
		{
			name: "Error creating new user",
			setup: func() {
				mockUserRepo.EXPECT().
					CreateUser(gomock.Any(), gomock.Any()).
					Return("", errors.New("hashing password error")).
					Times(1)
			},
			args: &dto.RegisterRequest{
				FirstName: "John",
				LastName:  "Doe",
				Email:     "john.doe@example.com",
				Password:  "password123",
			},
			want:    nil,
			wantErr: true,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setup != nil {
				tt.setup()
			}

			got, err := authUseCase.Register(context.Background(), tt.args)

			if (err != nil) != tt.wantErr {
				t.Errorf("AuthUseCase.Register() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("AuthUseCase.Register() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestAuthUseCase_Login(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockUserRepo := mocksRepository.NewMockIUserRepository(ctrl)
	mockSessionRepo := mocksRepository.NewMockISessionsRepo(ctrl)
	log := logs.NewDiscardLogger()
	ctx := context.Background()

	authUseCase := usecase.NewAuthUseCase(&usecase.AuthUseCaseDeps{
		Logger:          log,
		IUserRepository: mockUserRepo,
		ISessionsRepo:   mockSessionRepo,
	})

	tests := []struct {
		setup   func()
		args    *dto.LoginRequest
		want    *dto.LoginResponce
		name    string
		wantErr bool
	}{
		{
			name: "Successful authentication",
			setup: func() {
				// Хэшируем пароль перед созданием пользователя
				hashedPassword, err := utils.Hashing("password123")
				if err != nil {
					t.Fatalf("failed to hash password: %v", err)
				}

				mockUserRepo.EXPECT().
					FindUser(gomock.Any(), &dto.UserRequest{Mode: "email", Email: "john.doe@example.com"}).
					Return(&entity.User{
						UUID:         "62a16b1d-bbfe-419e-aab7-54e6fb101067",
						FirstName:    "John",
						LastName:     "Doe",
						UserName:     "JohnDoe",
						Email:        "john.doe@example.com",
						Phone:        nil,
						PasswordHash: hashedPassword,
						Roles:        []string{"user"},
					}, nil).
					Times(1)

				mockSessionRepo.EXPECT().
					CreateSession(ctx, &dto.SessionPayload{
						UserRoles: []string{"user"},
						UserUUID:  "62a16b1d-bbfe-419e-aab7-54e6fb101067",
						UserName:  "JohnDoe",
					}).
					Return("62a16b1d-bbfe-419e-aab7-54e6fb101067", nil).
					Times(1)
			},
			args: &dto.LoginRequest{
				Email:    "john.doe@example.com",
				Password: "password123",
			},
			want: &dto.LoginResponce{
				SessionID: "62a16b1d-bbfe-419e-aab7-54e6fb101067",
			},
			wantErr: false,
		},
		{
			name: "Error user not found",
			setup: func() {
				mockUserRepo.EXPECT().
					FindUser(gomock.Any(), &dto.UserRequest{Mode: "email", Email: "unknown@example.com"}).
					Return(nil, myErr.ErrUserNotFound).
					Times(1)
			},
			args: &dto.LoginRequest{
				Email:    "unknown@example.com",
				Password: "password123",
			},
			want:    nil,
			wantErr: true,
		},
		{
			name: "Invalid password",
			setup: func() {
				// Хэшируем пароль перед созданием пользователя
				hashedPassword, err := utils.Hashing("password123")
				if err != nil {
					t.Fatalf("failed to hash password: %v", err)
				}

				mockUserRepo.EXPECT().
					FindUser(gomock.Any(), &dto.UserRequest{Mode: "email", Email: "john.doe@example.com"}).
					Return(&entity.User{
						UUID:         "62a16b1d-bbfe-419e-aab7-54e6fb101067",
						FirstName:    "John",
						LastName:     "Doe",
						Email:        "john.doe@example.com",
						Phone:        nil,
						PasswordHash: hashedPassword,
						Roles:        []string{"user"},
					}, nil).
					Times(1)
			},
			args: &dto.LoginRequest{
				Email:    "john.doe@example.com",
				Password: "wrongpassword",
			},
			want:    nil,
			wantErr: true,
		},
		{
			name: "Error creating session",
			setup: func() {
				// Хэшируем пароль перед созданием пользователя
				hashedPassword, err := utils.Hashing("password123")
				if err != nil {
					t.Fatalf("failed to hash password: %v", err)
				}

				mockUserRepo.EXPECT().
					FindUser(gomock.Any(), &dto.UserRequest{Mode: "email", Email: "john.doe@example.com"}).
					Return(&entity.User{
						UUID:         "62a16b1d-bbfe-419e-aab7-54e6fb101067",
						FirstName:    "John",
						LastName:     "Doe",
						UserName:     "JohnDoe",
						Email:        "john.doe@example.com",
						Phone:        nil,
						PasswordHash: hashedPassword,
						Roles:        []string{"user"},
					}, nil).
					Times(1)

				mockSessionRepo.EXPECT().
					CreateSession(ctx, &dto.SessionPayload{
						UserRoles: []string{"user"},
						UserUUID:  "62a16b1d-bbfe-419e-aab7-54e6fb101067",
						UserName:  "JohnDoe",
					}).
					Return("", errors.New("session creation error")).
					Times(1)
			},
			args: &dto.LoginRequest{
				Email:    "john.doe@example.com",
				Password: "password123",
			},
			want:    nil,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setup != nil {
				tt.setup()
			}

			got, err := authUseCase.Login(context.Background(), tt.args)

			if (err != nil) != tt.wantErr {
				t.Errorf("AuthUseCase.Login() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("AuthUseCase.Login() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestAuthUseCase_Session(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockSessionRepo := mocksRepository.NewMockISessionsRepo(ctrl)
	log := logs.NewDiscardLogger()
	ctx := context.Background()

	authUseCase := usecase.NewAuthUseCase(&usecase.AuthUseCaseDeps{
		Logger:        log,
		ISessionsRepo: mockSessionRepo,
	})

	tests := []struct {
		setup   func()
		want    *dto.SessionPayload
		name    string
		args    string
		wantErr bool
	}{
		{
			name: "Successful session retrieval",
			setup: func() {
				mockSessionRepo.EXPECT().
					GetSession(ctx, "valid-session-id").
					Return(&dto.SessionPayload{
						UserRoles: []string{"user"},
						UserUUID:  "29828482-a33f-4c37-b332-ed3386c9521f",
						UserName:  "JohnDoe",
					}, nil).
					Times(1)
			},
			args: "valid-session-id",
			want: &dto.SessionPayload{
				UserRoles: []string{"user"},
				UserUUID:  "29828482-a33f-4c37-b332-ed3386c9521f",
				UserName:  "JohnDoe",
			},
			wantErr: false,
		},
		{
			name: "Error session not found",
			setup: func() {
				mockSessionRepo.EXPECT().
					GetSession(ctx, "invalid-session-id").
					Return(nil, myErr.ErrSessionNotFound).
					Times(1)
			},
			args:    "invalid-session-id",
			want:    nil,
			wantErr: true,
		},
		{
			name: "Error database error",
			setup: func() {
				mockSessionRepo.EXPECT().
					GetSession(ctx, "session-id-with-db-error").
					Return(nil, errors.New("database error")).
					Times(1)
			},
			args:    "session-id-with-db-error",
			want:    nil,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setup != nil {
				tt.setup()
			}

			got, err := authUseCase.Session(context.Background(), tt.args)

			if (err != nil) != tt.wantErr {
				t.Errorf("AuthUseCase.Session() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !reflect.DeepEqual(got, tt.want) {
				t.Errorf("AuthUseCase.Session() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestAuthUseCase_SessionDel(t *testing.T) {
	ctrl := gomock.NewController(t)
	defer ctrl.Finish()

	mockSessionRepo := mocksRepository.NewMockISessionsRepo(ctrl)
	log := logs.NewDiscardLogger()
	ctx := context.Background()

	authUseCase := usecase.NewAuthUseCase(&usecase.AuthUseCaseDeps{
		Logger:        log,
		ISessionsRepo: mockSessionRepo,
	})

	tests := []struct {
		name    string
		setup   func() // Функция для настройки ожиданий мока
		args    string
		wantErr bool
	}{
		{
			name: "Successful session deletion",
			setup: func() {
				mockSessionRepo.EXPECT().
					DeleteSession(ctx, "valid-session-id").
					Return(nil).
					Times(1)
			},
			args:    "valid-session-id",
			wantErr: false,
		},
		{
			name: "Error session not found",
			setup: func() {
				mockSessionRepo.EXPECT().
					DeleteSession(ctx, "invalid-session-id").
					Return(myErr.ErrSessionNotFound).
					Times(1)
			},
			args:    "invalid-session-id",
			wantErr: true,
		},
		{
			name: "Error database error",
			setup: func() {
				mockSessionRepo.EXPECT().
					DeleteSession(ctx, "session-id-with-db-error").
					Return(errors.New("database error")).
					Times(1)
			},
			args:    "session-id-with-db-error",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.setup != nil {
				tt.setup()
			}

			err := authUseCase.SessionDel(context.Background(), tt.args)

			if (err != nil) != tt.wantErr {
				t.Errorf("AuthUseCase.SessionDel() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
		})
	}
}
