# 🔑 License Server (API-driven)

A simple **API-driven license server** built with **FastAPI**, backed by **MariaDB**, with two deployment options:

* **Apache2 + mod\_wsgi** (recommended for production behind a web server)
* **Uvicorn + systemd** (standalone FastAPI server)

Includes:

* JWT-based authentication
* License generation, validation, revocation
* OpenAPI documentation (`/docs`)
* Automated installer for Linux (Ubuntu/Debian)

---

## 🚀 Features

* `/auth/token` → Obtain JWT access token
* `/licenses` → Create & list licenses (admin only)
* `/licenses/{key}` → Get license details (admin only)
* `/licenses/{key}/revoke` → Revoke license (admin only)
* `/licenses/validate` → Validate license key (public)

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
2. Select **deployment method**:

   * `1` → Apache2 + mod\_wsgi
   * `2` → Uvicorn + systemd
3. Installs system dependencies (`python3`, `mariadb-server`, `apache2`, etc.)
4. Creates database and user in MariaDB
5. Imports initial schema from `schema.sql`
6. Copies app to `/var/www/license-server` and fixes ownership to `www-data:www-data`
7. Sets up Python virtual environment (`lic/`) and installs dependencies
8. Configures selected deployment:

   * Apache2 → creates vhost, enables site, reloads Apache
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

* `/etc/systemd/system/license-server.service` (Uvicorn)
* `app/config.py` or directly in your FastAPI code if needed

---

## 🖥 Access the API

* **Apache2**: `http://your-server-domain/api/docs`
* **Uvicorn**: `http://your-server-ip:8000/docs` or `http://your-server-ip:8100/docs` if 8000 is in use

---

## 🔧 Apache2 Logs

* Error log: `/var/log/apache2/license-server-error.log`
* Access log: `/var/log/apache2/license-server-access.log`

---

## 🔒 Security Recommendations

* Change `JWT_SECRET` and admin password immediately
* Always use HTTPS (SSL/TLS) in production
* Restrict access to the API using firewall or reverse proxy rules
* Consider storing secrets in `.env` or a vault solution

---

## 🧪 Quick Test

Obtain token:

```bash
curl -X POST http://your-server/api/auth/token \
     -d "username=admin&password=changeme" \
     -H "Content-Type: application/x-www-form-urlencoded"
```

Create license:

```bash
curl -X POST http://your-server/api/licenses \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"product_code":"MYAPP-PRO","owner":"customer@example.com","expires_in_days":365}'
```

Validate license:

```bash
curl -X POST http://your-server/api/licenses/validate \
     -H "Content-Type: application/json" \
     -d '{"key":"XXXX-XXXX-XXXX","product_code":"MYAPP-PRO"}'
```

---

## 📄 License

MIT
