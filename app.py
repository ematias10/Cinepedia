from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, url_for
import re
#
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
#encriptacion para las contrasenas
from flask_bcrypt import Bcrypt

from models import db
from models.pelicula import Pelicula
from models.usuario import Usuario
from models.comentario import Comentario

from utils import login_required

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'



app = Flask(__name__)
app.secret_key = "secretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:2022@localhost/cinepedia'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    errores = {}

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        apellido = request.form['apellido'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        #Validar nombre
        if len(nombre) < 2:
            errores['nombre']= "El nombre debe tener al menos 2 caracteres."
        if len(apellido) < 2:
            errores['apellido']= "El apellido debe tener al menos 2 caracteres."

        #Validar email
        if not re.match(EMAIL_REGEX, email):
            errores['email'] = "El correo no tiene un formato valido."
        if Usuario.query.filter_by(email=email).first():
            errores['email'] = "El correo ya esta registrado."

        #Validar password
        if len(password) < 6:
            errores['password'] = "La contraseña debe tener al menos 6 caracteres."
        if password != confirm_password:
            errores['confirm_password'] = "Las contraseñas no coinciden."

        if errores:
            return render_template('register.html', errores=errores)
        
        password_encriptada = bcrypt.generate_password_hash(password).decode('utf-8')

        usuario = Usuario(nombre=nombre,
                          apellido=apellido,
                          email=email,
                          password=password_encriptada,
                          )
        db.session.add(usuario)
        db.session.commit()

        flash("Registro completado, por favor inicie sesion","success")
        return redirect('/login')
    return render_template('register.html', errores={})

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = Usuario.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['name'] = user.nombre
            session['username'] = str(user.nombre)+" "+str(user.apellido)
            flash("Inicio de sesión exitoso", "success")
            return redirect('/cine')
        else:
            flash("Credenciales incorrectas", "danger")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Elimina todos los datos de sesión
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for('login'))

@app.route('/cine')
@login_required
def cine():
    user_id = session['user_id']
    username = session['name']
    peliculas = Pelicula.query.all()
    return render_template('cine.html', peliculas=peliculas, user_id=user_id,username=username)

@app.route('/cine/agregar', methods = ['GET', 'POST'])
@login_required
def agregar_pelicula():
    errores = {}
    if request.method == 'POST':
        titulo = request.form['titulo']
        director = request.form['director']
        fecha_estreno = request.form['fecha_estreno']
        sinopsis = request.form['sinopsis']

        if len(titulo) < 2:
            errores['titulo'] = "El título debe tener al menos 2 caracteres."
        if len(director) < 2:
            errores['director'] = "El nombre del director debe tener al menos 2 caracteres."
        if not fecha_estreno:
            errores['fecha_estreno'] = "Debes seleccionar una fecha de estreno."
        if len(sinopsis) < 10:
            errores['sinopsis'] = "La sinopsis debe tener al menos 10 caracteres."

        try:
            fecha_estreno = datetime.strptime(fecha_estreno, '%Y-%m-%d').date()
        except ValueError:
            flash("formato de fecha incorrecto", "danger")
            return redirect(url_for('agregar_pelicula'))
        if not errores:
            pelicula = Pelicula(
                titulo=titulo,
                director=director,
                fecha_estreno=fecha_estreno,
                sinopsis=sinopsis,
                created_by=session['user_id']
            )

            db.session.add(pelicula)
            db.session.commit()
            flash("pelicula agregada con exito", "success")
            return redirect(url_for('cine'))
    return render_template('peliculas/agregar.html',errores=errores)



@app.route('/cine/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_pelicula(id):
    pelicula = Pelicula.query.get_or_404(id)

    if pelicula.created_by != session['user_id']:
        flash("No tienes permiso para editar esta película.", "danger")
        return redirect(url_for('cine'))
    errores={}
    if request.method == 'POST':
        pelicula.titulo = request.form['titulo']
        pelicula.director = request.form['director']
        pelicula.fecha_estreno = datetime.strptime(request.form['fecha_estreno'], '%Y-%m-%d').date()
        pelicula.sinopsis = request.form['sinopsis']

        db.session.commit()
        flash("Película actualizada con éxito.", "success")
        return redirect(url_for('cine'))
    return render_template('peliculas/editar.html', pelicula=pelicula, errores=errores)

@app.route('/cine/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_pelicula(id):
    pelicula = Pelicula.query.get_or_404(id)

    if pelicula.created_by != session['user_id']:
        flash("No tienes permiso para eliminar esta película.", "danger")
        return redirect(url_for('cine'))

    db.session.delete(pelicula)
    db.session.commit()
    flash("Película eliminada con éxito.", "success")
    return redirect(url_for('cine'))

@app.route('/cine/<int:id>', methods= ['GET', 'POST'])
@login_required
def detalle_pelicula(id):
    pelicula = Pelicula.query.get_or_404(id)
    creador = pelicula.usuario  # Relación con el usuario creador
    comentarios = Comentario.query.filter_by(pelicula_id=id).order_by(Comentario.fecha.desc()).all()

    if request.method == 'POST':
        if pelicula.created_by == session['user_id']:
            flash("No puedes comentar en tu propia película.", "warning")
            return redirect(url_for('detalle_pelicula', id=id))
        
        contenido = request.form['contenido'].strip()
        if contenido:
            nuevo_comentario = Comentario(contenido=contenido, usuario_id=session['user_id'], pelicula_id=id)
            db.session.add(nuevo_comentario)
            db.session.commit()
            flash("Comentario agregado.", "success")
        return redirect(url_for('detalle_pelicula', id=id))
    

    

    return render_template('peliculas/detalle.html', pelicula=pelicula, creador=creador, comentarios=comentarios)


@app.route('/comentarios/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_comentario(id):
    comentario = Comentario.query.get_or_404(id)

    if comentario.usuario_id != session['user_id']:
        flash("No puedes eliminar este comentario.", "danger")
        return redirect(url_for('detalle_pelicula', id=comentario.pelicula_id))

    db.session.delete(comentario)
    db.session.commit()
    flash("Comentario eliminado.", "success")
    return redirect(url_for('detalle_pelicula', id=comentario.pelicula_id))




if __name__ == '__main__':
    app.run(debug=True)
