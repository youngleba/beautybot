-- Таблица клиентов
CREATE TABLE IF NOT EXISTS clients (
    id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT
);

-- Таблица бонусов
CREATE TABLE IF NOT EXISTS loyalty (
    client_id BIGINT PRIMARY KEY,
    points INTEGER DEFAULT 0
);
