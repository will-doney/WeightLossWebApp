"""
Task Library and Suggestions
=============================
Contains the task library and suggestion algorithm.
"""

from datetime import datetime
import random

# ============================================================
# TASK SUGGESTION LIBRARY
# ============================================================
TASK_LIBRARY = {
    'beginner_cardio': [
        {'name': '10-minute walk', 'description': 'Light walk around the neighborhood or on a treadmill'},
        {'name': '5-minute stretching', 'description': 'Full body stretching routine to improve flexibility'},
        {'name': 'Chair exercises', 'description': '10 minutes of seated exercises for low-impact movement'},
        {'name': 'Water aerobics', 'description': 'Join a water aerobics class or swim laps at easy pace'},
    ],
    'intermediate_cardio': [
        {'name': '20-minute brisk walk', 'description': 'Power walk at moderate pace, maintain steady breathing'},
        {'name': '15-minute cycling', 'description': 'Outdoor bike ride or stationary bike at moderate resistance'},
        {'name': 'Dance workout', 'description': 'Follow a 20-minute dance workout video'},
        {'name': 'Swimming laps', 'description': 'Swim continuous laps for 15-20 minutes'},
    ],
    'advanced_cardio': [
        {'name': '30-minute run', 'description': 'Running or jogging at challenging pace'},
        {'name': 'HIIT workout', 'description': '20-minute high-intensity interval training session'},
        {'name': 'Jump rope', 'description': '15 minutes of jump rope intervals'},
        {'name': 'Cycling intervals', 'description': '30 minutes with high-intensity intervals'},
    ],
    'beginner_strength': [
        {'name': 'Wall push-ups', 'description': 'Complete 2 sets of 10 wall push-ups'},
        {'name': 'Bodyweight squats', 'description': 'Do 2 sets of 10 squats with proper form'},
        {'name': 'Plank hold', 'description': 'Hold plank position for 20-30 seconds, 2 sets'},
    ],
    'intermediate_strength': [
        {'name': 'Push-up routine', 'description': 'Complete 3 sets of 15 push-ups'},
        {'name': 'Dumbbell workout', 'description': '20-minute routine with light weights'},
        {'name': 'Bodyweight circuit', 'description': 'Squats, lunges, planks - 3 rounds'},
    ],
    'advanced_strength': [
        {'name': 'Weight training', 'description': '45-minute gym session with compound lifts'},
        {'name': 'Advanced calisthenics', 'description': 'Pull-ups, dips, pistol squats routine'},
        {'name': 'CrossFit WOD', 'description': 'Complete today\'s workout of the day'},
    ],
    'nutrition': [
        {'name': 'Drink 2 liters of water', 'description': 'Track and complete daily water intake goal'},
        {'name': 'Meal prep Sunday', 'description': 'Prepare healthy meals for the week ahead'},
        {'name': 'No sugar challenge', 'description': 'Avoid added sugars for the entire day'},
        {'name': 'Vegetable servings', 'description': 'Eat at least 5 servings of vegetables today'},
        {'name': 'Protein goal', 'description': 'Meet your daily protein target (track in app)'},
    ],
    'recovery': [
        {'name': 'Yoga session', 'description': '15-minute yoga for flexibility and recovery'},
        {'name': '8 hours sleep', 'description': 'Prioritize getting 8 hours of quality sleep tonight'},
        {'name': 'Foam rolling', 'description': '10 minutes of foam rolling major muscle groups'},
        {'name': 'Meditation', 'description': '10-minute mindfulness or meditation session'},
    ],
    'lifestyle': [
        {'name': 'Take the stairs', 'description': 'Use stairs instead of elevator all day'},
        {'name': 'Stand up hourly', 'description': 'Set timer to stand and stretch every hour'},
        {'name': 'Walking meeting', 'description': 'Take a phone call while walking'},
        {'name': 'Park farther away', 'description': 'Park in the farthest spot for extra steps'},
    ]
}


def get_task_suggestions(db, user_id, existing_task_names=None):
    """Generate personalized task suggestions based on user profile.
    Filters out tasks that the user already has."""
    from firebase_admin import firestore
    
    if existing_task_names is None:
        existing_task_names = set()
    else:
        # Normalize task names for comparison (case-insensitive)
        existing_task_names = {name.lower().strip() for name in existing_task_names}
    
    if not db:
        return []
    
    # Get user's latest profile
    profiles = db.collection('profile_entries')\
        .where(filter=firestore.FieldFilter('user_id', '==', user_id))\
        .stream()
    
    profile_list = [p.to_dict() for p in profiles]
    if not profile_list:
        # No profile yet - return beginner tasks
        default_suggestions = [
            TASK_LIBRARY['beginner_cardio'],
            TASK_LIBRARY['nutrition'],
            TASK_LIBRARY['beginner_strength'],
            TASK_LIBRARY['lifestyle']
        ]
        # Flatten and filter out existing tasks
        all_defaults = []
        for category in default_suggestions:
            all_defaults.extend(category)
        
        filtered = [task for task in all_defaults if task['name'].lower().strip() not in existing_task_names]
        return filtered[:4] if len(filtered) >= 4 else filtered
    
    # Sort by timestamp to get latest
    profile_list.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
    profile = profile_list[0]
    
    suggestions = []
    
    # Determine fitness level from activity_level
    activity_level = profile.get('activity_level', 'sedentary').lower()
    bmi = profile.get('bmi', 25)
    age = profile.get('age', 30)
    weekly_goal = profile.get('weekly_goal', 0.5)
    
    # Map activity level to fitness level
    if activity_level in ['sedentary', 'lightly_active']:
        fitness_level = 'beginner'
    elif activity_level in ['moderately_active']:
        fitness_level = 'intermediate'
    else:
        fitness_level = 'advanced'
    
    # Adjust for BMI (safety first)
    if bmi > 30:
        fitness_level = 'beginner'
    elif bmi > 27 and fitness_level == 'advanced':
        fitness_level = 'intermediate'
    
    # Adjust for age (safety considerations)
    if age > 60:
        fitness_level = 'beginner'
    elif age > 50 and fitness_level == 'advanced':
        fitness_level = 'intermediate'
    
    # Select cardio tasks (filter out existing, then pick randomly)
    cardio_key = f'{fitness_level}_cardio'
    available_cardio = [task for task in TASK_LIBRARY[cardio_key] if task['name'].lower().strip() not in existing_task_names]
    if available_cardio:
        suggestions.append(random.choice(available_cardio))
    
    # Select strength tasks
    strength_key = f'{fitness_level}_strength'
    available_strength = [task for task in TASK_LIBRARY[strength_key] if task['name'].lower().strip() not in existing_task_names]
    if available_strength:
        suggestions.append(random.choice(available_strength))
    
    # Always include nutrition (essential for weight loss)
    available_nutrition = [task for task in TASK_LIBRARY['nutrition'] if task['name'].lower().strip() not in existing_task_names]
    if available_nutrition:
        suggestions.append(random.choice(available_nutrition))
    
    # Add recovery or lifestyle based on weekly goal intensity
    if weekly_goal >= 0.75:
        # Aggressive goal - need recovery
        available_recovery = [task for task in TASK_LIBRARY['recovery'] if task['name'].lower().strip() not in existing_task_names]
        if available_recovery:
            suggestions.append(random.choice(available_recovery))
    else:
        # Moderate goal - add lifestyle task
        available_lifestyle = [task for task in TASK_LIBRARY['lifestyle'] if task['name'].lower().strip() not in existing_task_names]
        if available_lifestyle:
            suggestions.append(random.choice(available_lifestyle))
    
    return suggestions
