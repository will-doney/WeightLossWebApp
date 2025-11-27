# Dashboard Routes Module
# =======================
# Handles user dashboard, profile management, and activity tracking.
# Provides weight logging, workout tracking, goals, and profile updates.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from firebase_admin import firestore
from datetime import datetime, UTC

dashboard_bp = Blueprint('dashboard', __name__)

def format_timesince(dt):
    # Format datetime as relative time string (e.g., '2 hours ago').
    from datetime import timezone
    
    # Handle timezone-aware and timezone-naive datetimes
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


def generate_motivational_messages(user_name, avatar_points, weight_lost, goal_progress, 
                                   workout_streak, tasks_completed, tasks_total):
    """Generate personalized motivational messages based on user progress."""
    messages = []
    
    # Welcome message
    if user_name:
        messages.append(f"Welcome back, {user_name}! 👋")
    
    # Avatar points message
    if avatar_points >= 500:
        messages.append(f"You're on fire! 🔥 {avatar_points} points!")
    elif avatar_points >= 200:
        messages.append(f"Great progress! {avatar_points} points earned! 💪")
    elif avatar_points >= 50:
        messages.append(f"Keep going! You've earned {avatar_points} points! ⭐")
    
    # Weight loss message
    if weight_lost >= 10:
        messages.append(f"Amazing! You've lost {weight_lost} units! 🎉")
    elif weight_lost >= 5:
        messages.append(f"Excellent progress! {weight_lost} units down! ✨")
    elif weight_lost > 0:
        messages.append(f"You're making progress! {weight_lost} units down! 👍")
    
    # Goal progress message
    if goal_progress >= 75:
        messages.append(f"Almost there! {goal_progress:.0f}% to your goal! 🚀")
    elif goal_progress >= 50:
        messages.append(f"You're halfway there! {goal_progress:.0f}% complete! 🎯")
    elif goal_progress >= 25:
        messages.append(f"Great start! {goal_progress:.0f}% of your goal reached! 📈")
    
    # Workout streak message
    if workout_streak >= 30:
        messages.append(f"Incredible! {workout_streak} day workout streak! 🏆")
    elif workout_streak >= 7:
        messages.append(f"Amazing! {workout_streak} day streak going! 💪")
    elif workout_streak >= 3:
        messages.append(f"Nice! {workout_streak} day streak! Keep it up! 🔥")
    elif workout_streak > 0:
        messages.append(f"You've got a {workout_streak} day streak! 💯")
    
    # Task completion message
    if tasks_total > 0:
        completion_rate = (tasks_completed / tasks_total) * 100
        if completion_rate >= 90:
            messages.append(f"Tasks crushed! {completion_rate:.0f}% complete! 🎊")
        elif completion_rate >= 75:
            messages.append(f"Excellent task completion: {completion_rate:.0f}%! 📋")
        elif completion_rate >= 50:
            messages.append(f"Good work on tasks: {completion_rate:.0f}% done! ✅")
        elif tasks_completed > 0:
            messages.append(f"Keep completing tasks! {tasks_completed}/{tasks_total} done. 🚀")
    
    # Default motivational messages if low activity
    if not messages or len(messages) < 2:
        default_messages = [
            "Let's crush those fitness goals! 💪",
            "Every step counts! 🚶",
            "You've got this! 🎯",
            "Keep pushing forward! 🚀",
            "Your future self will thank you! 🌟"
        ]
        messages.extend(default_messages[:(3 - len(messages))])
    
    return messages[:3]  # Return top 3 messages


def calculate_workout_streak(db, user_id):
    """Calculate the current workout streak (consecutive days with workouts)."""
    try:
        workouts = db.collection('workouts')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .stream()
        
        workout_dates = set()
        for workout in workouts:
            data = workout.to_dict()
            if 'date' in data:
                workout_dates.add(data['date'].date())
        
        if not workout_dates:
            return 0
        
        # Sort dates in reverse
        sorted_dates = sorted(workout_dates, reverse=True)
        today = datetime.utcnow().date()
        
        # Check if most recent workout is within last 2 days
        if (today - sorted_dates[0]).days > 1:
            return 0  # Streak broken if no workout today or yesterday
        
        streak = 1
        for i in range(len(sorted_dates) - 1):
            if (sorted_dates[i] - sorted_dates[i + 1]).days == 1:
                streak += 1
            else:
                break
        
        return streak
    except Exception as e:
        print(f"Error calculating workout streak: {e}")
        return 0


