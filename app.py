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
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import os


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
    """Handle user login with username/password authentication.
    
    TODO: Implement password hashing (use werkzeug.security.check_password_hash)
    TODO: Add login attempt rate limiting to prevent brute force
    """
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        # Query Firebase for user with matching credentials
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


# ============================================================
# ROUTE: User Registration
# ============================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Create a new user account.
    
    SECURITY WARNING: Passwords are stored in plaintext!
    TODO: Hash passwords before storing (use werkzeug.security.generate_password_hash)
    TODO: Add email validation
    TODO: Implement password strength requirements
    """
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        # Check if username already exists
        users_ref = db.collection('users')
        existing_user = users_ref.where('username', '==', username).get()
        
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        
        # Create new user document
        user_id = str(uuid.uuid4())
        user_data = {
            'username': username,
            'email': email,
            'password': password,  # SECURITY: Should be hashed in production
            'created_at': datetime.utcnow(),
            'avatar': 'default.png',
            'is_active': True
        }
        
        users_ref.document(user_id).set(user_data)
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


# ============================================================
# ROUTE: User Logout
# ============================================================
@app.route('/logout')
def logout():
    """Clear user session and redirect to home page."""
    session.clear()
    flash('You have been logged out.', 'info')
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
    
    # Calculate total calories burned from all workouts
    workouts = db.collection('workouts')\
        .where('user_id', '==', user_id)\
        .stream()
    total_calories = sum(workout.to_dict().get('calories_burned', 0) for workout in workouts)
    
    # Build recent activities feed
    recent_activities = []
    
    # Get last 3 weight entries
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
    
    # Get last 2 workouts
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
    
    # Sort activities by recency (newest first)
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
        "difficulty": "easy",
        "details": "Short outdoor or indoor walk to boost circulation."
    },
    {
        "id": 2,
        "task": "Drink 2 liters of water",
        "difficulty": "easy",
        "details": "Stay hydrated throughout the day with measured intake."
    },
    {
        "id": 3,
        "task": "Stretch for 5 minutes",
        "difficulty": "easy",
        "details": "Loosen muscles with a quick flexibility routine."
    },
]


# ============================================================
# ROUTE: Daily Tasks (HTML)
# ============================================================
@app.route('/tasks')
def tasks():
    """Display daily tasks and challenges."""
    return render_template('tasks.html', tasks=TASKS_SAMPLE)


# ============================================================
# ROUTE: Daily Tasks (JSON API)
# ============================================================
@app.route('/api/tasks')
def tasks_api():
    """Return daily tasks as JSON for frontend or integrations."""
    return jsonify(TASKS_SAMPLE)


# ============================================================
# ROUTE: User Settings
# ============================================================
@app.route('/settings')
def settings():
    """Display user preferences and settings."""
    return render_template('settings.html')


# ============================================================
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
