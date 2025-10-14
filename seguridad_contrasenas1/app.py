from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'mvp_secret_key'  # Cambia esto en producción

# -----------------------
# Inicializar DB
# -----------------------
def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  contrasena_hash TEXT NOT NULL,
                  rol TEXT NOT NULL DEFAULT 'user',
                  twofa BOOLEAN DEFAULT FALSE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS analisis
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  id_usuario INTEGER NOT NULL,
                  contrasena_evaluada TEXT NOT NULL,
                  resultado TEXT NOT NULL,
                  fecha TEXT NOT NULL,
                  FOREIGN KEY(id_usuario) REFERENCES usuarios (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS apis
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre_api TEXT NOT NULL,
                  estado_conexion TEXT NOT NULL,
                  fecha_configuracion TEXT NOT NULL)''')
    conn.commit()
    conn.close()

init_db()

# -----------------------
# Utilidades
# -----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(hashed, password):
    return hashed == hash_password(password)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Debes iniciar sesión")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') not in ['admin', 'engineer']:
            flash("Acceso denegado")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def engineer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'engineer':
            flash("Acceso denegado. Solo ingenieros.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def analyze_password(password, twofa):
    criteria = {
        'longitud': len(password) >= 8,
        'mayuscula': any(c.isupper() for c in password),
        'especial': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password),
        'alfanumerica': any(c.isalpha() for c in password) and any(c.isdigit() for c in password)
    }
    score = sum(criteria.values())
    if twofa:
        score += 1
    if score >= 5:
        return "Fuerte"
    elif score >= 3:
        return "Media"
    return "Débil"

def simulate_api_connection(api_name):
    known = ['facebook','gmail','twitter']
    return 'exitoso' if api_name.lower() in known else 'fallido'

# -----------------------
# Rutas
# -----------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('analyze'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        hashed = hash_password(password)
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO usuarios (nombre,email,contrasena_hash,rol,twofa) VALUES (?,?,?,?,?)",
                      (nombre,email,hashed,'user',False))
            conn.commit()
            flash("Registro exitoso, inicia sesión")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email ya registrado")
        finally:
            conn.close()
    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute("SELECT id, contrasena_hash, rol FROM usuarios WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()
        if user and check_password(user[1], password):
            session['user_id'] = user[0]
            session['role'] = user[2]
            flash("Login exitoso")
            if user[2] == 'engineer':
                return redirect(url_for('engineer'))
            elif user[2] == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                return redirect(url_for('analyze'))
        else:
            flash("Credenciales inválidas")
    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada")
    return redirect(url_for('login'))

@app.route('/analyze', methods=['GET','POST'])
@login_required
def analyze():
    if request.method == 'POST':
        password = request.form['password']
        twofa = 'twofa' in request.form
        conn = sqlite3.connect('app.db')
        c = conn.cursor()
        c.execute("UPDATE usuarios SET twofa=? WHERE id=?", (twofa, session['user_id']))
        # Guardar versión enmascarada de la contraseña (mejor que almacenar el texto plano)
        masked = password[:2] + '***' if len(password) >= 2 else '***'
        resultado = analyze_password(password, twofa)
        fecha = datetime.now().isoformat()
        c.execute("INSERT INTO analisis (id_usuario, contrasena_evaluada, resultado, fecha) VALUES (?,?,?,?)",
                  (session['user_id'], masked, resultado, fecha))
        conn.commit()
        conn.close()
        flash(f"Contraseña analizada: {resultado}")
        return redirect(url_for('results'))
    return render_template("analyze.html")

@app.route('/results')
@login_required
def results():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("SELECT contrasena_evaluada, resultado, fecha FROM analisis WHERE id_usuario=? ORDER BY fecha DESC",
              (session['user_id'],))
    analyses = c.fetchall()
    conn.close()
    return render_template("results.html", analyses=analyses)

# -----------------------
# Panel Admin (añadir/eliminar/modificar usuarios)
# -----------------------
@app.route('/admin', methods=['GET','POST'])
@admin_required
def admin_panel():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            nombre = request.form['nombre']
            email = request.form['email']
            password = request.form['password']
            hashed = hash_password(password)
            rol = request.form.get('rol','user')
            # solo engineer puede crear admins
            if session.get('role') != 'engineer' and rol == 'admin':
                rol = 'user'
            try:
                c.execute("INSERT INTO usuarios (nombre,email,contrasena_hash,rol,twofa) VALUES (?,?,?,?,?)",
                          (nombre,email,hashed,rol,False))
                conn.commit()
                flash("Usuario añadido")
            except sqlite3.IntegrityError:
                flash("Email ya existe")
        elif action == 'delete':
            user_id = int(request.form['user_id'])
            c.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            conn.commit()
            flash("Usuario eliminado")
        elif action == 'edit':
            user_id = int(request.form['user_id'])
            nombre = request.form['nombre']
            email = request.form['email']
            rol = request.form['rol']
            if session.get('role') != 'engineer' and rol == 'admin':
                rol = 'user'
            twofa = 'twofa' in request.form
            c.execute("UPDATE usuarios SET nombre=?, email=?, rol=?, twofa=? WHERE id=?",
                      (nombre, email, rol, twofa, user_id))
            conn.commit()
            flash("Usuario modificado")
    c.execute("SELECT id, nombre, email, rol, twofa FROM usuarios WHERE rol!='engineer'")
    users = c.fetchall()
    conn.close()
    return render_template("admin.html", users=users)

# -----------------------
# Panel Engineer (gestión extendida + APIs)
# -----------------------
@app.route('/engineer', methods=['GET','POST'])
@engineer_required
def engineer():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action in ['add_user', 'add_admin']:
            nombre = request.form['nombre']
            email = request.form['email']
            password = request.form['password']
            hashed = hash_password(password)
            rol = 'user' if action == 'add_user' else 'admin'
            try:
                c.execute("INSERT INTO usuarios (nombre,email,contrasena_hash,rol,twofa) VALUES (?,?,?,?,?)",
                          (nombre,email,hashed,rol,False))
                conn.commit()
                flash(f"{'Usuario' if rol=='user' else 'Admin'} añadido")
            except sqlite3.IntegrityError:
                flash("Email ya existe")
        elif action == 'delete':
            user_id = int(request.form['user_id'])
            c.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
            conn.commit()
            flash("Usuario eliminado")
        elif action == 'edit':
            user_id = int(request.form['user_id'])
            nombre = request.form['nombre']
            email = request.form['email']
            rol = request.form['rol']
            twofa = 'twofa' in request.form
            c.execute("UPDATE usuarios SET nombre=?, email=?, rol=?, twofa=? WHERE id=?",
                      (nombre, email, rol, twofa, user_id))
            conn.commit()
            flash("Usuario modificado")
        elif action == 'add_api':
            nombre_api = request.form['nombre_api']
            estado = simulate_api_connection(nombre_api)
            fecha = datetime.now().isoformat()
            c.execute("INSERT INTO apis (nombre_api, estado_conexion, fecha_configuracion) VALUES (?,?,?)",
                      (nombre_api, estado, fecha))
            conn.commit()
            flash(f"API {nombre_api} añadida con estado: {estado}")
    c.execute("SELECT id, nombre, email, rol, twofa FROM usuarios WHERE rol!='engineer'")
    users = c.fetchall()
    c.execute("SELECT id, nombre_api, estado_conexion, fecha_configuracion FROM apis ORDER BY fecha_configuracion DESC")
    apis = c.fetchall()
    conn.close()
    return render_template("engineer.html", users=users, apis=apis)

if __name__ == '__main__':
    app.run(debug=True)
