from src.server.index import create_app
from src.server.extensions import db

def init_db():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database initialized successfully!")

if __name__ == "__main__":
    init_db()