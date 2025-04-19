from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import routes
    from ..app.main import main
    app.register_blueprint(main)

    return app
