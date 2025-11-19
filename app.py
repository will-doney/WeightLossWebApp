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

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime, UTC
import uuid
import os
import json


# Initialize Flask application
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'your-secret-key-here'  # TODO: Use environment variable for production

# Initialize Firebase Admin SDK
db = None
try:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as firebase_error:
    print(f"ERROR: Firebase initialization failed. Check firebase-key.json exists: {firebase_error}")

# Utility function: Format timestamp as relative time (e.g., "2 hours ago")
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

# ============================================================
# ROUTE: Home Page
# ============================================================
@app.route('/')
def home():
    """Display the home/landing page."""
    return render_template('home.html')


# ============================================================
# ROUTE: User Login
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with Firebase Authentication."""
    if request.method == 'POST':
        # Get the ID token from the client
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify the ID token
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Store user info in session
                session['user_id'] = uid
                session['email'] = email
                
                # Create or update user document in Firestore
                if db:
                    user_ref = db.collection('users').document(uid)
                    user_doc = user_ref.get()
                    
                    if not user_doc.exists:
                        # Create new user document
                        user_data = {
                            'email': email,
                            'created_at': datetime.utcnow(),
                            'avatar': 'default.png',
                            'is_active': True
                        }
                        user_ref.set(user_data)
                
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            except Exception as e:
                print(f"Firebase Auth error: {e}")
                return jsonify({'success': False, 'error': 'Invalid authentication'})
        
        # Handle form-based fallback (if JavaScript fails)
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase login button', 'info')
    
    return render_template('login.html')


# ============================================================
# ROUTE: User Registration
# ============================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration with Firebase Authentication."""
    if request.method == 'POST':
        # Get the ID token from the client
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify the ID token
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Store user info in session
                session['user_id'] = uid
                session['email'] = email
                
                # Create user document in Firestore
                if db:
                    user_data = {
                        'email': email,
                        'created_at': datetime.now(UTC),
                        'avatar': 'default.png',
                        'is_active': True
                    }
                    db.collection('users').document(uid).set(user_data)
                
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            except Exception as e:
                print(f"Firebase Auth error: {e}")
                return jsonify({'success': False, 'error': 'Registration failed'})
        
        # Handle form-based fallback (if JavaScript fails)
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase signup button', 'info')
    
    return render_template('signup.html')


# ============================================================
# ROUTE: User Logout
# ============================================================
@app.route('/logout')
def logout():
    """Clear user session and Firebase auth, redirect to home page."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))


# ============================================================
# ROUTE: User Dashboard
# ============================================================
@app.route('/dashboard')
def dashboard():
    """Display user's dashboard with weight tracking and stats.
    
    Requires authentication. Displays:
    - Current weight and weight change
    - Calories burned from workouts
    - Recent activities (weights, workouts)
    - Goal progress
    """
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Fetch user's weight entries
    weight_entries = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    weight_data = []
    for entry in weight_entries:
        data = entry.to_dict()
        weight_data.append({
            'weight': data['weight'],
            'date': data['date'],
            'date_formatted': data['date'].strftime('%b %d')
        })
    
    # Sort by date in Python instead of Firestore
    weight_data.sort(key=lambda x: x['date'])
    
    # Calculate total calories burned from all workouts
    workouts = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    total_calories = sum(workout.to_dict().get('calories_burned', 0) for workout in workouts)
    
    # Build recent activities feed
    recent_activities = []
    
    # Get last 3 weight entries
    recent_weights = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    # Convert to list and sort by date (newest first)
    weight_list = []
    for weight in recent_weights:
        data = weight.to_dict()
        weight_list.append(data)
    
    weight_list.sort(key=lambda x: x['date'], reverse=True)
    
    # Take only the 3 most recent
    for data in weight_list[:3]:
        recent_activities.append({
            'icon': '⚖️',
            'title': 'Logged Weight',
            'description': f"{data['weight']} lbs",
            'time': format_timesince(data['date'])
        })
    
    # Get last 2 workouts
    recent_workouts = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    # Convert to list and sort by date (newest first)
    workout_list = []
    for workout in recent_workouts:
        data = workout.to_dict()
        workout_list.append(data)
    
    workout_list.sort(key=lambda x: x['date'], reverse=True)
    
    # Take only the 2 most recent
    for data in workout_list[:2]:
        recent_activities.append({
            'icon': '🏃‍♂️',
            'title': data.get('workout_type', 'Workout').title(),
            'description': f"{data.get('duration', 0)} min, {data.get('calories_burned', 0)} cal",
            'time': format_timesince(data['date'])
        })
    
    # Sort activities by recency (newest first)
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('dashboard.html',
        user_name=session['email'].split('@')[0],  # Use email username part
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


# ============================================================
# ROUTE: Log Weight Entry
# ============================================================
@app.route('/log_weight', methods=['GET', 'POST'])
def log_weight():
    """Record a new weight entry for the user.
    
    Stores weight value, optional notes, and timestamp in Firestore.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            weight = float(request.form['weight'])
            notes = request.form.get('notes', '').strip()
            
            weight_entry = {
                'user_id': session['user_id'],
                'weight': weight,
                'notes': notes,
                'date': datetime.utcnow()
            }
            
            db.collection('weight_entries').add(weight_entry)
            flash('Weight logged successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Please enter a valid weight number.', 'error')
    
    return render_template('log_weight.html')


