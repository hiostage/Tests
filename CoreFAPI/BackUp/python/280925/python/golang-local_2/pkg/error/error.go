package error

import "errors"

var (
	// Users errors
	ErrUserAlreadyExists = errors.New("user with this email or phone number already exists")
	ErrUserNotFound      = errors.New("user not found")
	ErrInvalidPassword   = errors.New("invalid password")
	ErrModeSearch        = errors.New("incorrect user search mode")

	// Auth errors
	ErrNoSessionID     = errors.New("failed to get session id from context")
	ErrNoUserID        = errors.New("failed to get user id from context")
	ErrSessionNotFound = errors.New("session not found")
	ErrSessionExpired  = errors.New("session (cookies) expired")
	ErrIdsNotMatch     = errors.New("user id from the query data does not match the id from the session")

	// Data errors
	ErrNotUuid       = errors.New("uuid is required")
	ErrIncorrectUuid = errors.New("incorrect uuid format")

	// Other errors
	ErrTypeConversion = errors.New("type conversion error")
)
