#!/bin/bash
set -e

echo "=== Secure API License Server Installer ==="

# ---------------------------------------------------------
# 1. Gather User Inputs
# ---------------------------------------------------------
read -p "Database Host: " DB_HOST
read -p "Database Name: " DB_NAME
read -p "Database User: " DB_USER
read -s -p "Database Password: " DB_PASS
echo ""
read -s -p "JWT Secret (leave empty to auto-generate): " JWT_SECRET
echo ""

echo "--- Web Server Configuration ---"
read -p "Enter ServerName (e.g., api.yourdomain.com): " SERVER_NAME
read -p "Are you using an external reverse proxy (e.g., Cloudflare, AWS ALB, Nginx front)? (y/n): " USE_REVERSE_PROXY

if [[ "$USE_REVERSE_PROXY" =~ ^[Nn]$ ]]; then
    read -p "Do you want to install Certbot to auto-generate Let's Encrypt SSL certificates? (y/n): " USE_CERTBOT
fi

# ---------------------------------------------------------
# 2. Environment Setup
# ---------------------------------------------------------
if [ -z "$JWT_SECRET" ]; then
  JWT_SECRET=$(openssl rand -hex 64)
  echo "Generated JWT secret."
fi

echo "Creating .env file..."
cat <<EOF > .env
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASS=$DB_PASS
JWT_SECRET=$JWT_SECRET
EOF

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Applying database schema..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < schema.sql

# ---------------------------------------------------------
# 3. Systemd Service Setup
# ---------------------------------------------------------
echo "Creating system user..."
sudo useradd -r -s /bin/false licenseapi || true

echo "Creating systemd service..."
sudo tee /etc/systemd/system/licenseapi.service > /dev/null <<SERVICE
[Unit]
Description=License API Server
After=network.target

[Service]
User=licenseapi
Group=licenseapi
WorkingDirectory=$(pwd)
ExecStart=$(which uvicorn) app.main:app --host 127.0.0.1 --port 8000
Restart=always
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable licenseapi
sudo systemctl start licenseapi

# ---------------------------------------------------------
# 4. Apache2 & SSL Setup
# ---------------------------------------------------------
echo "Installing Apache2 and enabling required modules..."
sudo apt-get update
sudo apt-get install -y apache2
sudo a2enmod proxy proxy_http headers ssl rewrite

VHOST_CONF="/etc/apache2/sites-available/licenseapi.conf"

if [[ "$USE_REVERSE_PROXY" =~ ^[Yy]$ ]]; then
    echo "Configuring Apache for external reverse proxy (HTTP only)..."
    sudo tee $VHOST_CONF > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog \${APACHE_LOG_DIR}/license_error.log
    CustomLog \${APACHE_LOG_DIR}/license_access.log combined
</VirtualHost>
EOF

else
    # We are handling SSL directly in Apache
    if [[ "$USE_CERTBOT" =~ ^[Yy]$ ]]; then
        echo "Installing Certbot and generating Let's Encrypt certificates..."
        sudo apt-get install -y certbot
        
        # Stop Apache temporarily so Certbot can bind to port 80 for verification
        sudo systemctl stop apache2 || true
        sudo certbot certonly --standalone -d "$SERVER_NAME" --non-interactive --agree-tos -m "admin@$SERVER_NAME"
        
        CERT_FILE="/etc/letsencrypt/live/$SERVER_NAME/fullchain.pem"
        KEY_FILE="/etc/letsencrypt/live/$SERVER_NAME/privkey.pem"
    else
        echo "Generating self-signed SSL certificates..."
        CERT_FILE="/etc/ssl/certs/licenseapi.crt"
        KEY_FILE="/etc/ssl/private/licenseapi.key"
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$KEY_FILE" -out "$CERT_FILE" \
            -subj "/CN=$SERVER_NAME"
    fi

    echo "Configuring Apache VirtualHost with SSL..."
    sudo tee $VHOST_CONF > /dev/null <<EOF
<VirtualHost *:80>
    ServerName $SERVER_NAME
    Redirect permanent / https://$SERVER_NAME/
</VirtualHost>

<VirtualHost *:443>
    ServerName $SERVER_NAME

    SSLEngine on
    SSLCertificateFile $CERT_FILE
    SSLCertificateKeyFile $KEY_FILE

    # HSTS
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"

    # Security Headers
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Content-Security-Policy "default-src 'self'"

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    ErrorLog \${APACHE_LOG_DIR}/license_error.log
    CustomLog \${APACHE_LOG_DIR}/license_access.log combined
</VirtualHost>
EOF
fi

echo "Activating Apache configuration..."
sudo a2ensite licenseapi.conf
sudo a2dissite 000-default.conf || true
sudo systemctl restart apache2

# ---------------------------------------------------------
# 5. Final Output & JWT Warning
# ---------------------------------------------------------
echo ""
echo "=========================================================================="
echo "✅ Installation complete! Your Secure API License Server is now running."
echo "=========================================================================="
echo ""
echo "🚨 IMPORTANT: YOUR JWT SECRET 🚨"
echo "--------------------------------------------------------------------------"
echo "$JWT_SECRET"
echo "--------------------------------------------------------------------------"
echo "Please copy and save this secret in a secure location (e.g., a password manager)."
echo "You will need this exact string to generate valid JSON Web Tokens (JWT) "
echo "to authenticate against your API endpoints."
echo ""
echo "If you lose this key, you can find it in the .env file in this directory."
echo "=========================================================================="
