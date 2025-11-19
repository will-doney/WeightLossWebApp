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

from flask import Flask, render_template, send_from_directory, request,redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import os


app = Flask(__name__, static_folder='static', template_folder='templates')


# Initialize Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!

# Initialize Firebase
cred = credentials.Certificate("firebase-key.json")  # Make sure this file is in your project
firebase_admin.initialize_app(cred)

# Firebase Firestore database
db = firestore.client()

# Helper function to format time
def format_timesince(dt):
    now = datetime.utcnow()
    diff = now - dt
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hours ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minutes ago"
    else:
        return "Just now"

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Find user in Firebase
        users_ref = db.collection('users')
        user_query = users_ref.where('username', '==', username).where('password', '==', password).get()
        
        if user_query:
            user_data = user_query[0].to_dict()
            session['user_id'] = user_query[0].id
            session['username'] = user_data['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user exists
        users_ref = db.collection('users')
        existing_user = users_ref.where('username', '==', username).get()
        
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        
        # Create new user
        user_id = str(uuid.uuid4())
        user_data = {
            'username': username,
            'email': email,
            'password': password,  # In production, you should hash this!
            'created_at': datetime.utcnow()
        }
        
        users_ref.document(user_id).set(user_data)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
         flash('Please login to access the dashboard', 'error')
         return redirect(url_for('login'))
    
    user_id = session['user_id']


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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
