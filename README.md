# API License Server (Hardened Edition)

[![Python application](https://github.com/Scout064/API-License-Server/actions/workflows/python-app.yml/badge.svg?branch=Hardening)](https://github.com/Scout064/API-License-Server/actions/workflows/python-app.yml)
[![CodeQL Advanced](https://github.com/Scout064/API-License-Server/actions/workflows/codeql.yml/badge.svg)](https://github.com/Scout064/API-License-Server/actions/workflows/codeql.yml)
[![Dependabot Updates](https://github.com/Scout064/API-License-Server/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/Scout064/API-License-Server/actions/workflows/dependabot/dependabot-updates)
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

## Roles (RBAC)

| Role   | Permissions                                        |
| ------ | -------------------------------------------------- |
| admin  | Create clients, generate licenses, revoke licenses |
| reader | View/validate licenses only                        |

---

## Installation (Secure Setup)

### 1. Clone Repository

```bash
git clone https://github.com/Scout064/API-License-Server.git
cd API-License-Server
```

### 2. Run Secure Installer

```bash
chmod +x install.sh
./install.sh
```

You will be prompted for:

* Database Host
* Database Name
* Database User
* Database Password
* JWT Secret (auto-generated if left empty)

No default credentials are used.

### 3. Configure Apache

Copy:

```
apache-vhost.conf
```

Edit:

* ServerName
* SSL certificate paths

Enable required modules:

```bash
a2enmod proxy proxy_http headers ssl
systemctl reload apache2
```

---

## Environment Variables

The server requires the following variables in `.env`:

```
DB_HOST=
DB_NAME=
DB_USER=
DB_PASS=
JWT_SECRET=
```

If any are missing, the server will refuse to start.

---

## Database Schema

### Clients Table

* id
* name
* email
* created_at

### Licenses Table

* id
* key_hash (SHA-256)
* client_id
* status (active / revoked)
* expires_at
* created_at

License keys are never stored in plaintext.

---

## Authentication

All protected routes require a JWT token.

Send in header:

```
Authorization: Bearer <token>
```

### JWT Payload Example (Admin)

```json
{
  "sub": 1,
  "role": "admin",
  "exp": 1735689600
}
```

### JWT Payload Example (Reader)

```json
{
  "sub": 2,
  "role": "reader",
  "exp": 1735689600
}
```

---

## OpenAPI Documentation

Interactive docs:

```
https://yourdomain.com/docs
```

Alternative view:

```
https://yourdomain.com/redoc
```

To authenticate in Swagger:

1. Click **Authorize**
2. Enter:

   ```
   Bearer <your_token>
   ```
3. Click Authorize

---

## API Endpoints

### Clients (Admin Only)

```
POST   /clients
GET    /clients
GET    /clients/{client_id}
```

### Licenses

```
POST   /licenses/generate          (admin)
GET    /licenses/{license_key}     (reader/admin)
POST   /licenses/{license_key}/revoke  (admin)
```

---

## curl Examples

### Create Client

```bash
curl -X POST https://yourdomain.com/clients \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "Test Client",
        "email": "client@example.com"
      }'
```

### Generate License

```bash
curl -X POST "https://yourdomain.com/licenses/generate?client_id=1" \
  -H "Authorization: Bearer <admin_token>"
```

Response:

```json
{
  "id": 5,
  "client_id": 1,
  "status": "active",
  "key": "ABCD-1234-EFGH-5678",
  "created_at": "2026-02-27T10:12:55"
}
```

⚠ The plaintext key is returned only once.

### Validate License

```bash
curl -X GET https://yourdomain.com/licenses/ABCD-1234-EFGH-5678 \
  -H "Authorization: Bearer <reader_token>"
```

### Revoke License

```bash
curl -X POST https://yourdomain.com/licenses/ABCD-1234-EFGH-5678/revoke \
  -H "Authorization: Bearer <admin_token>"
```

---

## Rate Limiting

Default limits:

* 5/minute → license generation
* 5/minute → revocation
* 10/minute → validation
* 5/minute → client creation

If exceeded:

```
HTTP 429 Too Many Requests
```

Response:

```json
{
  "detail": "Rate limit exceeded"
}
```

---

## Security Model

### License Keys

* Generated using `secrets`
* Format: `XXXX-XXXX-XXXX-XXXX`
* Hashed using SHA-256 before storage
* Plaintext returned only once

### JWT Security

* HS256 algorithm
* Expiration enforced
* Role claim required
* Algorithm strictly validated

### Deployment Security

* HTTP redirected to HTTPS
* HSTS enabled (1 year)
* Secure headers:

  * X-Content-Type-Options
  * X-Frame-Options
  * Content-Security-Policy
  * X-XSS-Protection
* Service runs as non-root user
* Binds to 127.0.0.1
* Reverse proxy required
* No direct DB exposure

---

## Development Mode

Install dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
uvicorn app.main:app --reload
```

---

## Production Recommendations

* Use strong random JWT secret
* Restrict DB user permissions
* Only expose port 443
* Enable firewall rules
* Monitor logs for repeated failures
* Rotate JWT secret periodically
* Backup database regularly

---

## License

Public Domain (CC0-1.0)

---

## Security Summary

This hardened version protects against:

* SQL injection
* JWT algorithm confusion
* Token replay attacks
* License brute force attempts
* Plaintext key leakage
* Privilege escalation
* Insecure deployment defaults
