CREATE TABLE IF NOT EXISTS clients (
    id BIGINT PRIMARY KEY,
    username TEXT,
    full_name TEXT
);

CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    duration_minutes INT NOT NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    client_id BIGINT REFERENCES clients(id),
    service_id INT REFERENCES services(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'canceled')),
    UNIQUE (client_id, start_time)
);

CREATE TABLE IF NOT EXISTS master_off_days (
    id SERIAL PRIMARY KEY,
    day DATE UNIQUE NOT NULL
);

-- Таблица для бонусной системы
CREATE TABLE IF NOT EXISTS loyalty (
    client_id BIGINT PRIMARY KEY REFERENCES clients(id),
    points INTEGER DEFAULT 0
);
