# Dashboard Routes Module
# =======================
# Handles user dashboard, profile management, and activity tracking.
# Provides weight logging, workout tracking, goals, and profile updates.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
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
                                   workout_streak, tasks_completed, tasks_total, avatar_milestones=None):
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
    
    # Weight loss message (without numbers)
    if weight_lost >= 10:
        messages.append(f"Amazing progress! Keep up the great work! 🎉")
    elif weight_lost >= 5:
        messages.append(f"Excellent progress! You're doing fantastic! ✨")
    elif weight_lost > 0:
        messages.append(f"You're making great progress! Keep it up! 👍")
    
    # Goal progress message
    if goal_progress >= 75:
        messages.append(f"Almost there! You're crushing your goals! 🚀")
    elif goal_progress >= 50:
        messages.append(f"You're halfway there! Amazing work! 🎯")
    elif goal_progress >= 25:
        messages.append(f"Great start! You're on the right track! 📈")
    
    # Workout streak message
    if workout_streak >= 30:
        messages.append(f"Incredible workout consistency! 🏆")
    elif workout_streak >= 7:
        messages.append(f"Amazing workout streak! 💪")
    elif workout_streak >= 3:
        messages.append(f"Nice streak! Keep it up! 🔥")
    elif workout_streak > 0:
        messages.append(f"You're building a great habit! 💯")
    
    # Task completion message
    if tasks_total > 0:
        completion_rate = (tasks_completed / tasks_total) * 100
        if completion_rate >= 90:
            messages.append(f"Tasks crushed! Outstanding work! 🎊")
        elif completion_rate >= 75:
            messages.append(f"Excellent task completion! 📋")
        elif completion_rate >= 50:
            messages.append(f"Good work on completing tasks! ✅")
        elif tasks_completed > 0:
            messages.append(f"Keep completing those tasks! 🚀")
    
    # Avatar milestone messages
    if avatar_milestones:
        latest_unlocked = [m for m in avatar_milestones if m.get('unlocked')]
        if latest_unlocked:
            latest = latest_unlocked[0]
            if latest['name'] == 'Legend':
                messages.append(f"Legend status achieved! Ultimate milestone unlocked! 👑")
            elif latest['name'] == 'Halfway Hero':
                messages.append(f"Halfway hero! You're unstoppable! 🏅")
            elif latest['name'] == 'Committed':
                messages.append(f"Total commitment! You're dedicated! 🥇")
    
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


def get_avatar_milestones(db, user_id):
    """Get user's avatar milestones with progress tracking."""
    try:
        # First get avatar points
        avatar_doc = db.collection('avatars').document(user_id).get()
        avatar_points = 0
        if avatar_doc.exists:
            avatar_data = avatar_doc.to_dict()
            avatar_points = int(avatar_data.get('points', 0) or 0)
        
        # Define milestone thresholds and badges
        milestone_definitions = [
            {'name': 'First Steps', 'points_required': 50, 'badge': 'Bronze', 'icon': '🥉'},
            {'name': 'On The Move', 'points_required': 100, 'badge': 'Silver', 'icon': '🥈'},
            {'name': 'Committed', 'points_required': 250, 'badge': 'Gold', 'icon': '🥇'},
            {'name': 'Halfway Hero', 'points_required': 500, 'badge': 'Platinum', 'icon': '🏅'},
            {'name': 'Legend', 'points_required': 1000, 'badge': 'Diamond', 'icon': '👑'},
        ]
        
        # Check which milestones are achieved
        milestones = []
        for milestone in milestone_definitions:
            points_required = milestone['points_required']
            unlocked = avatar_points >= points_required
            progress_percent = min(100, (avatar_points / points_required) * 100) if points_required > 0 else 0
            
            milestones.append({
                'name': milestone['name'],
                'badge': milestone['badge'],
                'icon': milestone['icon'],
                'unlocked': unlocked,
                'points_required': points_required,
                'current_points': avatar_points,
                'progress_percent': round(progress_percent, 1),
                'progress_display': f"{avatar_points}/{points_required} pts",
                'claimed': unlocked  # Assuming claimed when unlocked for now
            })
        
        return milestones
    except Exception as e:
        print(f"Error fetching avatar milestones: {e}")
        return []


