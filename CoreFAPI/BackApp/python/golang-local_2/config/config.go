package config

import (
	"flag"
	"log"
	"os"
	"time"

	"github.com/ilyakaznacheev/cleanenv"
)

type Config struct {
	Env             string `yaml:"env" env-required:"true"`
	StoragePath     string `yaml:"storage_path" env-required:"true"`
	Redis           `yaml:"redis"`
	HTTPServer      `yaml:"http_server"`
	IsFileLogOutput bool `yaml:"is_file_log_output"`
}

type HTTPServer struct {
	Address            string        `yaml:"host" env-required:"true"`
	Port               string        `yaml:"port" env-required:"true"`
	AllowedDomainsCORS []string      `yaml:"allowed_domains_cors"`
	ReadHeaderTimeout  time.Duration `yaml:"read_header_timeout"`
	ReadTimeout        time.Duration `yaml:"read_timeout"`
	WriteTimeout       time.Duration `yaml:"write_timeout"`
	IdleTimeout        time.Duration `yaml:"idle_timeout"`
}

type Redis struct {
	Address  string        `yaml:"host" env-required:"true"`
	Port     string        `yaml:"port" env-required:"true"`
	Password string        `yaml:"password" env-required:"true"`
	TTLKeys  time.Duration `yaml:"ttl" env-required:"true"`
	NumberDB int           `yaml:"db_number"` // default == 0
}

func MustLoad() *Config {
	var cfg Config
	var filePath string

	flag.StringVar(&filePath, "config", "", "path to config file")
	flag.Parse()

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		log.Fatalf("env file does not exist: %s", filePath)
	}

	if err := cleanenv.ReadConfig(filePath, &cfg); err != nil {
		log.Fatalf("cannot read config: %s", err)
	}

	log.Println("configuration file successfully loaded")
	return &cfg
}
