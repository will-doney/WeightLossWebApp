"""
Weight Loss Web App - Flask Backend
====================================
Main application entry point for the Weight Loss Web App. Handles user authentication,
weight tracking, workout logging, and goal management with Firebase Firestore integration.

Key Features:
- User registration and login with session management
- Weight entry logging and progress tracking
- Workout logging with calorie calculations
- Goal setting and deadline management
- Real-time activity feed with timestamps
- Responsive dashboard with statistics
- Daily task management with suggestions
- Avatar customization system

Dependencies:
- Flask: Web framework
- firebase-admin: Firestore database connection
- Jinja2: HTML templating (included with Flask)

Environment Setup:
- python -m venv .venv
- .venv/Scripts/Activate.ps1 (Windows)
- pip install -r requirements.txt
- python app.py

Author: will-doney
Date: November 2025
"""

from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import os


# Initialize Flask application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # TODO: Use environment variable for production

# Initialize Firebase Admin SDK
_db = None

def init_firebase():
    """Initialize Firebase if not already initialized."""
    global _db
    if _db is None:
        try:
            # Check if Firebase is already initialized (for Flask reloader)
            if not firebase_admin._apps:
                cred = credentials.Certificate("firebase-key.json")
                firebase_admin.initialize_app(cred)
            _db = firestore.client()
            print("✓ Firebase initialized successfully")
        except Exception as firebase_error:
            print(f"ERROR: Firebase initialization failed: {firebase_error}")
            _db = None

# Initialize Firebase immediately
init_firebase()


# ============================================================
# DATABASE HELPER
# ============================================================
def get_db():
    """Return the Firestore database client, initializing if needed."""
    global _db
    if _db is None:
        init_firebase()
    return _db


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================
from routes.main import main_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.tasks import tasks_bp
from routes.other import other_bp

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(other_bp)

print("✓ All route blueprints registered")


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================
if __name__ == '__main__':
    # Get port from environment or use default 5000
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting Weight Loss Web App on port {port}...")
    print("=" * 50)
    
    # Run Flask development server
    app.run(debug=True, host='0.0.0.0', port=port)
