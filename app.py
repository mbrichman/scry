from flask import Flask
from flask_cors import CORS

from config import SECRET_KEY
from routes import init_routes

def create_app():
    """Application factory pattern for better testing and configuration"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize PostgreSQL database
    print("🚀 Initializing PostgreSQL database")
    from db.database import create_tables
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️ Database table creation warning: {e}")
    
    # Initialize routes
    init_routes(app)
    
    return app

# Create the app instance
app = create_app()

# === Main ===
if __name__ == "__main__":
    import os
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
