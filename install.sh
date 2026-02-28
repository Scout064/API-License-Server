#!/bin/bash
set -euo pipefail

echo "=== Secure API License Server Installer (Hardened) ==="

APP_DIR="/var/www/licenseapi"

# ---------------------------------------------------------
# 1. Gather User Inputs
# ---------------------------------------------------------
read -p "Database Host (e.g., 127.0.0.1): " DB_HOST
read -p "Database Name: " DB_NAME
read -p "Database User: " DB_USER
read -s -p "Database Password: " DB_PASS
echo ""
read -s -p "JWT Secret (leave empty to auto-generate): " JWT_SECRET
echo ""

echo "--- Web Server Configuration ---"
read -p "Enter ServerName (e.g., api.yourdomain.com): " SERVER_NAME
read -p "Are you using an external reverse proxy? (y/n): " USE_REVERSE_PROXY

USE_CERTBOT="n"
if [[ "$USE_REVERSE_PROXY" =~ ^[Nn]$ ]]; then
    read -p "Use Certbot for Let's Encrypt SSL? (y/n): " USE_CERTBOT
fi

# ---------------------------------------------------------
# 2. Dependency Resolution
# ---------------------------------------------------------
echo "--- Installing Dependencies ---"
sudo apt-get update

CORE_DEPS=("mariadb-server" "mariadb-client" "python3" "python3-pip" "apache2")
for pkg in "${CORE_DEPS[@]}"; do
    if ! dpkg -l | grep -q "ii  $pkg "; then
        sudo apt-get install -y "$pkg"
    fi
done

if [[ "$USE_CERTBOT" =~ ^[Yy]$ ]]; then
    sudo apt-get install -y certbot python3-certbot-apache
fi

if [[ "$USE_REVERSE_PROXY" =~ ^[Nn]$ ]] && [[ "$USE_CERTBOT" =~ ^[Nn]$ ]]; then
    sudo apt-get install -y openssl
fi

# ---------------------------------------------------------
# 3. MariaDB Hardening
# ---------------------------------------------------------
echo "--- Hardening MariaDB ---"

sudo systemctl enable mariadb
sudo systemctl start mariadb

# Secure root access (uses unix_socket auth by default on Ubuntu)
sudo mysql <<SECUREMYSQL
DELETE FROM mysql.user WHERE User='';
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
UPDATE mysql.user SET Host='localhost' WHERE User='root';
FLUSH PRIVILEGES;
SECUREMYSQL

# Force local bind only (if DB_HOST is localhost)
if [[ "$DB_HOST" == "127.0.0.1" ]] || [[ "$DB_HOST" == "localhost" ]]; then
    sudo sed -i 's/^bind-address.*/bind-address = 127.0.0.1/' /etc/mysql/mariadb.conf.d/50-server.cnf
fi

# Disable LOCAL INFILE (security risk)
if ! grep -q "local-infile=0" /etc/mysql/mariadb.conf.d/50-server.cnf; then
    echo "local-infile=0" | sudo tee -a /etc/mysql/mariadb.conf.d/50-server.cnf
fi

sudo systemctl restart mariadb

# Create DB and least-privileged user
sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'${DB_HOST}' IDENTIFIED BY '${DB_PASS}';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON \`${DB_NAME}\`.* TO '${DB_USER}'@'${DB_HOST}';
FLUSH PRIVILEGES;
EOF

# ---------------------------------------------------------
# 4. App Setup
# ---------------------------------------------------------
echo "Deploying application..."
sudo mkdir -p "$APP_DIR"
sudo cp -r ./* "$APP_DIR/"

if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET=$(openssl rand -hex 64)
fi

sudo bash -c "cat <<EOF > $APP_DIR/.env
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS
JWT_SECRET=$JWT_SECRET
EOF"

cd "$APP_DIR"
sudo pip install -r requirements.txt --break-system-packages || sudo pip install -r requirements.txt

echo "Applying database schema..."
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < "$APP_DIR/schema.sql"

# ---------------------------------------------------------
# 5. Systemd Service
# ---------------------------------------------------------
sudo useradd -r -s /bin/false licenseapi || true
sudo chown -R licenseapi:licenseapi "$APP_DIR"
sudo chmod 750 "$APP_DIR"
sudo chmod 600 "$APP_DIR/.env"

sudo tee /etc/systemd/system/licenseapi.service > /dev/null <<SERVICE
[Unit]
Description=License API Server
After=network.target mariadb.service

[Service]
User=licenseapi
Group=licenseapi
WorkingDirectory=$APP_DIR
ExecStart=$(which uvicorn) app.main:app --host 127.0.0.1 --port 8000
Restart=always
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable licenseapi
sudo systemctl start licenseapi

# ---------------------------------------------------------
# 6. Apache + SSL
# ---------------------------------------------------------
sudo a2enmod proxy proxy_http headers ssl rewrite
VHOST_CONF="/etc/apache2/sites-available/licenseapi.conf"

if [[ "$USE_REVERSE_PROXY" =~ ^[Yy]$ ]]; then
    sudo tee "$VHOST_CONF" > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
EOF
else
    if [[ "$USE_CERTBOT" =~ ^[Yy]$ ]]; then
        sudo systemctl stop apache2 || true
        sudo certbot certonly --standalone -d "$SERVER_NAME" --non-interactive --agree-tos -m "admin@$SERVER_NAME"
        CERT_FILE="/etc/letsencrypt/live/$SERVER_NAME/fullchain.pem"
        KEY_FILE="/etc/letsencrypt/live/$SERVER_NAME/privkey.pem"
    else
        CERT_FILE="/etc/ssl/certs/licenseapi.crt"
        KEY_FILE="/etc/ssl/private/licenseapi.key"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" -subj "/CN=$SERVER_NAME"
    fi

    sudo tee "$VHOST_CONF" > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    Redirect permanent / https://$SERVER_NAME/
</VirtualHost>

<VirtualHost *:443>
    ServerName $SERVER_NAME
    SSLEngine on
    SSLCertificateFile $CERT_FILE
    SSLCertificateKeyFile $KEY_FILE
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
EOF
fi

sudo a2ensite licenseapi.conf
sudo a2dissite 000-default.conf || true
sudo systemctl restart apache2

echo "=========================================================================="
echo "✅ Installation complete!"
echo "🚨 YOUR JWT SECRET: $JWT_SECRET"
echo "=========================================================================="
