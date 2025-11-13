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
    
    # Get user's weight data
    weight_entries = db.collection('weight_entries')\
        .where('user_id', '==', user_id)\
        .order_by('date')\
        .stream()
    
    weight_data = []
    for entry in weight_entries:
        data = entry.to_dict()
        weight_data.append({
            'weight': data['weight'],
            'date': data['date'].strftime('%b %d')
        })
    
    # Get user's workouts for calories
    workouts = db.collection('workouts')\
        .where('user_id', '==', user_id)\
        .stream()
    
    total_calories = sum(workout.to_dict().get('calories_burned', 0) for workout in workouts)
    
    # Get recent activities
    recent_activities = []
    
    # Recent weights (last 3)
    recent_weights = db.collection('weight_entries')\
        .where('user_id', '==', user_id)\
        .order_by('date', direction=firestore.Query.DESCENDING)\
        .limit(3)\
        .stream()
    
    for weight in recent_weights:
        data = weight.to_dict()
        recent_activities.append({
            'icon': '⚖️',
            'title': 'Logged Weight',
            'description': f"{data['weight']} lbs",
            'time': format_timesince(data['date'])
        })
    
    # Recent workouts (last 2)
    recent_workouts = db.collection('workouts')\
        .where('user_id', '==', user_id)\
        .order_by('date', direction=firestore.Query.DESCENDING)\
        .limit(2)\
        .stream()
    
    for workout in recent_workouts:
        data = workout.to_dict()
        recent_activities.append({
            'icon': '🏃‍♂️',
            'title': data.get('workout_type', 'Workout').title(),
            'description': f"{data.get('duration', 0)} min, {data.get('calories_burned', 0)} cal",
            'time': format_timesince(data['date'])
        })
    
    # Sort by time
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('dashboard.html',
        user_name=session['username'],
        current_weight=weight_data[-1]['weight'] if weight_data else None,
        weight_change=0,  # You can calculate this later
        last_updated="Recently",
        calories_burned=total_calories,
        daily_calorie_goal=2000,
        workout_streak=0,
        goal_progress=0,
        goal_remaining=0,
        selected_timeframe='30d',
        weight_data=weight_data[-7:],  # Last 7 entries
        max_weight=max([w['weight'] for w in weight_data]) if weight_data else 1,
        badges=[],
        unlocked_badges=0,
        total_badges=0,
        recent_activities=recent_activities[:5]
    )

@app.route('/log_weight', methods=['GET', 'POST'])
def log_weight():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        weight = float(request.form['weight'])
        notes = request.form.get('notes', '')
        
        weight_data = {
            'user_id': session['user_id'],
            'weight': weight,
            'notes': notes,
            'date': datetime.utcnow()
        }
        
        db.collection('weight_entries').add(weight_data)
        flash('Weight logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('log_weight.html')

@app.route('/log_workout', methods=['GET', 'POST'])
def log_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        workout_type = request.form['workout_type']
        duration = int(request.form['duration'])
        calories = int(request.form['calories'])
        
        workout_data = {
            'user_id': session['user_id'],
            'workout_type': workout_type,
            'duration': duration,
            'calories_burned': calories,
            'date': datetime.utcnow()
        }
        
        db.collection('workouts').add(workout_data)
        flash('Workout logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('log_workout.html')

@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        target_weight = float(request.form['target_weight'])
        deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
        
        goal_data = {
            'user_id': session['user_id'],
            'target_weight': target_weight,
            'deadline': deadline,
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        
        db.collection('goals').add(goal_data)
        flash('Goal set successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('set_goal.html')

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
