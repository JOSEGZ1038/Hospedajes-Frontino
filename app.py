import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Cambia esto por una clave segura en producción
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ruta para ver y dejar reseñas de un hospedaje
@app.route('/resenas/<int:hospedaje_id>', methods=['GET', 'POST'])
def resenas(hospedaje_id):
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    # Obtener datos del hospedaje
    c.execute('SELECT * FROM hospedajes WHERE id = ?', (hospedaje_id,))
    hospedaje = c.fetchone()
    if not hospedaje:
        conn.close()
        return redirect(url_for('index'))
    # Si POST, guardar reseña solo si está autenticado
    if request.method == 'POST':
        usuario = session.get('usuario')
        if not usuario:
            conn.close()
            return redirect(url_for('login'))
        comentario = request.form['comentario']
        c.execute('INSERT INTO resenas (hospedaje_id, usuario, comentario) VALUES (?, ?, ?)',
                  (hospedaje_id, usuario, comentario))
        conn.commit()
    # Obtener reseñas
    c.execute('SELECT usuario, comentario, fecha FROM resenas WHERE hospedaje_id = ? ORDER BY fecha DESC', (hospedaje_id,))
    lista_resenas = c.fetchall()
    conn.close()
    return render_template('resenas.html', hospedaje=hospedaje, resenas=lista_resenas)

# Inicializar la base de datos
conn = sqlite3.connect('inventario.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS hospedajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    direccion TEXT NOT NULL,
    telefono TEXT NOT NULL,
    descripcion TEXT,
    precio REAL DEFAULT 0.0,
    tipo TEXT,
    imagen TEXT
)''')
# Tabla de reseñas
c.execute('''CREATE TABLE IF NOT EXISTS resenas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospedaje_id INTEGER NOT NULL,
    usuario TEXT,
    comentario TEXT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospedaje_id) REFERENCES hospedajes(id)
)''')
conn.commit()
conn.close()


# Vista principal, muestra hospedajes. Si es admin, puede registrar
@app.route('/')
def index():
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute('SELECT * FROM hospedajes')
    hospedajes = c.fetchall()
    conn.close()
    es_admin = session.get('usuario') == 'admin'
    return render_template('index.html', hospedajes=hospedajes, es_admin=es_admin)


# Ruta para registrar hospedaje (solo admin)
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if session.get('usuario') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        descripcion = request.form['descripcion']
        precio = request.form.get('precio', 0)
        tipo = request.form.get('tipo')
        imagen_file = request.files.get('imagen')
        imagen_path = ''
        if imagen_file and imagen_file.filename:
            filename = f"{nombre.replace(' ', '_')}_{imagen_file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(save_path)
            imagen_path = save_path.replace('\\', '/').replace('c:/Users/Yamile/Desktop/Sistema de Inventario/', '')

        conn = sqlite3.connect('inventario.db')
        c = conn.cursor()
        c.execute('INSERT INTO hospedajes (nombre, direccion, telefono, descripcion, precio, tipo, imagen) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (nombre, direccion, telefono, descripcion, precio, tipo, imagen_path))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('registrar.html')

# Login simple para admin/cliente
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        # Usuario admin: admin / clave: admin123
        if usuario == 'admin' and clave == 'admin123':
            session['usuario'] = 'admin'
            return redirect(url_for('index'))
        elif usuario == 'cliente' and clave == 'cliente123':
            session['usuario'] = 'cliente'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Credenciales incorrectas')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('index'))


# Ruta para eliminar hospedaje (solo admin)
@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    if session.get('usuario') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    c.execute('DELETE FROM hospedajes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Ruta para editar hospedaje (solo admin)
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if session.get('usuario') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('inventario.db')
    c = conn.cursor()
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        descripcion = request.form['descripcion']
        precio = request.form.get('precio', 0)
        tipo = request.form.get('tipo', '')
        imagen_file = request.files.get('imagen')
        imagen_path = request.form.get('imagen_actual', '')
        if imagen_file and imagen_file.filename:
            filename = f"{nombre.replace(' ', '_')}_{imagen_file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen_file.save(save_path)
            imagen_path = save_path.replace('\\', '/').replace('c:/Users/Yamile/Desktop/Sistema de Inventario/', '')

        c.execute('''UPDATE hospedajes SET nombre=?, direccion=?, telefono=?, descripcion=?, precio=?, tipo=?, imagen=? WHERE id=?''',
              (nombre, direccion, telefono, descripcion, precio, tipo, imagen_path, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    else:
        c.execute('SELECT * FROM hospedajes WHERE id = ?', (id,))
        hospedaje = c.fetchone()
        conn.close()
        if not hospedaje:
            return redirect(url_for('index'))
        return render_template('editar.html', hospedaje=hospedaje)

if __name__ == '__main__':
    app.run(debug=True)
