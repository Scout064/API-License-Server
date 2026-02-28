CREATE TABLE clients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE licenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_hash CHAR(64) NOT NULL UNIQUE,
    client_id INT NOT NULL,
    status ENUM('active', 'revoked') DEFAULT 'active',
    expires_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);

CREATE INDEX idx_license_hash ON licenses(key_hash);
