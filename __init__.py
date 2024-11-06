from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os  # Importa el módulo os para manejar rutas

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "*"}})

    # Usa PostgreSQL en producción (Render) y SQLite localmente
    if os.getenv("RENDER"):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")  # Configura la URL de PostgreSQL en Render
    else:
        # Configuración de SQLite para desarrollo local
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')


    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True

    app.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'
    app.config['JWT_ALGORITHM'] = "HS256"
    
    jwt = JWTManager(app)  # Inicializa JWTManager
    
    db.init_app(app)

    from .routes import routes_blueprint
    app.register_blueprint(routes_blueprint)

    with app.app_context():
        db.create_all()  # Crea las tablas en la base de datos

    return app

