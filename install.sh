#!/bin/bash
set -e

echo "=== License Server Installer ==="

APP_DIR="/var/www/license-server"
DB_NAME="license_db"
DB_USER="license_user"
DB_PASS="StrongPassword123!"
# Generate or set JWT secret
JWT_SECRET="SUPER_SECRET_CHANGE_ME"

# Ask for MariaDB root password
read -sp "Enter MariaDB root password: " MYSQL_ROOT_PASS
echo ""

# Ask for deployment choice
echo "Select deployment method:"
echo "1) Apache2 + mod_wsgi"
echo "2) Uvicorn + systemd"
read -p "Enter choice [1-2]: " DEPLOY_CHOICE

# Update system
echo "[1/7] Updating system..."
apt-get update -y && apt-get upgrade -y

# Install system dependencies
echo "[2/7] Installing dependencies..."
apt-get install -y python3 python3-venv python3-pip mariadb-server apache2 libapache2-mod-wsgi-py3

# Setup MariaDB
echo "[3/7] Configuring MariaDB..."
systemctl enable mariadb
systemctl start mariadb

# Create database and user
mysql -uroot -p"${MYSQL_ROOT_PASS}" <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

# Apply schema
echo "[4/7] Applying schema..."
mysql -uroot -p"${MYSQL_ROOT_PASS}" ${DB_NAME} < schema.sql

# Deploy application
echo "[5/7] Deploying application..."
mkdir -p $APP_DIR
cp -r ./* $APP_DIR
chown -R www-data:www-data $APP_DIR
cd $APP_DIR

# Setup Python environment
echo "[6/7] Setting up Python environment..."
python3 -m venv lic
source lic/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# Deployment step
echo "[7/7] Configuring deployment..."
if [ "$DEPLOY_CHOICE" == "1" ]; then
    echo "Setting up Apache2 + mod_wsgi..."
    cp apache-vhost.conf /etc/apache2/sites-available/license-server.conf
    a2ensite license-server.conf
    a2enmod wsgi
    systemctl reload apache2
    echo "Deployment via Apache2 complete!"
elif [ "$DEPLOY_CHOICE" == "2" ]; then
    echo "Setting up Uvicorn + systemd..."

    # Check if port 8000 is in use
    if ss -tuln | grep -q ":8000"; then
        PORT=8100
        echo "Port 8000 is in use. Using port $PORT for Uvicorn."
    else
        PORT=8000
        echo "Using port $PORT for Uvicorn."
    fi

    # URL-encode the database password
    ENCODED_DB_PASS=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${DB_PASS}'))")
    # Escape special characters in JWT_SECRET for systemd
    ESCAPED_JWT_SECRET=$(printf '%s\n' "$JWT_SECRET" | sed 's/\\/\\\\/g; s/"/\\"/g')

    # Create systemd service dynamically with selected port
    SERVICE_FILE="/etc/systemd/system/license-server.service"
    cat > $SERVICE_FILE <<EOF
[Unit]
Description=FastAPI License Server
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="DATABASE_URL=mysql+pymysql://${DB_USER}:${ENCODED_DB_PASS}@localhost/${DB_NAME}"
Environment="JWT_SECRET=${ESCAPED_JWT_SECRET}"
Environment="ADMIN_USERNAME=admin"
Environment="ADMIN_PASSWORD=changeme"
ExecStart=$APP_DIR/lic/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable --now license-server
    echo "Deployment via systemd/Uvicorn complete on port $PORT!"
else
    echo "Invalid choice, exiting."
    exit 1
fi

echo "=== Installation complete! ==="
if [ "$DEPLOY_CHOICE" == "1" ]; then
    echo "Access the License API via Apache2: http://your-server-domain/api/docs"
else
    echo "Access the License API via Uvicorn: http://your-server-ip:$PORT/docs"
fi
