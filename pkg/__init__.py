from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail

from pkg.models import db 
from pkg.routes import register_blueprints

csrf = CSRFProtect()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='static', template_folder='templates')
    app.config.from_pyfile("config.py")

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    register_blueprints(app)

    return app
