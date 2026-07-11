CREATE DATABASE IF NOT EXISTS teacher_ai;
USE teacher_ai;

CREATE TABLE classrooms (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    slug VARCHAR(255) UNIQUE,
    subject VARCHAR(255),
    password VARCHAR(255),
    description TEXT,
    color VARCHAR(50),
    max_participants INT DEFAULT 1000,
    INDEX idx_classrooms_name (name),
    INDEX idx_classrooms_slug (slug)
);

CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    role VARCHAR(50),
    email VARCHAR(255),
    INDEX idx_users_username (username)
);