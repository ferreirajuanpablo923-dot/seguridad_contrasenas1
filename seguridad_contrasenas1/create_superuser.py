import sqlite3, hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect("app.db")
c = conn.cursor()

# Cambia estos datos si quieres:
nombre = "Ingeniero Principal"
email = "ingeniero@demo.com"
password = "123456"
rol = "engineer"  # Cambia a "admin" si prefieres crear admin

try:
    c.execute("INSERT INTO usuarios (nombre,email,contrasena_hash,rol,twofa) VALUES (?,?,?,?,?)",
              (nombre, email, hash_password(password), rol, False))
    conn.commit()
    print(f"Usuario creado -> {rol}: {email} / {password}")
except Exception as e:
    print("Error:", e)

conn.close()
