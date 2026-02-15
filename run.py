import sys
import os
from flask import redirect, url_for, Flask

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_app(config_name=None):
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['DEBUG'] = True

    @app.route('/')
    def home():
        return redirect(url_for('auth.login'))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.admin import admin_bp
    from routes.teacher import teacher_bp
    from routes.student import student_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5013, debug=True)
