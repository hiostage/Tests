-- Создаем пользователя если не существует
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'groups_user') THEN
    CREATE ROLE groups_user WITH LOGIN PASSWORD 'strong_password';
  END IF;
END $$;

-- Создаем базу данных если не существует
SELECT 'CREATE DATABASE interest_groups'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'interest_groups')\gexec

-- Даем права пользователю
GRANT ALL PRIVILEGES ON DATABASE interest_groups TO groups_user;
ALTER DATABASE interest_groups OWNER TO groups_user;