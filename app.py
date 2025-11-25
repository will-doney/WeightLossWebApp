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
    from datetime import timezone
    
    # Ensure both datetimes are timezone-aware or both are naive
    if dt.tzinfo is not None:
        # dt is timezone-aware, make now timezone-aware too
        now = datetime.now(timezone.utc)
    else:
        # dt is timezone-naive, use naive now
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
                        # Ensure avatar document exists for this user with 0 points
                        try:
                            avatar_ref = db.collection('avatars').document(uid)
                            if not avatar_ref.get().exists:
                                avatar_ref.set({'points': 0, 'updated_at': datetime.utcnow()})
                        except Exception as e:
                            print(f"Warning: could not create avatar doc for {uid}: {e}")
                
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
                # Ensure avatar doc exists for new signup
                try:
                    avatar_ref = db.collection('avatars').document(uid)
                    if not avatar_ref.get().exists:
                        avatar_ref.set({'points': 0, 'updated_at': datetime.utcnow()})
                except Exception as e:
                    print(f"Warning: could not create avatar doc for {uid} on signup: {e}")
                
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
    
    # Safely get user name from session email or fallback to user_id
    user_email = session.get('email') or session.get('user_id') or ''
    if user_email and '@' in user_email:
        user_name = user_email.split('@')[0]
    else:
        user_name = user_email or 'User'

    return render_template('dashboard.html',
        user_name=user_name,
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


# ============================================================
# ROUTE: Update Profile (Comprehensive User Data Entry)
# ============================================================
@app.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    """Comprehensive user profile update with historical tracking.
    
    Handles weight, height, age, sex, goals, activity level, and notes.
    Stores complete profile snapshots with timestamps for history tracking.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        try:
            # Extract form data
            current_weight = float(request.form['current_weight'])  # kg
            height_cm = int(request.form['height_cm'])  # cm
            age = int(request.form['age'])
            sex = request.form['sex'].strip().lower()
            target_weight = float(request.form['target_weight'])  # kg
            target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')
            weekly_goal = float(request.form['weekly_goal'])  # kg per week
            activity_level = request.form['activity_level'].strip()
            exercise_goals = request.form.get('exercise_goals', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Calculate BMI using metric formula: weight(kg) / height(m)²
            height_meters = height_cm / 100.0
            bmi = current_weight / (height_meters ** 2)
            
            # Create comprehensive profile entry
            profile_data = {
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'current_weight': current_weight,  # kg
                'height_cm': height_cm,
                'height_meters': height_meters,
                'age': age,
                'sex': sex,
                'bmi': round(bmi, 1),
                'target_weight': target_weight,  # kg
                'target_date': target_date,
                'weekly_goal': weekly_goal,  # kg per week
                'activity_level': activity_level,
                'exercise_goals': exercise_goals,
                'notes': notes,
                'weight_to_lose': current_weight - target_weight  # kg
            }
            
            # Store in profile_entries collection for history
            db.collection('profile_entries').add(profile_data)
            
            # Also add weight entry for dashboard tracking
            weight_entry = {
                'user_id': user_id,
                'weight': current_weight,  # kg
                'notes': f"Profile update - BMI: {bmi:.1f}, Height: {height_cm}cm",
                'date': datetime.utcnow()
            }
            db.collection('weight_entries').add(weight_entry)
            
            # Update or create current goals
            goal_entry = {
                'user_id': user_id,
                'target_weight': target_weight,
                'deadline': target_date,
                'weekly_goal': weekly_goal,
                'created_at': datetime.utcnow(),
                'is_active': True
            }
            db.collection('goals').add(goal_entry)
            
            flash(f'Profile updated successfully! Current BMI: {bmi:.1f}', 'success')
            return redirect(url_for('dashboard'))
            
        except (ValueError, KeyError) as e:
            flash('Please check all fields and enter valid data.', 'error')
            print(f"Profile update error: {e}")
    
    # GET request - load current data and history
    current_data = None
    profile_history = []
    
    if db:
        # Get all profile entries for user (avoid compound index)
        all_profiles = db.collection('profile_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))
        
        profile_docs = []
        for profile_doc in all_profiles.stream():
            doc_data = profile_doc.to_dict()
            doc_data['doc_id'] = profile_doc.id
            profile_docs.append(doc_data)
        
        # Sort by timestamp in Python (client-side)
        if profile_docs:
            profile_docs.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            # Get most recent profile entry
            current_data = profile_docs[0]
            if current_data.get('target_date'):
                # Handle both datetime and date objects
                target_date_obj = current_data['target_date']
                if hasattr(target_date_obj, 'date'):
                    # It's a datetime object
                    current_data['target_date'] = target_date_obj.strftime('%Y-%m-%d')
                else:
                    # It might be a string or other format
                    current_data['target_date'] = str(target_date_obj)[:10]
            
            # Get profile history (last 10 entries)
            for history_data in profile_docs[:10]:
                history_entry = {
                    'date_formatted': history_data['timestamp'].strftime('%m/%d/%Y %I:%M %p'),
                    'weight_change': f"{history_data.get('current_weight', 0)} kg",
                    'goal_change': f"Target: {history_data.get('target_weight', 0)} kg",
                    'other_changes': f"BMI: {history_data.get('bmi', 0)}, {history_data.get('height_cm', 0)}cm"
                }
                profile_history.append(history_entry)
    
    # Provide today's date for minimum date validation
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('update_profile.html', 
                         current_data=current_data, 
                         profile_history=profile_history,
                         today=today)


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
        flash('Task name is required!', 'error')
        return redirect(url_for('tasks'))
    
    if db:
        task_data = {
            'user_id': session['user_id'],
            'name': task_name,
            'description': task_description,
            'completed': False
        }
        
        db.collection('tasks').add(task_data)
        flash(f'Task "{task_name}" added successfully!', 'success')
    else:
        flash('Database not available', 'error')
    
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
                    # Atomically update avatar points when task completion changes
                    try:
                        avatar_ref = db.collection('avatars').document(session['user_id'])
                        if new_completed:
                            # add 10 points
                            avatar_ref.set({'points': firestore.Increment(10), 'updated_at': datetime.utcnow()}, merge=True)
                        else:
                            # remove 10 points
                            avatar_ref.set({'points': firestore.Increment(-10), 'updated_at': datetime.utcnow()}, merge=True)

                        # Clamp to zero if negative
                        try:
                            avatar_doc = avatar_ref.get()
                            if avatar_doc.exists:
                                pts = int(avatar_doc.to_dict().get('points', 0) or 0)
                                if pts < 0:
                                    avatar_ref.set({'points': 0, 'updated_at': datetime.utcnow()}, merge=True)
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"Error updating avatar points for {session.get('user_id')}: {e}")

                    if new_completed:
                        flash(f'Task "{task_data.get("name", "Unknown")}" completed! (+10 pts)', 'success')
                    else:
                        flash(f'Task "{task_data.get("name", "Unknown")}" reopened! (-10 pts)', 'warning')
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
                    task_name = task_data.get('name', 'Unknown')
                    task_ref.delete()
                    flash(f'Task "{task_name}" deleted successfully!', 'success')
                else:
                    flash('Unauthorized task access', 'error')
            else:
                flash('Task not found', 'error')
                
        except Exception as e:
            flash('Error deleting task', 'error')
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
# ROUTE: Change Password (Firebase)
# ============================================================
@app.route('/change_password', methods=['POST'])
def change_password():
    """Send password reset email to user via Firebase."""
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('settings'))
    
    try:
        user_email = session.get('user_email')
        if not user_email:
            flash('User email not found in session', 'error')
            return redirect(url_for('settings'))
        
        # Send password reset email via Firebase Authentication
        auth.send_password_reset_email(user_email)
        
        # Log for debugging (remove in production)
        print(f"Password reset email sent to: {user_email}")
        
        flash('✅ Password reset email sent! Check your inbox and spam folder.', 'success')
        return redirect(url_for('settings'))
        
    except Exception as e:
        error_message = f"Error sending reset email: {str(e)}"
        print(error_message)
        flash('❌ Error sending password reset email. Please try again.', 'error')
        return redirect(url_for('settings'))









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
# ROUTE: Persist Avatar Points (server-side)
# ============================================================
@app.route('/api/avatar/points', methods=['POST'])
def avatar_points_api():
    """Persist avatar points for the current authenticated user.

    Expects JSON body: { "points": <int> }
    Requires user session (`session['user_id']`) populated by login flow.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json(silent=True) or {}
    try:
        points = int(data.get('points', 0))
    except Exception:
        return jsonify({'error': 'Invalid points value'}), 400

    uid = session['user_id']
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500

    try:
        db.collection('avatars').document(uid).set({
            'points': points,
            'updated_at': datetime.utcnow()
        }, merge=True)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error saving avatar points for {uid}: {e}")
        return jsonify({'error': 'db_error'}), 500


@app.route('/api/avatar/points', methods=['GET'])
def avatar_points_get():
    """Return persisted avatar points for the current authenticated user."""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    uid = session['user_id']
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500

    try:
        doc = db.collection('avatars').document(uid).get()
        if doc.exists:
            data = doc.to_dict() or {}
            # Return points field (default 0) and other metadata
            return jsonify({'points': int(data.get('points', 0)), 'updated_at': data.get('updated_at')}), 200
        return jsonify({'points': 0}), 200
    except Exception as e:
        print(f"Error reading avatar points for {uid}: {e}")
        return jsonify({'error': 'db_error'}), 500


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
