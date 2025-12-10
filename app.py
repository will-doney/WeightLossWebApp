# WeightGame - Flask Backend Application
# ========================================
# A gamified weight loss tracking web application with Firebase integration.
#
# Features:
# - Firebase Authentication for secure user login/signup
# - Real-time Firestore database for data persistence
# - Daily task management with personalized suggestions
# - Progress tracking with weight entries and workout logs
# - Avatar customization system with points
# - Responsive dashboard with statistics and charts
#
# Setup:
#     python -m venv .venv
#     .venv/Scripts/Activate.ps1
#     pip install -r requirements.txt
#     python app.py
#
# Author: will-doney
# Date: November 2025

from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
import os


app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'

_db = None

def init_firebase():
    # Initialize Firebase Admin SDK and Firestore client.
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

init_firebase()

def get_db():
    # Return the Firestore database client, initializing if needed.
    global _db
    if _db is None:
        init_firebase()  # Lazy initialization for Flask reloader compatibility
    return _db

from routes.home import home_bp
from routes.main import main_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.tasks import tasks_bp
from routes.other import other_bp
from routes.onboarding import onboarding_bp
from routes.welcome import welcome_bp

app.register_blueprint(home_bp)
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(other_bp)
app.register_blueprint(onboarding_bp)
app.register_blueprint(welcome_bp)


print("✓ All route blueprints registered")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting WeightGame on port {port}...")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=port)