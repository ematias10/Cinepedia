from datetime import datetime
from models import db

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now())
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    pelicula_id = db.Column(db.Integer, db.ForeignKey('pelicula.id'), nullable=False)

    usuario = db.relationship('Usuario', backref=db.backref('comentarios', lazy=True))
    pelicula = db.relationship('Pelicula', backref=db.backref('comentarios', lazy=True, cascade="all, delete-orphan"))