# ============================================================
# ROUTE: Log Workout
# ============================================================
@app.route('/log_workout', methods=['GET', 'POST'])
def log_workout():
    """Record a new workout session.
    
    Stores workout type, duration, calories burned, and timestamp.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            workout_type = request.form['workout_type'].strip()
            duration = int(request.form['duration'])
            calories = int(request.form['calories'])
            
            if duration <= 0 or calories < 0:
                flash('Please enter valid duration and calories.', 'error')
                return render_template('log_workout.html')

            workout_entry = {
                'user_id': session['user_id'],
                'workout_type': workout_type,
                'duration': duration,
                'calories_burned': calories,
                'date': datetime.utcnow()
            }

            db.collection('workouts').add(workout_entry)
            flash('Workout logged successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Please enter valid numbers for duration and calories.', 'error')
    
    return render_template('log_workout.html')


# ============================================================
# ROUTE: Set Weight Goal
# ============================================================
@app.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    """Create or update a weight loss goal.
    
    Stores target weight, deadline, and creation timestamp.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            target_weight = float(request.form['target_weight'])
            deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
            
            goal_entry = {
                'user_id': session['user_id'],
                'target_weight': target_weight,
                'deadline': deadline,
                'created_at': datetime.utcnow(),
                'is_active': True
            }
            
            db.collection('goals').add(goal_entry)
            flash('Goal set successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Please enter a valid weight and deadline.', 'error')
    
    return render_template('set_goal.html')


# Sample tasks payload used by both HTML view and API response.
TASKS_SAMPLE = [
    {
        "id": 1,
        "task": "10-minute walk",
        "details":           "Short outdoor or indoor walk to boost circulation."
    },
    {
        "id": 2,
        "task": "Drink 2 liters of water", 
        "details": "Stay hydrated throughout the day with measured intake."
    },
    {
        "id": 3,
        "task": "Stretch for 5 minutes",
        "details": "Loosen muscles with a quick flexibility routine."
    },
]


