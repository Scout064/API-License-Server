# 🔑 License Server (API-driven)

A simple **API-driven license server** built with **FastAPI**, backed by **MariaDB**, with one deployment option:

* **Uvicorn + systemd** (standalone FastAPI server)

Includes:

* JWT-based authentication
* License generation, validation, revocation
* OpenAPI documentation (`/docs`)
* Automated installer for Linux (Ubuntu/Debian)

---

## 🚀 Features

* `/api/clients` → List and create Clients
* `/api/clients/{client_id}` → inquire client
* `/api/licenses/generate` → Generate License
* `/api/licenses/{license_key}` → inquire license status
* `/api/licenses/{license_key}/revoke` → revoke license key

Interactive docs:

* Swagger UI: `/docs`
* ReDoc: `/redoc`

---

## 📦 Installation (Linux)

Run the automated installer:

```bash
git clone https://github.com/Scout064/license-server.git
cd license-server
chmod +x install.sh
./install.sh
```

### Installer Steps

1. Prompt for **MariaDB root password**
2. **deployment method**:
   * `2` → Uvicorn + systemd
3. Installs system dependencies (`python3`, `mariadb-server`, etc.)
4. Creates database and user in MariaDB
5. Imports initial schema from `schema.sql`
6. Copies app to `/var/www/license-server` and fixes ownership to `www-data:www-data`
7. Sets up Python virtual environment (`lic/`) and installs dependencies
8. Configures deployment:
   * Uvicorn → checks if port 8000 is free, switches to 8100 if needed, sets up systemd service

---

## ⚙️ Configuration

Default credentials (change in production!):

```bash
DB_USER=license_user
DB_PASS=StrongPassword123!
JWT_SECRET=CHANGE_ME_SUPER_SECRET
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

Update environment variables in:

* `install.sh` before running the script
* `/etc/systemd/system/license-server.service` (Uvicorn)
* `app/config.py`

---

## 🖥 Access the API

* **Uvicorn**: `http://your-server-ip:8000/docs or .../redoc` or `http://your-server-ip:8100/docs or .../redoc` if 8000 is in use

---

## 🔧 Logs

* Error log: `journalctl -u license-server.service -f`

---

## 🔒 Security Recommendations

* Change `JWT_SECRET` and admin password immediately
* Always use HTTPS (SSL/TLS) in production
* Restrict access to the API using firewall or reverse proxy rules
* Consider storing secrets in `.env` or a vault solution

---

## 🧪 Quick Test

---

## 📄 License


