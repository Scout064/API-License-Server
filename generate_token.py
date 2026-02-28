#!/usr/bin/env python3
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("/var/www/licenseapi/.env")

def main():
    print("=== API License Server - JWT Generator ===")
    
    secret = os.getenv("JWT_SECRET")
    if not secret:
        secret = input("🔑 Enter your JWT_SECRET: ").strip()

    if not secret:
        print("❌ Error: JWT_SECRET is required.")
        return

    # Gather token details
    user_id_input = input("👤 Enter User ID [default: 1]: ").strip()
    user_id = int(user_id_input) if user_id_input else 1

    role_input = input("🛡️  Enter Role (admin/reader/user) [default: admin]: ").strip().lower()
    role = role_input if role_input else "admin"

    days_input = input("⏳ Enter expiration in days [default: 30]: ").strip()
    days = int(days_input) if days_input else 30

    # Match the payload structure defined in your auth.py
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=days),
        "iat": datetime.utcnow()
    }

    # Generate the token
    token = jwt.encode(payload, secret, algorithm="HS256")
    
    print("\n✅ Token Generated Successfully!\n")
    print("=" * 70)
    print(token)
    print("=" * 70)
    print(f"\nHeader format for API requests:")
    print(f"Authorization: Bearer {token}\n")

if __name__ == "__main__":
    # Ensure the pyjwt library is installed
    try:
        import jwt
    except ImportError:
        print("❌ Error: 'PyJWT' is not installed. Run 'pip install PyJWT' first.")
        exit(1)
        
    main()
