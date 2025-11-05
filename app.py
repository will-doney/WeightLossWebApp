"""
WeightGame Flask Application
---------------------------
Main entry point for the WeightGame web application. This Flask app serves a gamified
weight loss tracking system with features for daily tasks, progress visualization,
and avatar customization.

Routes:
- / : Home page with app introduction
- /dashboard : User progress and statistics
- /tasks : Daily challenges and habits
- /settings : User preferences and app configuration
- /myavatar : Character customization
- 404 handler : Custom not found page

Author: will-doney
Date: November 2025
"""

from flask import Flask, render_template, send_from_directory, request
import os

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/tasks')
def tasks():
    return render_template('tasks.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/myavatar')
def myavatar():
    return render_template('myavatar.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # Use port 5000 by default. For production, use a WSGI server.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
