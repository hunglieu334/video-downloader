from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from src.config.app import Config
from src.server.models import db, User, init_db
from src.server.routes.pages import register_page_routes
from src.server.routes.api import register_api_routes

def create_app():
    app = Flask(__name__, 
                template_folder='../../views',
                static_folder='../../public')
    app.config.from_object(Config)
    
    # Setup database
    db.init_app(app)
    
    # Setup login manager
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register routes
    register_page_routes(app)
    register_api_routes(app)
    
    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)