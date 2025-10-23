package entity

import (
	"regexp"
	"strings"
	"unicode"

	"gitea.youteam.space/YouTeam/go/pkg/utils"
)

// Определение пользователя и его поведения. Что он может? Какие в нем данные?
type User struct {
	UUID         string   `json:"uuid"`
	FirstName    string   `json:"firstName"`
	LastName     string   `json:"lastName"`
	UserName     string   `json:"userName"`
	Email        string   `json:"email"`
	Phone        *string  `json:"phone"`
	PasswordHash string   `json:"password"`
	Roles        []string `json:"roles"` // TODO: на данный момент ролей нет в БД, они вообще не определены
}

// -----------------------------------------------------------------------------------
// Строитель для создания User
type UserBuilder struct {
	u *User
}

func NewUserBuilder() *UserBuilder {
	return &UserBuilder{
		u: &User{},
	}
}

// Методы для установки полей
func (b *UserBuilder) WithUUID(uuid string) *UserBuilder {
	b.u.UUID = uuid
	return b
}

func (b *UserBuilder) WithFirstName(firstName string) *UserBuilder {
	b.u.FirstName = firstName
	return b
}

func (b *UserBuilder) WithLastName(lastName string) *UserBuilder {
	b.u.LastName = lastName
	return b
}

// Генерация UserName на основе почты
func (b *UserBuilder) WithUserName(email string) *UserBuilder {
	if email == "" {
		b.u.UserName = ""
		return b
	}

	atIndex := strings.IndexByte(email, '@')
	var username string
	if atIndex == -1 {
		username = email
	} else {
		username = email[:atIndex]
	}

	// Регулярка для разделения на слова по не буквенно-цифровым ASCII символам
	re := regexp.MustCompile(`[^a-zA-Z0-9]+`)
	parts := re.Split(username, -1)

	var sb strings.Builder

	for _, part := range parts {
		if part == "" {
			continue
		}
		runes := []rune(part)
		if len(runes) == 0 {
			continue
		}

		// Делаем первую букву заглавной
		runes[0] = unicode.ToUpper(runes[0])
		// Остальные — строчные
		for i := 1; i < len(runes); i++ {
			runes[i] = unicode.ToLower(runes[i])
		}

		sb.WriteRune(runes[0]) // первая буква
		for _, r := range runes[1:] {
			sb.WriteRune(r) // остальные буквы
		}
	}

	b.u.UserName = sb.String()
	return b
}

func (b *UserBuilder) WithEmail(email string) *UserBuilder {
	b.u.Email = email
	return b
}

func (b *UserBuilder) WithPhone(phone string) *UserBuilder {
	b.u.Phone = &phone
	return b
}

func (b *UserBuilder) WithPassword(hashedPassword string) *UserBuilder {
	b.u.PasswordHash = hashedPassword
	return b
}

func (b *UserBuilder) WithRoles(roles []string) *UserBuilder {
	b.u.Roles = roles
	return b
}

// Строим финальный объект
func (b *UserBuilder) Build() *User {
	return b.u
}

// -----------------------------------------------------------------------------------

func (u *User) CheckPassword(password string) bool {
	return utils.CheckHashing(password, u.PasswordHash)
}

// Генерация UserName на основе имени и фамилии
// func (b *UserBuilder) WithUserName(firstName, lastName string) *UserBuilder {
// 	if firstName == "" || lastName == "" {
// 		b.u.UserName = ""
// 		return b
// 	}

// 	var sb strings.Builder
// 	sb.WriteString(strings.ToUpper(string(firstName[0])))
// 	sb.WriteString(strings.ToLower(firstName[1:]))
// 	sb.WriteString(strings.ToUpper(string(lastName[0])))
// 	sb.WriteString(strings.ToLower(lastName[1:]))

// 	b.u.UserName = sb.String()
// 	return b
// }
