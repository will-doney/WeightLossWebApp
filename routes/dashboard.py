"""
Dashboard Routes
================
Handles the main dashboard and user profile/activity management.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from firebase_admin import firestore
from datetime import datetime, UTC

dashboard_bp = Blueprint('dashboard', __name__)

def format_timesince(dt):
    """Format timestamp as relative time (e.g., '2 hours ago')."""
    from datetime import timezone
    
    # Ensure both datetimes are timezone-aware or both are naive
    if dt.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
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
# ROUTE: User Dashboard
# ============================================================
@dashboard_bp.route('/dashboard')
def dashboard():
    """Display user's dashboard with weight tracking and stats."""
    from app import get_db
    db = get_db()
    
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('dashboard.html',
            user_name='User',
            current_weight=None,
            weight_change=0,
            last_updated="No data",
            calories_burned=0,
            daily_calorie_goal=2000,
            workout_streak=0,
            goal_progress=0,
            goal_remaining=0,
            selected_timeframe='30d',
            weight_data=[],
            max_weight=1,
            badges=[],
            unlocked_badges=0,
            total_badges=0,
            recent_activities=[]
        )
    
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
    
    # Sort by date in Python
    weight_data.sort(key=lambda x: x['date'])
    
    # Calculate total calories burned from all workouts
    workouts = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    total_calories = sum(workout.to_dict().get('calories_burned', 0) for workout in workouts)
    
    # Build recent activities feed
    recent_activities = []
    
    # Get weight entries for activities
    recent_weights = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    weight_list = [w.to_dict() for w in recent_weights]
    weight_list.sort(key=lambda x: x['date'], reverse=True)
    
    for data in weight_list[:3]:
        recent_activities.append({
            'icon': '⚖️',
            'title': 'Logged Weight',
            'description': f"{data['weight']} lbs",
            'time': format_timesince(data['date'])
        })
    
    # Get workout entries for activities
    recent_workouts = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    workout_list = [w.to_dict() for w in recent_workouts]
    workout_list.sort(key=lambda x: x['date'], reverse=True)
    
    for data in workout_list[:2]:
        recent_activities.append({
            'icon': '🏃‍♂️',
            'title': data.get('workout_type', 'Workout').title(),
            'description': f"{data.get('duration', 0)} min, {data.get('calories_burned', 0)} cal",
            'time': format_timesince(data['date'])
        })
    
    # Sort activities by recency
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    # Get user name
    user_email = session.get('email') or session.get('user_id') or ''
    if user_email and '@' in user_email:
        user_name = user_email.split('@')[0]
    else:
        user_name = user_email or 'User'

    return render_template('dashboard.html',
        user_name=user_name,
        current_weight=weight_data[-1]['weight'] if weight_data else None,
        weight_change=0,
        last_updated="Recently",
        calories_burned=total_calories,
        daily_calorie_goal=2000,
        workout_streak=0,
        goal_progress=0,
        goal_remaining=0,
        selected_timeframe='30d',
        weight_data=weight_data[-7:],
        max_weight=max([w['weight'] for w in weight_data]) if weight_data else 1,
        badges=[],
        unlocked_badges=0,
        total_badges=0,
        recent_activities=recent_activities[:5]
    )


# ============================================================
# ROUTE: Log Weight Entry
# ============================================================
@dashboard_bp.route('/log_weight', methods=['GET', 'POST'])
def log_weight():
    """Record a new weight entry for the user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
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
            return redirect(url_for('dashboard.dashboard'))
        except ValueError:
            flash('Please enter a valid weight number.', 'error')
    
    return render_template('log_weight.html')


# ============================================================
# ROUTE: Log Workout
# ============================================================
@dashboard_bp.route('/log_workout', methods=['GET', 'POST'])
def log_workout():
    """Record a new workout session."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
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
            return redirect(url_for('dashboard.dashboard'))
        except ValueError:
            flash('Please enter valid numbers for duration and calories.', 'error')
    
    return render_template('log_workout.html')


# ============================================================
# ROUTE: Set Weight Goal
# ============================================================
@dashboard_bp.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    """Create or update a weight loss goal."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
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
            return redirect(url_for('dashboard.dashboard'))
        except ValueError:
            flash('Please enter a valid weight and deadline.', 'error')
    
    return render_template('set_goal.html')


# ============================================================
# ROUTE: Update Profile
# ============================================================
@dashboard_bp.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    """Comprehensive user profile update with historical tracking."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('update_profile.html', 
                             current_data=None, 
                             profile_history=[],
                             today=datetime.now().strftime('%Y-%m-%d'))
    
    if request.method == 'POST':
        try:
            # Extract form data
            current_weight = float(request.form['current_weight'])
            height_cm = int(request.form['height_cm'])
            age = int(request.form['age'])
            sex = request.form['sex'].strip().lower()
            target_weight = float(request.form['target_weight'])
            target_date = datetime.strptime(request.form['target_date'], '%Y-%m-%d')
            weekly_goal = float(request.form['weekly_goal'])
            activity_level = request.form['activity_level'].strip()
            exercise_goals = request.form.get('exercise_goals', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Calculate BMI
            height_meters = height_cm / 100.0
            bmi = current_weight / (height_meters ** 2)
            
            # Create profile entry
            profile_data = {
                'user_id': user_id,
                'timestamp': datetime.utcnow(),
                'current_weight': current_weight,
                'height_cm': height_cm,
                'height_meters': height_meters,
                'age': age,
                'sex': sex,
                'bmi': round(bmi, 1),
                'target_weight': target_weight,
                'target_date': target_date,
                'weekly_goal': weekly_goal,
                'activity_level': activity_level,
                'exercise_goals': exercise_goals,
                'notes': notes,
                'weight_to_lose': current_weight - target_weight
            }
            
            db.collection('profile_entries').add(profile_data)
            
            # Add weight entry
            weight_entry = {
                'user_id': user_id,
                'weight': current_weight,
                'notes': f"Profile update - BMI: {bmi:.1f}, Height: {height_cm}cm",
                'date': datetime.utcnow()
            }
            db.collection('weight_entries').add(weight_entry)
            
            # Update goals
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
            return redirect(url_for('dashboard.dashboard'))
            
        except (ValueError, KeyError) as e:
            flash('Please check all fields and enter valid data.', 'error')
            print(f"Profile update error: {e}")
    
    # GET request - load data
    current_data = None
    profile_history = []
    
    if db:
        all_profiles = db.collection('profile_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))
        
        profile_docs = []
        for profile_doc in all_profiles.stream():
            doc_data = profile_doc.to_dict()
            doc_data['doc_id'] = profile_doc.id
            profile_docs.append(doc_data)
        
        if profile_docs:
            profile_docs.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            current_data = profile_docs[0]
            
            if current_data.get('target_date'):
                target_date_obj = current_data['target_date']
                if hasattr(target_date_obj, 'date'):
                    current_data['target_date'] = target_date_obj.strftime('%Y-%m-%d')
                else:
                    current_data['target_date'] = str(target_date_obj)[:10]
            
            for history_data in profile_docs[:10]:
                history_entry = {
                    'date_formatted': history_data['timestamp'].strftime('%m/%d/%Y %I:%M %p'),
                    'weight_change': f"{history_data.get('current_weight', 0)} kg",
                    'goal_change': f"Target: {history_data.get('target_weight', 0)} kg",
                    'other_changes': f"BMI: {history_data.get('bmi', 0)}, {history_data.get('height_cm', 0)}cm"
                }
                profile_history.append(history_entry)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('update_profile.html', 
                         current_data=current_data, 
                         profile_history=profile_history,
                         today=today)
