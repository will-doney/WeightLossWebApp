# Home Routes Module
# ==================

from flask import Blueprint, render_template, redirect, url_for, session, jsonify, flash
from firebase_admin import firestore
from datetime import datetime
import random

home_bp = Blueprint('home', __name__)

# ============================================================
# COPY ALL HELPER FUNCTIONS FROM dashboard.py
# ============================================================

def format_timesince(dt):
    from datetime import timezone
    
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
    
    # Weight loss message
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
    
    return messages[:3]

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
            return 0
        
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

# ============================================================
# MAIN HOME ROUTE - COPIED FROM DASHBOARD BUT SIMPLIFIED
# ============================================================

@home_bp.route('/')
def home():
    """Home page - uses EXACT SAME data fetching as dashboard"""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        flash('Please login to access the home page', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    if not db:
        flash('Database connection unavailable. Please try again later.', 'error')
        return render_template('home.html',
            user_name='User',
            current_weight=None,
            weight_lost=0,
            calories_burned=0,
            workout_streak=0,
            avatar_points=0,
            avatar_level=1,
            avatar_progress=0,
            tasks_completed=0,
            tasks_total=0,
            motivational_messages=[],
            motivational_message="Let's start crushing those fitness goals today! 💪",
            today_date=datetime.now().strftime('%A, %B %d'),
            tasks=[],
            weight_data=[],
            max_weight=1,
            badges=[],
            unlocked_badges=0,
            total_badges=0,
            steps=0,
            water_intake=0,
            exercise_minutes=0,
            weekly_tasks_completed=0,
            weekly_points=0,
            weekly_workouts=0,
            weekly_calories=0,
            weekly_goal_percentage=0,
            current_week=datetime.now().isocalendar()[1]
        )
    
    # ============================================================
    # DIRECT COPY FROM dashboard.py dashboard() function
    # (with minor simplifications for home page)
    # ============================================================
    
    # 1. Fetch weight entries
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
    
    # 2. Fetch profile
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
            
            if profile_initial_weight and target_weight and profile_initial_weight > target_weight and current_weight:
                total_to_lose = profile_initial_weight - target_weight
                already_lost = profile_initial_weight - current_weight
                goal_progress = min(100, max(0, (already_lost / total_to_lose) * 100))
                goal_progress = round(goal_progress, 1)
                goal_remaining = total_to_lose - already_lost
    except Exception as e:
        print(f"Error fetching profile: {e}")
    
    # 3. Fetch workouts
    workouts_ref = db.collection('workouts')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    workout_list = [w.to_dict() for w in workouts_ref]
    
    # Calculate calories from workouts
    workout_calories = sum(w.get('calories_burned', 0) for w in workout_list)
    
    # Calculate workout streak
    workout_streak = 0
    workout_dates = set()
    for w in workout_list:
        if 'date' in w:
            workout_dates.add(w['date'].date())
    
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
    
    # 5. Get user name
    user_name = session.get('display_name')
    if not user_name:
        user_email = session.get('email') or session.get('user_id') or ''
        if user_email and '@' in user_email:
            user_name = user_email.split('@')[0]
        else:
            user_name = user_email or 'User'

    # 6. Fetch avatar and calculate level
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

    # 7. Fetch tasks
    tasks_completed = 0
    tasks_total = 0
    tasks = []
    try:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_data['id'] = task_doc.id
            tasks.append(task_data)
            tasks_total += 1
            if task_data.get('completed', False):
                tasks_completed += 1
    except Exception as e:
        print(f"Error fetching tasks: {e}")

    # 8. Calculate avatar milestones
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
    
    # 9. Build badges from avatar milestones
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

    # 10. Generate motivational messages
    motivational_messages = generate_motivational_messages(
        user_name, avatar_points, weight_lost, goal_progress, 
        workout_streak, tasks_completed, tasks_total, avatar_milestones
    )
    
    # Select a random message for initial display
    if motivational_messages:
        motivational_message = random.choice(motivational_messages)
    else:
        motivational_message = "Let's start crushing those fitness goals today! 💪"

    # 11. Today's date and other stats
    today_date = datetime.now().strftime('%A, %B %d')
    current_week = datetime.now().isocalendar()[1]
    
    # Weekly stats (simplified)
    weekly_tasks_completed = tasks_completed
    weekly_points = avatar_points
    weekly_workouts = len([w for w in workout_list if w.get('date') and (datetime.utcnow().date() - w['date'].date()).days < 7])
    weekly_calories = sum(w.get('calories_burned', 0) for w in workout_list if w.get('date') and (datetime.utcnow().date() - w['date'].date()).days < 7)
    weekly_goal_percentage = min(100, (tasks_completed / max(tasks_total, 1)) * 100)
    
    # Other stats (you can expand these)
    steps = 0  # Add step tracking if you have it
    water_intake = 0  # Add water tracking if you have it
    exercise_minutes = sum(w.get('duration', 0) for w in workout_list if w.get('date') and (datetime.utcnow().date() - w['date'].date()).days == 0)
    
    # Sort tasks by completion status
    tasks.sort(key=lambda x: (not x.get('completed', False), x.get('name', '')))
    
    return render_template('home.html',
        # Core user data
        user_name=user_name,
        
        # Stats for hero
        workout_streak=workout_streak,
        avatar_points=avatar_points,
        tasks_completed=tasks_completed,
        tasks_total=tasks_total,
        
        # Avatar data
        avatar_level=avatar_level,
        avatar_progress=avatar_progress,
        
        # Weight data
        current_weight=current_weight,
        weight_lost=round(weight_lost, 1),
        starting_weight=initial_weight,
        target_weight=target_weight,
        weight_data=weight_data[-7:],  # Last 7 days
        max_weight=max([w['weight'] for w in weight_data]) if weight_data else 1,
        
        # Today's stats
        calories_burned=total_calories,
        steps=steps,
        water_intake=water_intake,
        exercise_minutes=exercise_minutes,
        today_date=today_date,
        
        # Tasks
        tasks=tasks[:5],  # Show only 5 tasks on home
        
        # Achievements
        unlocked_badges=unlocked_count,
        total_badges=total_count,
        badges=badges[:4],  # Show only 4 badges
        
        # Weekly stats
        weekly_tasks_completed=weekly_tasks_completed,
        weekly_points=weekly_points,
        weekly_workouts=weekly_workouts,
        weekly_calories=weekly_calories,
        weekly_goal_percentage=weekly_goal_percentage,
        current_week=current_week,
        
        # Motivational message
        motivational_message=motivational_message,
        
        # Additional data for template
        motivational_messages=motivational_messages
    )

# API endpoint for avatar messages
@home_bp.route('/api/avatar/message')
def get_avatar_message():
    """API endpoint to get a random motivational message"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    from app import get_db
    db = get_db()
    user_id = session['user_id']
    
    if not db:
        return jsonify({'message': 'Keep pushing forward! 🚀'})
    
    try:
        # Fetch user data for personalized messages
        weight_lost = 0
        avatar_points = 0
        workout_streak = 0
        
        # Get weight data
        weight_entries = db.collection('weight_entries')\
            .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
            .stream()
        
        weight_list = [entry.to_dict() for entry in weight_entries]
        if weight_list and len(weight_list) > 1:
            weight_list.sort(key=lambda x: x['date'])
            initial_weight = weight_list[0]['weight']
            current_weight = weight_list[-1]['weight']
            weight_lost = initial_weight - current_weight
        
        # Get avatar points
        avatar_doc = db.collection('avatars').document(user_id).get()
        if avatar_doc.exists:
            avatar_data = avatar_doc.to_dict()
            avatar_points = int(avatar_data.get('points', 0) or 0)
        
        # Get workout streak
        workout_streak = calculate_workout_streak(db, user_id)
        
        # Generate messages based on user data
        messages = []
        
        # Weight loss messages
        if weight_lost >= 10:
            messages.append("Incredible weight loss journey! You're an inspiration! 🌟")
        elif weight_lost >= 5:
            messages.append("Amazing progress on your weight loss goals! 🎉")
        elif weight_lost > 0:
            messages.append(f"Great work! You've lost {weight_lost:.1f} kg so far! 💪")
        
        # Points messages
        if avatar_points >= 500:
            messages.append(f"WOW! {avatar_points} points! You're crushing it! 🔥")
        elif avatar_points >= 200:
            messages.append(f"Excellent! {avatar_points} points earned! Keep it up! ⭐")
        elif avatar_points >= 50:
            messages.append(f"Great progress with {avatar_points} points! 🎯")
        
        # Streak messages
        if workout_streak >= 7:
            messages.append(f"{workout_streak}-day workout streak! You're unstoppable! 💥")
        elif workout_streak >= 3:
            messages.append(f"Nice {workout_streak}-day streak! Consistency is key! 🔑")
        
        # General motivational messages
        general_messages = [
            "Every small step brings you closer to your goals! 👣",
            "Your dedication is inspiring! Keep going! 🌟",
            "Don't forget to stay hydrated today! 💧",
            "Celebrate every victory, no matter how small! 🎉",
            "Your future self will thank you for this! 🙏",
            "Remember: progress, not perfection! 📈",
            "You're stronger than you think! 💥",
            "Today is a great day to make progress! ☀️",
            "Keep pushing forward! You've got this! 🚀",
            "One day at a time, one step at a time! 🕒",
            "Believe in yourself and all that you are! ✨",
            "The only bad workout is the one that didn't happen! 🏋️",
            "You're building habits that will last a lifetime! 🌱",
            "Stay focused and trust the process! 📊",
            "You have the power to create change! ⚡"
        ]
        
        # Add some general messages if we don't have enough personalized ones
        messages.extend(general_messages)
        
        # Select a random message
        selected_message = random.choice(messages)
        
        return jsonify({
            'message': selected_message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        print(f"Error fetching avatar message: {e}")
        return jsonify({
            'message': "Keep crushing your fitness goals! 💪",
            'error': str(e)
        })

# Simple API for real-time updates
@home_bp.route('/api/home/stats')
def home_stats():
    """Simple API for real-time updates"""
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
    
    from app import get_db
    db = get_db()
    user_id = session['user_id']
    
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500
    
    try:
        # Get tasks
        tasks_completed = 0
        tasks_total = 0
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            tasks_total += 1
            if task_data.get('completed', False):
                tasks_completed += 1
        
        # Get avatar points
        avatar_points = 0
        avatar_doc = db.collection('avatars').document(user_id).get()
        if avatar_doc.exists:
            avatar_data = avatar_doc.to_dict()
            avatar_points = int(avatar_data.get('points', 0) or 0)
        
        # Get workout streak
        workout_streak = calculate_workout_streak(db, user_id)
        
        return jsonify({
            'streak': workout_streak,
            'points': avatar_points,
            'tasks': {
                'completed': tasks_completed,
                'total': tasks_total
            }
        })
        
    except Exception as e:
        print(f"Error in home stats API: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500