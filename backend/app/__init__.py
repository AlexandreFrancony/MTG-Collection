"""MTG Collection Tracker - Flask Application"""
import os
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Trust proxy headers (for HTTPS behind nginx)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # CORS - allow frontend
    CORS(app, origins=[
        'http://localhost:5173',  # Vite dev server
        'http://localhost:3000',
        os.getenv('FRONTEND_URL', 'https://mtg.francony.fr')
    ])

    # Register blueprints
    from app.routes.health import health_bp
    from app.routes.cards import cards_bp
    from app.routes.collection import collection_bp
    from app.routes.scan import scan_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(cards_bp, url_prefix='/api/cards')
    app.register_blueprint(collection_bp, url_prefix='/api/collection')
    app.register_blueprint(scan_bp, url_prefix='/api/scan')

    return app
