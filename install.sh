#!/bin/bash
set -e

echo "=== Secure API License Server Installer ==="

read -p "Database Host: " DB_HOST
read -p "Database Name: " DB_NAME
read -p "Database User: " DB_USER
read -s -p "Database Password: " DB_PASS
echo ""
read -s -p "JWT Secret (leave empty to auto-generate): " JWT_SECRET
echo ""

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

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Applying database schema..."
mysql -h $DB_HOST -u $DB_USER -p$DB_PASS $DB_NAME < schema.sql

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

echo "Installation complete."