def calculate_goal_progress(db, user_id, current_weight):
    """Calculate progress towards weight loss goal as percentage."""
    try:
        # Get latest profile with goal info
        profiles = db.collection('profile_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(1)\
            .stream()
        
        profile_list = list(profiles)
        if not profile_list:
            return 0, 0, None
        
        profile = profile_list[0].to_dict()
        initial_weight = profile.get('current_weight')
        target_weight = profile.get('target_weight')
        
        if not initial_weight or not target_weight or initial_weight <= target_weight:
            return 0, 0, None
        
        total_to_lose = initial_weight - target_weight
        already_lost = initial_weight - current_weight
        
        if total_to_lose <= 0:
            return 0, 0, None
        
        progress_percent = (already_lost / total_to_lose) * 100
        progress_percent = min(100, max(0, progress_percent))  # Clamp 0-100
        
        return round(progress_percent, 1), total_to_lose - already_lost, target_weight
    except Exception as e:
        print(f"Error calculating goal progress: {e}")
        return 0, 0, None


@dashboard_bp.route('/dashboard')
def dashboard():
    # Display user dashboard with weight tracking, stats, activity feed, avatar, tasks, and points.
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('dashboard.html',
            user_name='User',
            current_weight=None,
            current_weight_unit='kg',
            weight_lost=0,
            weight_lost_unit='kg',
            last_updated="No data",
            calories_burned=0,
            daily_calorie_goal=2000,
            workout_streak=0,
            goal_progress=0,
            goal_remaining=0,
            target_weight=None,
            selected_timeframe='30d',
            weight_data=[],
            max_weight=1,
            badges=[],
            unlocked_badges=0,
            total_badges=0,
            recent_activities=[],
            avatar_points=0,
            avatar_level=1,
            avatar_progress=0,
            tasks_completed=0,
            tasks_total=0,
            motivational_messages=[]
        )
    
    # Fetch user's weight entries for chart
    weight_entries = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    weight_data = []
    initial_weight = None
    
    for entry in weight_entries:
        data = entry.to_dict()
        weight_data.append({
            'weight': data['weight'],
            'date': data['date'],
            'date_formatted': data['date'].strftime('%b %d')
        })
    
    weight_data.sort(key=lambda x: x['date'])
    
    # Get initial weight (first recorded weight)
    if weight_data:
        initial_weight = weight_data[0]['weight']
    
    # Get latest profile for unit preference
    unit_preference = 'kg'  # default
    try:
        profiles = db.collection('profile_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(1)\
            .stream()
        
        profile_list = list(profiles)
        if profile_list:
            profile = profile_list[0].to_dict()
            # Store unit preference (we'll default to kg from update_profile)
            unit_preference = profile.get('unit_preference', 'kg')
    except Exception as e:
        print(f"Error fetching profile: {e}")
    
    # Fetch calories logged
    total_calories = 0
    try:
        calorie_logs = db.collection('calorie_logs')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .stream()
        total_calories = sum(log.to_dict().get('calories', 0) for log in calorie_logs)
    except Exception:
        pass
    
    # Also sum from workouts for backwards compatibility
    workouts = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    total_calories += sum(workout.to_dict().get('calories_burned', 0) for workout in workouts)
    
    current_weight = weight_data[-1]['weight'] if weight_data else None
    weight_lost = (initial_weight - current_weight) if (initial_weight and current_weight) else 0
    
    # Calculate goal progress
    goal_progress, goal_remaining, target_weight = calculate_goal_progress(db, user_id, current_weight) if current_weight else (0, 0, None)
    
    # Calculate workout streak
    workout_streak = calculate_workout_streak(db, user_id)
    
    # Build recent activity feed from weight and workout logs
    recent_activities = []
    
    recent_weights = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    weight_list = [w.to_dict() for w in recent_weights]
    weight_list.sort(key=lambda x: x['date'], reverse=True)
    
    for data in weight_list[:3]:
        recent_activities.append({
            'icon': '⚖️',
            'title': 'Logged Weight',
            'description': f"{data['weight']} {unit_preference}",
            'time': format_timesince(data['date'])
        })
    
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
    
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    user_email = session.get('email') or session.get('user_id') or ''
    if user_email and '@' in user_email:
        user_name = user_email.split('@')[0]
    else:
        user_name = user_email or 'User'

    # Generate basic achievement badges
    badges = []
    unlocked_count = 0
    achievement_definitions = [
        {'name': 'First Steps', 'icon': '👟', 'requirement': 'weight_logged', 'value': 1},
        {'name': 'On a Roll', 'icon': '💪', 'requirement': 'weight_lost', 'value': 5},
        {'name': '10% There', 'icon': '🎯', 'requirement': 'goal_progress', 'value': 10},
        {'name': '25% Victory', 'icon': '🏅', 'requirement': 'goal_progress', 'value': 25},
        {'name': 'Half Way!', 'icon': '🔥', 'requirement': 'goal_progress', 'value': 50},
        {'name': 'Goal Crushed!', 'icon': '🏆', 'requirement': 'goal_progress', 'value': 100},
    ]
    
    for badge_def in achievement_definitions:
        unlocked = False
        progress = "Locked"
        
        if badge_def['requirement'] == 'weight_logged':
            unlocked = len(weight_data) >= badge_def['value']
            progress = f"{len(weight_data)}/{badge_def['value']} weights"
        elif badge_def['requirement'] == 'weight_lost':
            unlocked = weight_lost >= badge_def['value']
            progress = f"{weight_lost:.1f}/{badge_def['value']} {unit_preference}"
        elif badge_def['requirement'] == 'goal_progress':
            unlocked = goal_progress >= badge_def['value']
            progress = f"{goal_progress:.0f}%"
        
        badges.append({
            'name': badge_def['name'],
            'icon': badge_def['icon'],
            'unlocked': unlocked,
            'progress': progress,
            'date': 'Recently' if unlocked else None
        })
        
        if unlocked:
            unlocked_count += 1

    # Fetch avatar points and calculate level
    avatar_points = 0
    avatar_level = 1
    avatar_progress = 0
    try:
        avatar_doc = db.collection('avatars').document(user_id).get()
        if avatar_doc.exists:
            avatar_data = avatar_doc.to_dict()
            avatar_points = int(avatar_data.get('points', 0) or 0)
            points_per_level = 100
            avatar_level = (avatar_points // points_per_level) + 1
            avatar_progress = (avatar_points % points_per_level) / points_per_level * 100
    except Exception as e:
        print(f"Error fetching avatar: {e}")

    # Fetch user's daily tasks
    tasks_completed = 0
    tasks_total = 0
    try:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        task_list = []
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_list.append(task_data)
            tasks_total += 1
            if task_data.get('completed', False):
                tasks_completed += 1
    except Exception as e:
        print(f"Error fetching tasks: {e}")

    # Generate motivational messages
    motivational_messages = generate_motivational_messages(
        user_name, avatar_points, weight_lost, goal_progress, 
        workout_streak, tasks_completed, tasks_total
    )

    return render_template('dashboard.html',
        user_name=user_name,
        current_weight=current_weight,
        current_weight_unit=unit_preference,
        weight_lost=round(weight_lost, 1),
        weight_lost_unit=unit_preference,
        last_updated="Recently" if weight_data else "No data",
        calories_burned=total_calories,
        daily_calorie_goal=2000,
        workout_streak=workout_streak,
        goal_progress=goal_progress,
        goal_remaining=round(goal_remaining, 1) if goal_remaining else 0,
        target_weight=target_weight,
        selected_timeframe='30d',
        weight_data=weight_data[-7:],
        max_weight=max([w['weight'] for w in weight_data]) if weight_data else 1,
        badges=badges,
        unlocked_badges=unlocked_count,
        total_badges=len(badges),
        recent_activities=recent_activities[:5],
        avatar_points=avatar_points,
        avatar_level=avatar_level,
        avatar_progress=avatar_progress,
        tasks_completed=tasks_completed,
        tasks_total=tasks_total,
        motivational_messages=motivational_messages
    )

@dashboard_bp.route('/log_weight', methods=['GET', 'POST'])
def log_weight():
    # Record a new weight entry for the logged-in user.
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

@dashboard_bp.route('/log_calories', methods=['GET', 'POST'])
def log_calories():
    # Log daily calories burned or eaten.
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        try:
            calories = float(request.form['calories'])
            calorie_type = request.form.get('calorie_type', 'burned').strip()
            notes = request.form.get('notes', '').strip()
            
            if calories < 0:
                flash('Please enter a valid calorie amount.', 'error')
                return render_template('log_calories.html')

            calorie_entry = {
                'user_id': session['user_id'],
                'calories': calories,
                'calorie_type': calorie_type,  # 'burned' or 'consumed'
                'notes': notes,
                'date': datetime.utcnow()
            }

            db.collection('calorie_logs').add(calorie_entry)
            flash('Calories logged successfully!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        except ValueError:
            flash('Please enter a valid calorie number.', 'error')
    
    return render_template('log_calories.html')

@dashboard_bp.route('/log_workout', methods=['GET', 'POST'])
def log_workout():
    # Record a new workout session with duration and calories.
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

@dashboard_bp.route('/set_goal', methods=['GET', 'POST'])
def set_goal():
    # Create or update user weight loss goal with target and deadline.
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

@dashboard_bp.route('/update_profile', methods=['GET', 'POST'])
def update_profile():
    # Comprehensive profile update with weight, height, age, goals, and BMI calculation.
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
            
            # Calculate BMI from weight and height
            height_meters = height_cm / 100.0
            bmi = current_weight / (height_meters ** 2)
            
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
            
            # Save profile snapshot to history
            db.collection('profile_entries').add(profile_data)
            
            # Also create weight entry for chart tracking
            weight_entry = {
                'user_id': user_id,
                'weight': current_weight,
                'notes': f"Profile update - BMI: {bmi:.1f}, Height: {height_cm}cm",
                'date': datetime.utcnow()
            }
            db.collection('weight_entries').add(weight_entry)
            
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
