package cookie

import "net/http"

// Все эти поля взяты из стандартной библиотеке http.Cookie

// Domain: example.com
// Домен, для которого куки действительна. Если не указано, куки будет действительна только для текущего домена

// Если MaxAge = 0, то куки не имеет атрибута Max-Age (время жизни определяется через Expires)

// Expires: time.Now().Add(24 * time.Hour)
// Время истечения срока действия куки. Если не указано, куки становится "сеансовой" (удаляется при закрытии браузера).

// SameSite: http.SameSiteDefaultMode (см. в документации)
// Определяет политику отправки куки для межсайтовых запросов
// например SameSiteNoneMode - Куки отправляется для всех запросов, но только по HTTPS (требуется Secure: true)
type CookieData struct {
	Name     string // Ключ куки
	Value    string // Значение куки
	Path     string // Куки доступны на всех путях
	HttpOnly bool   // Защита от доступа через JavaScript, т.е. XSS атаки
	Secure   bool   // Куки отправляются только по HTTPS
	MaxAge   int    // Время жизни куки (в секундах)
}

// CookieManager управляет куками
type CookieManager struct{}

func (cm *CookieManager) SetCookie(w http.ResponseWriter, cookie *CookieData) {
	httpCookie := &http.Cookie{
		Name:     cookie.Name,
		Value:    cookie.Value,
		Path:     cookie.Path,
		HttpOnly: cookie.HttpOnly,
		Secure:   cookie.Secure,
		MaxAge:   cookie.MaxAge,
	}
	http.SetCookie(w, httpCookie)
}

func (cm *CookieManager) DeleteCookie(w http.ResponseWriter, name string) {
	httpCookie := &http.Cookie{
		Name:   name,
		Value:  "",
		Path:   "/",
		MaxAge: -1, // Установка MaxAge в -1 удаляет куку
	}
	http.SetCookie(w, httpCookie)
}
