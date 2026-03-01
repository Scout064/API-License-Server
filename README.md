# API License Server (Hardened Edition)

[![Python application](https://github.com/Scout064/API-License-Server/actions/workflows/python-app.yml/badge.svg?branch=Hardening)](https://github.com/Scout064/API-License-Server/actions/workflows/python-app.yml)
[![CodeQL Advanced](https://github.com/Scout064/API-License-Server/actions/workflows/codeql.yml/badge.svg)](https://github.com/Scout064/API-License-Server/actions/workflows/codeql.yml)
[![Dependabot Updates](https://github.com/Scout064/API-License-Server/actions/workflows/dependabot/dependabot-updates/badge.svg?branch=main)](https://github.com/Scout064/API-License-Server/actions/workflows/dependabot/dependabot-updates)
[![Dependency review](https://github.com/Scout064/API-License-Server/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Scout064/API-License-Server/actions/workflows/dependency-review.yml)

A secure, production-ready License Management API built with FastAPI and MariaDB.

This hardened version includes:

* 🔐 Hashed license key storage (no plaintext keys in database)
* 🔑 JWT authentication with role-based access control (RBAC)
* 🚦 Rate limiting (anti-bruteforce protection)
* 🔒 HTTPS enforcement + HSTS
* 🛡 Secure HTTP headers
* 👤 Non-root service execution
* ⚙ Environment-based configuration (no default credentials)

---

## Features

### Core Functionality
* Create and manage clients
* Generate secure license keys
* Validate licenses
* Revoke licenses
* Optional expiration dates

### Security Enhancements
* SHA-256 hashed license keys
* JWT tokens with expiration
* Strict HS256 algorithm enforcement
* Role-based access control (Admin / Reader)
* Rate limiting per endpoint
* HTTPS-only deployment
* HSTS enabled
* Secure systemd service
* Indexed database lookups
* Cascading client-license cleanup

---

## Architecture

```
Client → HTTPS → Apache → FastAPI → MariaDB
```

* Apache handles TLS termination
* FastAPI handles API logic
* MariaDB stores hashed license data
* JWT secures API access

---

## Prerequisites

Before running the installation, ensure your server meets the following requirements:

* **Operating System:** An `apt`-based Linux distribution (Debian or Ubuntu).
* **Database:** MariaDB version **10.4 or higher** is a hard requirement.
* **Permissions:** You must have `sudo` privileges to execute the installer.

### Adding a user to the sudo group

If your current user is not in the sudo group, log in as `root` (or use `su -`) and run:

```
usermod -aG sudo yourusername
```

*Note: You must log out and log back in for changes to take effect.*

---

## Installation (Secure Setup)

### 1. Clone Repository

Use `git` to clone the source code to your local machine:

```
git clone https://github.com/Scout064/API-License-Server.git
cd API-License-Server
```

### 2. Run Secure Installer

Make the script executable and run it. The script will automatically check for and install dependencies (Apache2, MariaDB-Server, Python, etc.) based on your choices.

```
chmod +x install.sh
./install.sh
```

You will be prompted for:

* Database Host, Name, User, and Password
* JWT Secret (leave empty to auto-generate)
* ServerName (e.g., api.yourdomain.com)
* SSL Preference (Certbot/Let's Encrypt or Self-Signed)

### 3. Finalize Apache

The installer creates a configuration at `/etc/apache2/sites-available/licenseapi.conf`. If you did not use the automated SSL setup, ensure you edit this file with your certificate paths:

```
sudo a2enmod proxy proxy_http headers ssl rewrite
sudo a2ensite licenseapi.conf
sudo systemctl restart apache2
```

---

## Roles (RBAC)

| Role | Permissions |
| --- | --- |
| admin | Create clients, generate licenses, revoke licenses |
| reader | View/validate licenses only |

---

## Environment Variables

The server requires a `.env` file in `/var/www/licenseapi/`:

```
DB_HOST=
DB_NAME=
DB_USER=
DB_PASS=
JWT_SECRET=
```

---

## API Endpoints

### Clients (Admin Only)

* `POST /clients` - Create a new client
* `GET /clients` - List all clients

### Licenses

* `POST /licenses/generate?client_id=1` (Admin) - Generate a new key
* `GET /licenses/{license_key}` (Reader/Admin) - Validate a key
* `POST /licenses/{license_key}/revoke` (Admin) - Revoke a key

---

## curl Example: Generate License

```
curl -X POST "[https://yourdomain.com/licenses/generate?client_id=1](https://yourdomain.com/licenses/generate?client_id=1)" \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**

```
{
  "id": 5,
  "client_id": 1,
  "status": "active",
  "key": "ABCD-1234-EFGH-5678",
  "created_at": "2026-02-27T10:12:55"
}
```

*⚠ The plaintext key is only shown once during generation.*

---

## Security Model

* **License Keys:** Generated using `secrets` and stored as SHA-256 hashes.
* **JWT:** Uses HS256 algorithm with enforced expiration and role claims.
* **Deployment:** Service runs as a dedicated `licenseapi` non-root user. Apache enforces HSTS and secure headers (CSP, X-Frame-Options).

---

## License

Public Domain (CC0-1.0)