def get_dashboard_achievements(db, user_id, current_weight, initial_weight, target_weight, goal_progress, unit_preference='kg'):
    """Get combined achievements from avatar milestones and weight goals."""
    # Get avatar milestones
    avatar_milestones = get_avatar_milestones(db, user_id)
    
    # Calculate weight lost
    weight_lost = (initial_weight - current_weight) if (initial_weight and current_weight) else 0
    
    # Combine both achievement systems
    combined_achievements = []
    
    # 1. Add avatar-based achievements (mapped to dashboard names)
    milestone_map = {
        'First Steps': {'name': 'First Steps', 'icon': '🥉'},
        'On The Move': {'name': 'On The Move', 'icon': '🥈'},
        'Committed': {'name': 'Committed', 'icon': '🥇'},
        'Halfway Hero': {'name': 'Halfway Hero', 'icon': '🏅'},
        'Legend': {'name': 'Legend', 'icon': '👑'},
    }
    
    for avatar_milestone in avatar_milestones:
        if avatar_milestone['name'] in milestone_map:
            mapped = milestone_map[avatar_milestone['name']]
            combined_achievements.append({
                'name': mapped['name'],
                'icon': mapped['icon'],
                'unlocked': avatar_milestone['unlocked'],
                'progress': avatar_milestone['progress_display'],
                'date': 'Recently' if avatar_milestone['unlocked'] else None,
                'type': 'avatar',
                'source_milestone': avatar_milestone
            })
    
    
    

     
    
    # Sort achievements: unlocked first, then by name
    combined_achievements.sort(key=lambda x: (
        not x['unlocked'],  # Unlocked first
          # Alphabetical
    ))
    
    # Calculate statistics
    unlocked_count = len([a for a in combined_achievements if a['unlocked']])
    total_count = len(combined_achievements)
    
    return combined_achievements, unlocked_count, total_count, avatar_milestones


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
            motivational_messages=[],
            avatar_milestones=[]
        )
    
    # ============================================================
    # OPTIMIZED: Fetch all data in minimal queries, reuse results
    # ============================================================
    
    # 1. Fetch weight entries ONCE
    weight_entries = db.collection('weight_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    weight_list = [entry.to_dict() for entry in weight_entries]
    weight_list.sort(key=lambda x: x['date'])
    
    weight_data = [{
        'weight': data['weight'],
        'date': data['date'],
        'date_formatted': data['date'].strftime('%b %d')
    } for data in weight_list]
    
    initial_weight = weight_data[0]['weight'] if weight_data else None
    current_weight = weight_data[-1]['weight'] if weight_data else None
    weight_lost = (initial_weight - current_weight) if (initial_weight and current_weight) else 0
    
    # 2. Fetch profile ONCE
    unit_preference = 'kg'
    target_weight = None
    goal_progress = 0
    goal_remaining = 0
    try:
        profiles = db.collection('profile_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(1)\
            .stream()
        
        profile_list = list(profiles)
        if profile_list:
            profile = profile_list[0].to_dict()
            unit_preference = profile.get('unit_preference', 'kg')
            target_weight = profile.get('target_weight')
            profile_initial_weight = profile.get('current_weight')
            
            # Calculate goal progress inline
            if profile_initial_weight and target_weight and profile_initial_weight > target_weight and current_weight:
                total_to_lose = profile_initial_weight - target_weight
                already_lost = profile_initial_weight - current_weight
                goal_progress = min(100, max(0, (already_lost / total_to_lose) * 100))
                goal_progress = round(goal_progress, 1)
                goal_remaining = total_to_lose - already_lost
    except Exception as e:
        print(f"Error fetching profile: {e}")
    
    # 3. Fetch workouts ONCE and reuse for calories, streak, and recent activities
    workouts_ref = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    workout_list = [w.to_dict() for w in workouts_ref]
    
    # Calculate calories from workouts
    workout_calories = sum(w.get('calories_burned', 0) for w in workout_list)
    
    # Calculate workout streak from cached data
    workout_dates = set()
    for w in workout_list:
        if 'date' in w:
            workout_dates.add(w['date'].date())
    
    workout_streak = 0
    if workout_dates:
        sorted_dates = sorted(workout_dates, reverse=True)
        today = datetime.utcnow().date()
        if (today - sorted_dates[0]).days <= 1:
            workout_streak = 1
            for i in range(len(sorted_dates) - 1):
                if (sorted_dates[i] - sorted_dates[i + 1]).days == 1:
                    workout_streak += 1
                else:
                    break
    
    # 4. Fetch calorie logs
    total_calories = 0
    try:
        calorie_logs = db.collection('calorie_logs')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .stream()
        total_calories = sum(log.to_dict().get('calories', 0) for log in calorie_logs)
    except Exception:
        pass
    total_calories += workout_calories
    
    # 5. Build recent activities from cached data (no new queries)
    recent_activities = []
    
    # Sort weight list for recent activities (already have the data)
    weight_list_sorted = sorted(weight_list, key=lambda x: x['date'], reverse=True)
    for data in weight_list_sorted[:3]:
        recent_activities.append({
            'icon': '⚖️',
            'title': 'Logged Weight',
            'description': f"{data['weight']} kg",
            'time': format_timesince(data['date'])
        })
    
    # Sort workouts for recent activities (already have the data)
    workout_list_sorted = sorted(workout_list, key=lambda x: x['date'], reverse=True)
    for data in workout_list_sorted[:2]:
        recent_activities.append({
            'icon': '🏃‍♂️',
            'title': data.get('workout_type', 'Workout').title(),
            'description': f"{data.get('duration', 0)} min, {data.get('calories_burned', 0)} cal",
            'time': format_timesince(data['date'])
        })
    
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    
    # 6. Get user name
    user_name = session.get('display_name')
    if not user_name:
        user_email = session.get('email') or session.get('user_id') or ''
        if user_email and '@' in user_email:
            user_name = user_email.split('@')[0]
        else:
            user_name = user_email or 'User'

    # 7. Fetch avatar ONCE and calculate level
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

    # 8. Fetch tasks
    tasks_completed = 0
    tasks_total = 0
    try:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            tasks_total += 1
            if task_data.get('completed', False):
                tasks_completed += 1
    except Exception as e:
        print(f"Error fetching tasks: {e}")

    # 9. Calculate avatar milestones from cached avatar_points (no new query)
    milestone_definitions = [
        {'name': 'First Steps', 'points_required': 50, 'badge': 'Bronze', 'icon': '🥉'},
        {'name': 'On The Move', 'points_required': 100, 'badge': 'Silver', 'icon': '🥈'},
        {'name': 'Committed', 'points_required': 250, 'badge': 'Gold', 'icon': '🥇'},
        {'name': 'Halfway Hero', 'points_required': 500, 'badge': 'Platinum', 'icon': '🏅'},
        {'name': 'Legend', 'points_required': 1000, 'badge': 'Diamond', 'icon': '👑'},
    ]
    
    avatar_milestones = []
    for milestone in milestone_definitions:
        points_required = milestone['points_required']
        unlocked = avatar_points >= points_required
        progress_percent = min(100, (avatar_points / points_required) * 100) if points_required > 0 else 0
        avatar_milestones.append({
            'name': milestone['name'],
            'badge': milestone['badge'],
            'icon': milestone['icon'],
            'unlocked': unlocked,
            'points_required': points_required,
            'current_points': avatar_points,
            'progress_percent': round(progress_percent, 1),
            'progress_display': f"{avatar_points}/{points_required} pts",
            'claimed': unlocked
        })
    
    # 10. Build badges from avatar milestones (no new query)
    badges = []
    for m in avatar_milestones:
        badges.append({
            'name': m['name'],
            'icon': m['icon'],
            'unlocked': m['unlocked'],
            'progress': m['progress_display'],
            'date': 'Recently' if m['unlocked'] else None,
            'type': 'avatar',
            'source_milestone': m
        })
    
    badges.sort(key=lambda x: not x['unlocked'])
    unlocked_count = len([b for b in badges if b['unlocked']])
    total_count = len(badges)

    # 11. Generate motivational messages
    motivational_messages = generate_motivational_messages(
        user_name, avatar_points, weight_lost, goal_progress, 
        workout_streak, tasks_completed, tasks_total, avatar_milestones
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
        total_badges=total_count,
        recent_activities=recent_activities[:5],
        avatar_points=avatar_points,
        avatar_level=avatar_level,
        avatar_progress=avatar_progress,
        tasks_completed=tasks_completed,
        tasks_total=tasks_total,
        motivational_messages=motivational_messages,
        avatar_milestones=avatar_milestones
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
                'weight_to_lose': current_weight - target_weight,
                'unit_preference': 'kg'  # Always kg now
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