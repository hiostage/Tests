package validate

import (
	"github.com/go-playground/validator/v10"
)

func IsValid(data any) error {
	v := validator.New()

	if err := v.Struct(data); err != nil {
		return err
	}
	return nil
}
