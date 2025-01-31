from flask import Flask
from flask_cors import CORS
from app.routes.home_routes import home_bp
from app.routes.camera_routes import camera_bp
from app.routes.ptz_routes import ptz_bp
# from app.routes.focus_routes import focus_bp
from app.routes.discovery_routes import discovery_bp
import logging


def create_app():
    app = Flask(__name__)

    # Load configuration from instance/config.py
    # app.config.from_pyfile('config.py')

    # Suppress warnings from the daemon logger
    logging.getLogger('daemon').setLevel(logging.ERROR)

    # Enable CORS
    CORS(app)

    # Register Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(camera_bp, url_prefix='/api/camera')
    app.register_blueprint(ptz_bp, url_prefix='/api/ptz')
    # app.register_blueprint(focus_bp, url_prefix='/api/focus')
    app.register_blueprint(discovery_bp, url_prefix='/api/discovery')

    return app
