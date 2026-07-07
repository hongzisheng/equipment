"""启动入口

运行方式：
    conda activate equipment-backend
    python run.py

等价于原 app.py 的 `app.run(host='0.0.0.0', port=5000, debug=True)`
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
