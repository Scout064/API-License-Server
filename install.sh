#!/bin/bash
set -e

echo "=== Secure API License Server Installer ==="

APP_DIR="/var/www/licenseapi"

# ---------------------------------------------------------
# 1. Gather User Inputs (First, to determine dependencies)
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
echo ""
echo "--- Checking & Resolving Dependencies ---"

sudo apt-get update

# Base requirements
CORE_DEPS=("mariadb-server" "mariadb-client" "python3" "python3-pip" "apache2")
for pkg in "${CORE_DEPS[@]}"; do
    if ! dpkg -l | grep -q "ii  $pkg "; then
        echo "📦 Installing core dependency: $pkg..."
        sudo apt-get install -y "$pkg"
    else
        echo "✅ $pkg is already installed."
    fi
done

# Conditional Dependency: Certbot
if [[ "$USE_CERTBOT" =~ ^[Yy]$ ]]; then
    if ! command -v certbot &> /dev/null; then
        echo "📦 Installing Certbot as requested..."
        sudo apt-get install -y certbot python3-certbot-apache
    fi
fi

# Conditional Dependency: OpenSSL (Only if not using Certbot/Proxy and need self-signed)
if [[ "$USE_REVERSE_PROXY" =~ ^[Nn]$ ]] && [[ "$USE_CERTBOT" =~ ^[Nn]$ ]]; then
    if ! command -v openssl &> /dev/null; then
        echo "📦 Installing OpenSSL for self-signed certificate generation..."
        sudo apt-get install -y openssl
    fi
fi

# ---------------------------------------------------------
# 3. File Migration & Environment Setup
# ---------------------------------------------------------
echo "Moving application to $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo cp -r ./* $APP_DIR/

if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET=$(openssl rand -hex 64)
  echo "Generated JWT secret."
fi

sudo bash -c "cat <<EOF > $APP_DIR/.env
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS
JWT_SECRET=$JWT_SECRET
EOF"

echo "Installing Python dependencies..."
cd $APP_DIR
sudo pip install -r requirements.txt --break-system-packages || sudo pip install -r requirements.txt

# Ensure MariaDB is running before schema import
sudo systemctl start mariadb

echo "Applying database schema..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < $APP_DIR/schema.sql

# ---------------------------------------------------------
# 4. Systemd Service Setup
# ---------------------------------------------------------
sudo useradd -r -s /bin/false licenseapi || true
sudo chown -R licenseapi:licenseapi $APP_DIR
sudo chmod 600 $APP_DIR/.env

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
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable licenseapi
sudo systemctl start licenseapi

# ---------------------------------------------------------
# 5. Apache2 & SSL Configuration
# ---------------------------------------------------------
sudo a2enmod proxy proxy_http headers ssl rewrite
VHOST_CONF="/etc/apache2/sites-available/licenseapi.conf"

if [[ "$USE_REVERSE_PROXY" =~ ^[Yy]$ ]]; then
    # HTTP Only for proxy usage
    sudo tee $VHOST_CONF > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    DocumentRoot $APP_DIR
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
        # Self-signed
        CERT_FILE="/etc/ssl/certs/licenseapi.crt"
        KEY_FILE="/etc/ssl/private/licenseapi.key"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "$KEY_FILE" -out "$CERT_FILE" -subj "/CN=$SERVER_NAME"
    fi

    sudo tee $VHOST_CONF > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    Redirect permanent / https://$SERVER_NAME/
</VirtualHost>

<VirtualHost *:443>
    ServerName $SERVER_NAME
    DocumentRoot $APP_DIR
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

# ---------------------------------------------------------
# 6. Final Output
# ---------------------------------------------------------
echo ""
echo "=========================================================================="
echo "✅ Installation complete!"
echo "🚨 YOUR JWT SECRET: $JWT_SECRET"
echo "=========================================================================="
echo "Save this secret! It is required for API access tokens."
