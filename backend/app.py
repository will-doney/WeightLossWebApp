"""
Backend API Server (Optional)
=============================
Separate API server for handling complex business logic.
Currently contains basic task endpoints.

Note: Main app.py serves the application. This file can be used
for additional microservices or API endpoints if needed.

Author: will-doney
Date: November 2025
"""

from flask import Flask, jsonify
from flask_cors import CORS

# Initialize Flask app with CORS for cross-origin requests
app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    """Health check endpoint."""
    return "Flask backend is running!"


@app.route('/api/tasks')
def get_tasks():
    """Return list of daily tasks for users.
    
    TODO: Fetch tasks from database instead of hardcoding
    TODO: Add user-specific task filtering
    """
    tasks = [
        {"id": 1, "task": "10-minute walk", "difficulty": "easy"},
        {"id": 2, "task": "Drink 2 liters of water", "difficulty": "easy"},
        {"id": 3, "task": "Stretch for 5 minutes", "difficulty": "easy"},
    ]
    return jsonify(tasks)


if __name__ == '__main__':
    # Run development server
    app.run(debug=True, port=5001)
