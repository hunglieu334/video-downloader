from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

from src.config.app import Config
from src.server.extensions import db
from src.server.models import User

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'templates'))
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    # Register blueprints
    from src.server.routes.auth import auth
    from src.server.routes.main import main
    from src.server.routes.api import api
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(api)
    
    return app

app = create_app()