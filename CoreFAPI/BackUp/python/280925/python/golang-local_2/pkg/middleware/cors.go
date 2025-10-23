package middleware

import (
	"log"
	"net/http"
)

func CORS(allowedDomains []string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Add("Vary", "Origin")

			origin := r.Header.Get("Origin")
			switch {
			case origin == "":
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			case isAllowedOrigin(origin, allowedDomains):
				// w.Header().Set("X-Allowed-Domains", strings.Join(allowedDomains, ", "))
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			default:
				w.Header().Set("Content-Type", "text/plain; charset=utf-8")
				w.WriteHeader(http.StatusForbidden)
				log.Printf("Error: Origin is not allowed by CORS policy. Current origin - %s", origin)
				if _, err := w.Write([]byte("Error: Origin is not allowed by CORS policy")); err != nil {
					log.Printf("failed to record a response for rejected CORSs, err - %v", err)
				}
			}

			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

			if r.Method == http.MethodOptions {
				w.WriteHeader(http.StatusNoContent)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

func isAllowedOrigin(origin string, allowedDomains []string) bool {
	for _, domain := range allowedDomains {
		if origin == domain {
			return true
		}
	}
	return false
}
