package dto

type RegisterRequest struct {
	FirstName string `json:"firstName" validate:"required,ascii,alpha,min=2"`
	LastName  string `json:"lastName" validate:"required,ascii,alpha,min=2"`
	Email     string `json:"email" validate:"required,ascii,email"`
	Password  string `json:"password" validate:"required,min=8,max=20"`
	Phone     string `json:"phone" validate:"required,e164"`
}

type RegisterResponce struct {
	UUID string `json:"id"`
}

type UpdateRequest struct {
	FirstName string `json:"firstName" validate:"required,ascii,alpha,min=2"`
	LastName  string `json:"lastName" validate:"required,ascii,alpha,min=2"`
	Email     string `json:"email" validate:"required,ascii,email"`
	Password  string `json:"password" validate:"required,min=8,max=20"`
	Phone     string `json:"phone" validate:"required,e164"`
}

// Данные активной сессии
type SessionPayload struct {
	UserUUID  string   `json:"id"`
	UserName  string   `json:"userName"`
	UserRoles []string `json:"roles"`
}

type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8,max=20"`
}

type LoginResponce struct {
	SessionID string `json:"sessionId"`
}

// Для поиска пользователя, искать можно по id или email
type UserRequest struct {
	Mode  string
	Email string
	ID    string
}
