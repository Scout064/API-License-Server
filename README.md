# 🔑 License Server (API-driven)

A simple **API-driven license server** built with **FastAPI**, backed by **MariaDB**, with two deployment options:

- **Apache2 + mod_wsgi** (recommended for production behind a web server)  
- **Uvicorn + systemd** (standalone FastAPI server)

Includes:  
- JWT-based authentication  
- License generation, validation, revocation  
- OpenAPI documentation (`/docs`)  
- Automated installer for Linux (Ubuntu/Debian)  

---

## 🚀 Features

- `/auth/token` → Obtain JWT access token  
- `/licenses` → Create & list licenses (admin only)  
- `/licenses/{key}` → Get license details (admin only)  
- `/licenses/{key}/revoke` → Revoke license (admin only)  
- `/licenses/validate` → Validate license key (public)  

Interactive docs:  
- Swagger UI: `/docs`  
- ReDoc: `/redoc`  

---

## 📦 Installation (Linux)

Run the automated installer:

```bash
git clone https://github.com/Scout064/license-server.git
cd license-server
chmod +x install.sh
./install.sh
