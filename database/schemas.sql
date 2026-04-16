-- Schema for Threatlabs MySQL Database

CREATE TABLE IF NOT EXISTS honey_agents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    country_name VARCHAR(100),
    service_type VARCHAR(50) NOT NULL,
    banner TEXT,
    alert_generated INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    secret_token_sha256 VARCHAR(255) UNIQUE
);

CREATE TABLE IF NOT EXISTS attack_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME,
    agent_id BIGINT,
    source_ip VARCHAR(45) NOT NULL,
    source_port INT,
    target_port INT,
    service_type VARCHAR(50) NOT NULL,
    username_attempt VARCHAR(255),
    password_attempt VARCHAR(255),
    payload TEXT,
    malware_hash VARCHAR(255),
    attack_type VARCHAR(50),
    country_code VARCHAR(10),
    country_name VARCHAR(100),
    FOREIGN KEY (agent_id) REFERENCES honey_agents (id)
);

CREATE TABLE IF NOT EXISTS malicious_ips (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_attack_count INT DEFAULT 1,
    country_code VARCHAR(10),
    country_name VARCHAR(100),
    reputation_score INT DEFAULT 0,
    classification VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS ip_agent_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_id INT NOT NULL,
    agent_id BIGINT NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    report_count INT DEFAULT 1,
    FOREIGN KEY (ip_id) REFERENCES malicious_ips (id),
    FOREIGN KEY (agent_id) REFERENCES honey_agents (id),
    UNIQUE(ip_id, agent_id)
);

CREATE TABLE IF NOT EXISTS ip_service_attacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_id INT NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    attack_count INT DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ip_id) REFERENCES malicious_ips (id),
    UNIQUE(ip_id, service_type)
);

CREATE TABLE IF NOT EXISTS compromised_credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    malicious_ip_id INT,
    service_type VARCHAR(50) NOT NULL,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    attempt_count INT DEFAULT 1,
    FOREIGN KEY (malicious_ip_id) REFERENCES malicious_ips (id)
);

CREATE TABLE IF NOT EXISTS password_attempted (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    count INT DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS username_viewed (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    count INT DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    otp_code VARCHAR(255) UNIQUE,
    otp_active INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    `key` VARCHAR(255) UNIQUE NOT NULL,
    integration VARCHAR(100),
    created_at DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS log_attempt_account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    status VARCHAR(50) NOT NULL,
    FOREIGN KEY (account_id) REFERENCES users (id)
);
