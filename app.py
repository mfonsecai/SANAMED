import re  # Agrega esta línea al principio del archivo para importar el módulo de expresiones regulares
import datetime

from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL


app = Flask(__name__, template_folder="templates")

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sanamed"
mysql = MySQL(app)

def get_id_usuario():
    # Obtener el ID del usuario desde la sesión
    if 'id_usuario' in session:
        return session['id_usuario']
    else:
        return None

def validate_password(password):
    # Validar que la contraseña tenga al menos 8 caracteres, una mayúscula y un carácter especial
    if len(password) < 8:
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[!@#$%^&*()_+=\[{\]};:<>|./?,-]", password):
        return False
    return True


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=["GET", 'POST'])
def login():
    if request.method == "POST" and "correo" in request.form and "contrasena" in request.form:
        username = request.form['correo']
        password = request.form['contrasena']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Usuarios WHERE correo = %s AND contrasena = %s", (username, password))
        account = cur.fetchone()

        if account:
            session['logged_in'] = True
            return redirect(url_for('user_home'))
        else:
            return render_template('index.html', error="Usuario o contraseña incorrectos")

    return render_template('index.html')


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


@app.route('/puzzle')
def puzzle():
    return render_template('puzzle.html')

@app.route('/register_emotion', methods=["POST"])
def register_emotion():
    if request.method == 'POST':
        # Obtener el ID del usuario desde la sesión
        user_id = get_id_usuario()
        if user_id:
            emotion = request.form['emotion']
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Insertar la emoción en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO Emociones (id_usuario, emocion, fecha) VALUES (%s, %s, %s)",
                        (user_id, emotion, date))
            mysql.connection.commit()
            cur.close()

            return redirect(url_for('user_home'))
        else:
            return redirect(url_for('index'))



if __name__ == '__main__':
    app.secret_key = "sanamed"
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
