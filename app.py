from flask import Flask, render_template, request, Response, session, redirect, url_for
from flask_mysqldb import MySQL, MySQLdb

app = Flask(__name__,template_folder="templates")

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="sanamed"
mysql= MySQL(app)

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
            return render_template('index.html', error="Credenciales incorrectas")

    return render_template('index.html')

@app.route('/signup', methods=["GET",'POST'])
def register():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        celular = request.form['celular']
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        
        # Insertar el nuevo usuario en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Usuarios (nombre, tipo_documento, numero_documento, celular, correo, contrasena) VALUES (%s, %s, %s, %s, %s, %s)", (nombre, tipo_documento, numero_documento, celular, correo, contrasena))
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



if __name__ == '__main__':
    app.secret_key="sanamed"
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
