from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
import os

from src.config.app import Config
from src.server.models import db, User, init_db

def create_app():
    # Đảm bảo thư mục instance tồn tại
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'instance'), exist_ok=True)
    
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'views'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'public'),
                static_url_path='/public')  # Thêm dòng này
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Thêm context processor để truyền user vào tất cả các templates
    @app.context_processor
    def inject_user():
        return dict(user=current_user)
    
    # Register routes
    from src.server.routes.pages import register_page_routes
    from src.server.routes.api import register_api_routes
    
    register_page_routes(app)
    register_api_routes(app)
    
    # Create database tables if they don't exist
    with app.app_context():
        # Xóa tất cả các bảng và tạo lại
        db.drop_all()
        init_db()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)