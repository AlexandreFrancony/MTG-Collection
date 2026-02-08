"""Entry point for the MTG Collection Tracker API"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))

    print(f"🎴 MTG Collection Tracker API starting on port {port}")
    print(f"   Debug mode: {debug}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
