from models import db

class Pelicula(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String(200), nullable=False)
    fecha_estreno = db.Column(db.Date, nullable=False)
    sinopsis = db.Column(db.Text(), nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable = False)

    usuario = db.relationship('Usuario', backref=db.backref('peliculas', lazy=True))