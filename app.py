import re
from datetime import datetime,date
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
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

        cur = mysql.connection.cursor()
        cur.execute("SELECT id_usuario FROM Usuarios WHERE correo = %s AND contrasena = %s", (username, password))
        account = cur.fetchone()

        if account:
            session['logged_in'] = True
            session['id_usuario'] = account[0]  # Establecer el ID de usuario en la sesión
            print("ID de usuario establecido en la sesión:", session['id_usuario'])  # Agregar esta impresión
            return redirect(url_for('user_home'))
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
            return render_template('register.html', error="La contraseña debe tener al menos 8 caracteres, una mayúscula y un carácter especial.")

        # Insertar el nuevo usuario en la base de datos
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO Usuarios (nombre, tipo_documento, numero_documento, celular, correo, contrasena) VALUES (%s, %s, %s, %s, %s, %s)",
            (nombre, tipo_documento, numero_documento, celular, correo, contrasena))
        mysql.connection.commit()
        cur.close()

        return render_template('index.html')

    return render_template('register.html')

@app.route('/user_home')
def user_home():
    if 'logged_in' in session and session['logged_in']:
        # Aquí renderizas el home del usuario
        return render_template('user_home.html')
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
                    error = "La hora seleccionada está fuera del rango permitido (8:00 - 17:00)."
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())

                id_profesional = request.form['profesional']

                cur = mysql.connection.cursor()
                try:
                    cur.execute("INSERT INTO Consultas (id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo) VALUES (%s, %s, %s, %s, %s)",
                                (id_usuario, id_profesional, fecha, hora_seleccionada, motivo))
                    mysql.connection.commit()

                    cur.execute("INSERT INTO Profesionales_Usuarios (id_profesional, id_usuario) VALUES (%s, %s)",
                                (id_profesional, id_usuario))
                    mysql.connection.commit()
                except Exception as e:
                    mysql.connection.rollback()
                    error = "Error al programar la cita: " + str(e)
                    return render_template('agendar_cita.html', error=error, profesionales=obtener_profesionales_disponibles())
                finally:
                    cur.close()

                return redirect(url_for('user_home'))
    else:
        return redirect(url_for('index'))

    return render_template('agendar_cita.html', profesionales=obtener_profesionales_disponibles())
@app.route('/calendario')
def mostrar_calendario():
    # Aquí debes implementar la lógica para mostrar el calendario
    return render_template('calendario.html')

# Ruta para seleccionar un día y mostrar las emociones
@app.route('/seleccionar_dia', methods=['POST'])
def seleccionar_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        emociones, horas = obtener_emociones_por_fecha(fecha_seleccionada)
        if not emociones:
            mensaje = "No hay emociones registradas para este día."
            return render_template('emociones.html', fecha_seleccionada=fecha_seleccionada, mensaje=mensaje)
        return render_template('emociones.html', fecha_seleccionada=fecha_seleccionada, emociones_horas=zip(emociones, horas))

def obtener_emociones_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT emocion, HOUR(fecha_emocion), MINUTE(fecha_emocion) FROM Emociones WHERE DATE(fecha_emocion) = %s"
    cur.execute(query, (fecha,))
    emociones = []
    horas = []
    for row in cur.fetchall():
        emociones.append(row[0])
        hora = str(row[1]).zfill(2)
        minuto = str(row[2]).zfill(2)
        hora_formateada = f"{hora}:{minuto}"
        horas.append(hora_formateada)
    cur.close()
    return emociones, horas
def obtener_especialidad_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT especialidad FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    especialidad_profesional = cur.fetchone()[0]
    cur.close()
    return especialidad_profesional

@app.route('/consultas_dia', methods=["GET", 'POST'])
def consultas_dia():
    if request.method == 'POST':
        fecha_seleccionada = request.form['fecha']
        consultas = obtener_consultas_por_fecha(fecha_seleccionada)
        return render_template('consultas.html', fecha_seleccionada=fecha_seleccionada, consultas=consultas, obtener_nombre_profesional=obtener_nombre_profesional, obtener_especialidad_profesional=obtener_especialidad_profesional)

def obtener_consultas_por_fecha(fecha):
    cur = mysql.connection.cursor()
    query = "SELECT id_usuario, id_profesional, fecha_consulta, hora_consulta, motivo FROM Consultas WHERE DATE(fecha_consulta) = %s"
    cur.execute(query, (fecha,))
    consultas = cur.fetchall()
    cur.close()
    return consultas

def obtener_nombre_profesional(id_profesional):
    cur = mysql.connection.cursor()
    cur.execute("SELECT nombre FROM Profesionales WHERE id_profesional = %s", (id_profesional,))
    nombre_profesional = cur.fetchone()[0]
    cur.close()
    return nombre_profesional

if __name__ == '__main__':
    app.secret_key = "sanamed"
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
