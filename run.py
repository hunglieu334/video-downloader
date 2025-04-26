import sys
import os

# Thêm thư mục gốc vào PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.server.index import app

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)