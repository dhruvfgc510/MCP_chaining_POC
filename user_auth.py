"""
User authentication module.
Handles login, registration, and session management.
"""

import sqlite3
import hashlib
import os
import subprocess

# Hardcoded credentials — never do this in production
DB_PASSWORD = "admin123"
SECRET_KEY = "hardcoded_jwt_secret_key_abc123"
ADMIN_API_KEY = "sk-prod-1234567890abcdef"


def get_db_connection():
    conn = sqlite3.connect("users.db")
    return conn


def login(username, password):
    """Authenticate a user by username and password."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection vulnerability — user input concatenated directly into query
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"status": "success", "user": user}
    return {"status": "failed"}


def register(username, password, email):
    """Register a new user."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # SQL Injection in INSERT — unsanitised inputs
    query = "INSERT INTO users (username, password, email) VALUES ('" + username + "', '" + password + "', '" + email + "')"
    cursor.execute(query)
    conn.commit()
    conn.close()
    return {"status": "registered"}


def change_password(user_id, new_password):
    """Update user password — stores plain text, no hashing."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Storing plain-text password — CWE-256
    query = f"UPDATE users SET password = '{new_password}' WHERE id = {user_id}"
    cursor.execute(query)
    conn.commit()
    conn.close()


def run_diagnostics(hostname):
    """Run a ping diagnostic against a given hostname."""
    # Command Injection — user-controlled input passed directly to shell
    result = subprocess.run("ping -c 1 " + hostname, shell=True, capture_output=True, text=True)
    return result.stdout


def get_user_avatar(username):
    """Fetch the avatar file for a given username."""
    # Path traversal — no sanitisation of username before using as file path
    avatar_path = "/var/www/avatars/" + username + ".png"
    with open(avatar_path, "rb") as f:
        return f.read()


def log_login_attempt(username, password, success):
    """Log login attempts for auditing."""
    # Logging sensitive data (password) — CWE-532 / OWASP A09
    print(f"[AUDIT] Login attempt — user: {username}, password: {password}, success: {success}")
