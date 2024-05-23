import re
from datetime import datetime, date
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_mysqldb import MySQL
import random

# Configurar la aplicación Flask
app = Flask(__name__, template_folder="templates")
app.secret_key = "sanamed"

# Configurar la conexión a la base de datos MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed"
mysql = MySQL(app)

# Función para validar la contraseña
def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[!@#$%^&*()_+=\[{\]};:<>|./?,-]", password):
        return False
    return True

# Función para obtener el ID del usuario actualmente logueado
def obtener_id_usuario_actual():
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None

# Función para generar un ID de profesional aleatorio
def generar_id_profesional_aleatorio():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    if profesionales:
        id_profesional = random.choice(profesionales)[0]
        return id_profesional
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST" and "correo" in request.form and "contrasena" in request.form:
        username = request.form['correo']
        password = request.form['contrasena']
        rol = request.form['rol']
        
        cur = mysql.connection.cursor()
        
        # Buscar en la tabla de usuarios
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s AND contrasena = %s AND tipo_perfil = %s", (username, password, rol))
        user_data = cur.fetchone()
        
        # Si no se encuentra en la tabla de usuarios, buscar en la tabla de profesionales
        if not user_data and rol == "profesional":
            cur.execute("SELECT id_profesional FROM Profesionales WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()
        
        # Si aún no se encuentra, buscar en la tabla de administradores
        if not user_data and rol == "admin":
            cur.execute("SELECT id_administrador FROM Administradores WHERE correo = %s AND contrasena = %s", (username, password))
            user_data = cur.fetchone()

        cur.close()

        if user_data:
            session['logged_in'] = True
            session['id_usuario'] = user_data[0]  # Establecer el ID de usuario en la sesión

            if rol == 'usuario':
                return redirect(url_for('user_home'))
            elif rol == 'profesional':
                return redirect(url_for('profesional_home'))
            elif rol == 'admin':
                return redirect(url_for('admin_home'))
        else:
            return render_template('index.html', error="Credenciales incorrectas")

    return render_template('index.html')

@app.route('/registro_emocion', methods=['POST'])
def registro_emocion():
    if 'logged_in' in session and session['logged_in']:
        if request.method == 'POST':
            # Obtener la emoción seleccionada por el usuario
            emocion = request.form['emocion']

            # Obtener el ID del usuario actualmente logueado
            print("Contenido de la sesión:", session)  # Agregar esta impresión
            id_usuario = obtener_id_usuario_actual()

            # Obtener la fecha y hora actual
            fecha_emocion = datetime.now()

            # Insertar la emoción en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Emociones (id_usuario, fecha_emocion, emocion) VALUES (%s, %s, %s)",
                        (id_usuario, fecha_emocion, emocion))
            mysql.connection.commit()
            cur.close()

            # Redirigir al usuario de nuevo a la página de inicio
            return redirect(url_for('user_home'))
    else:
        return redirect(url_for('index'))
    
@app.route('/signup', methods=["GET", 'POST'])
def register():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        celular = request.form['celular']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        # Validar la contraseña
        if not validate_password(contrasena):
            flash("La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial.", "error")
            return render_template('register.html')

        # Verificar si el correo electrónico ya está registrado
        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s", (correo,))
        existing_user = cur.fetchone()
        cur.close()

        if existing_user:
            flash("El correo electrónico ya está registrado. Por favor, utiliza otro correo electrónico", "error")
            return render_template('register.html')

        # Insertar el nuevo usuario en la base de datos
        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO Usuarios (nombre, tipo_documento, numero_documento, celular, correo, contrasena) VALUES (%s, %s, %s, %s, %s, %s)",
                (nombre, tipo_documento, numero_documento, celular, correo, contrasena))
            mysql.connection.commit()
            flash("Registro exitoso. Inicia sesión con tus credenciales.", "success")
            return redirect(url_for('register'))
        except Exception as e:
            mysql.connection.rollback()
            error = "El número de documento ya se encuentra registrado"
            flash(error, "error")
            return render_template('register.html', error=error)
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/user_home')
def user_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('user_home.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/admin_home')
def admin_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('admin_home.html')
    else:
        return redirect(url_for('index'))
    
@app.route('/profesional_home')
def profesional_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('profesional_home.html')
    else:
        return redirect(url_for('index'))

@app.route('/games')
def games():
    return render_template('games.html')

@app.route('/rompecabezas')
def rompecabezas():
    return render_template('rompecabezas.html')

@app.route('/laberinto')
def laberinto():
    return render_template('laberinto.html')

# Función para obtener un ID de profesional aleatorio
# Función para obtener profesionales disponibles
def obtener_profesionales_disponibles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_profesional, nombre, especialidad FROM Profesionales")
    profesionales = cur.fetchall()
    cur.close()
    return profesionales

@app.route('/agendar_cita', methods=["GET", "POST"])
def agendar_cita():
    if 'logged_in' in session and session['logged_in']:
        if request.method == "POST":
            fecha = request.form['fecha']
            hora = request.form['hora']
            motivo = request.form['motivo']
            id_usuario = session['id_usuario']

            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM Consultas WHERE fecha_consulta = %s AND hora_consulta = %s", (fecha, hora))
            cita_existente = cur.fetchone()
            cur.close()

            # Validar que la fecha no sea anterior a la fecha actual
            fecha_actual = date.today()
            fecha_seleccionada = datetime.strptime(fecha, '%Y-%m-%d').date()

            if fecha_seleccionada < fecha_actual:
                error = "No puedes programar una cita en una fecha anterior a la fecha actual."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())

            if cita_existente:
                error = "Ya hay una cita programada para esa fecha y hora."
                return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
            else:
                # Convertir la hora AM/PM a un formato de 24 horas
                hora_seleccionada = datetime.strptime(hora, '%I:%M %p').strftime('%H:%M')

                hora_inicio = datetime.strptime('08:00', '%H:%M').time()
                hora_fin = datetime.strptime('17:00', '%H:%M').time()
                
                if hora_seleccionada < hora_inicio.strftime('%H:%M') or hora_seleccionada > hora_fin.strftime('%H:%M'):
                    error = "La hora seleccionada está fuera del horario permitido (8:00 AM a 5:00 PM)."
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())

                id_profesional = generar_id_profesional_aleatorio()
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO Consultas (id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo_consulta) VALUES (%s, %s, %s, %s, %s)",
                            (id_usuario, id_profesional, fecha, hora_seleccionada, motivo))
                mysql.connection.commit()
                cur.close()
                return redirect(url_for('user_home'))

        return render_template('agendar_cita.html', profesionales=obtener_profesionales_disponibles())
    else:
        return redirect(url_for('index'))

@app.route('/consultar_citas', methods=["GET"])
def consultar_citas():
    if 'logged_in' in session and session['logged_in']:
        id_usuario = session['id_usuario']
        cur = mysql.connection.cursor()
        cur.execute("SELECT c.fecha_consulta, c.hora_consulta, c.motivo_consulta, p.nombre AS nombre_profesional, p.especialidad "
                    "FROM Consultas c JOIN Profesionales p ON c.id_profesional = p.id_profesional WHERE c.id_usuario = %s", (id_usuario,))
        citas = cur.fetchall()
        cur.close()
        return render_template('consultar_citas.html', citas=citas)
    else:
        return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