# ============================================================
# ROUTE: Daily Tasks (HTML)
# ============================================================
@app.route('/tasks')
def tasks():
    """Display daily tasks and challenges with user-specific data."""
    if 'user_id' not in session:
        flash('Please login to access tasks', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's tasks from Firestore
    tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
    user_tasks = []
    
    if db:
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_data['id'] = task_doc.id
            user_tasks.append(task_data)
    
    # Create default tasks only for new users (one-time setup)
    if not user_tasks and db:
        # Check if user has ever had tasks before
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists or not user_doc.to_dict().get('tasks_initialized', False):
            # First time setup - create sample tasks
            for sample_task in TASKS_SAMPLE:
                task_data = {
                    'user_id': user_id,
                    'name': sample_task['task'],
                    'description': sample_task['details'],
                    'completed': False
                }
                doc_ref = db.collection('tasks').add(task_data)
                task_data['id'] = doc_ref[1].id
                user_tasks.append(task_data)
            
            # Mark user as initialized to prevent recreating tasks
            user_ref.set({'tasks_initialized': True}, merge=True)
    
    return render_template('tasks.html', tasks=user_tasks)


# ============================================================
# ROUTE: Add New Task
# ============================================================
@app.route('/add_task', methods=['POST'])
def add_task():
    """Add a new task for the current user."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    
    if not task_name:
        # Task name required (handled by form validation)
        return redirect(url_for('tasks'))
    
    if db:
        task_data = {
            'user_id': session['user_id'],
            'name': task_name,
            'description': task_description,
            'completed': False
        }
        
        db.collection('tasks').add(task_data)
        # Task added (banner handles notification)
        pass
    else:
        # Database not available (handled by banner system)
        pass
    
    return redirect(url_for('tasks'))


# ============================================================
# ROUTE: Toggle Task Completion
# ============================================================
@app.route('/toggle_task/<task_id>', methods=['POST'])
def toggle_task(task_id):
    """Toggle completion status of a task."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db:
        try:
            task_ref = db.collection('tasks').document(task_id)
            task_doc = task_ref.get()
            
            if task_doc.exists:
                task_data = task_doc.to_dict()
                
                # Verify task belongs to current user
                if task_data.get('user_id') == session['user_id']:
                    new_completed = not task_data.get('completed', False)
                    update_data = {
                        'completed': new_completed
                    }
                    
                    task_ref.update(update_data)
                    
                    status = 'completed' if new_completed else 'reopened'
                    # Task status updated (banner handles notification)
                else:
                    flash('Unauthorized task access', 'error')
            else:
                flash('Task not found', 'error')
                
        except Exception as e:
            flash('Error updating task', 'error')
            print(f"Task toggle error: {e}")
    
    return redirect(url_for('tasks'))


# ============================================================
# ROUTE: Delete Task
# ============================================================
@app.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    """Delete a task for the current user."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if db:
        try:
            task_ref = db.collection('tasks').document(task_id)
            task_doc = task_ref.get()
            
            if task_doc.exists:
                task_data = task_doc.to_dict()
                
                # Verify task belongs to current user
                if task_data.get('user_id') == session['user_id']:
                    task_ref.delete()
                    # Task deleted (banner handles notification)
                    pass
                else:
                    # Unauthorized access (handled by banner system)
                    pass
            else:
                # Task not found (handled by banner system)
                pass
                
        except Exception as e:
            # Error deleting task (handled by banner system)
            print(f"Task deletion error: {e}")
    
    return redirect(url_for('tasks'))


# ============================================================
# ROUTE: Daily Tasks (JSON API)
# ============================================================
@app.route('/api/tasks')
def tasks_api():
    """Return daily tasks as JSON for frontend or integrations."""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    tasks_list = []
    
    if db:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_data['id'] = task_doc.id
            tasks_list.append(task_data)
    
    return jsonify(tasks_list)


# ============================================================
# ROUTE: User Settings
# ============================================================
@app.route('/settings')
def settings():
    """Display user preferences and settings."""
    return render_template('settings.html')


# ============================================================
# ROUTE: Progress View
# ============================================================
@app.route('/view_progress')
def view_progress():
    """Display detailed progress analytics."""
    # For now, redirect to dashboard, but this can be expanded later
    # to show detailed progress charts and analytics
    return redirect(url_for('dashboard'))

# ROUTE: Avatar Customization
# ============================================================
@app.route('/myavatar')
def myavatar():
    """Display avatar customization page."""
    return render_template('myavatar.html')


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 Not Found errors with custom page."""
    return render_template('404.html'), 404


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================
if __name__ == '__main__':
    # Get port from environment or use default 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run Flask development server
    # NOTE: For production, use a WSGI server like Gunicorn or uWSGI
    app.run(host='0.0.0.0', port=port, debug=True)
