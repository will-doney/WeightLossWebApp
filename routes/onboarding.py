from flask import Blueprint, render_template, request, session, redirect, url_for
from datetime import datetime

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboard')

def _init_onboard():
    if 'onboarding' not in session:
        session['onboarding'] = {}

def save_onboarding_data(db, user_id):
    """Save onboarding data to Firestore as a profile entry."""
    onboard_data = session.get('onboarding', {})
    
    if not onboard_data:
        return
    
    # Parse and convert onboarding data to profile format
    profile_data = {
        'user_id': user_id,
        'timestamp': datetime.utcnow(),
        'onboarding_source': True
    }
    
    # Add name if provided
    if 'name' in onboard_data:
        profile_data['name'] = onboard_data['name']
    
    # Add sex/gender
    if 'sex' in onboard_data:
        profile_data['sex'] = onboard_data['sex']
    
    # Parse birthday and calculate age
    if 'birthday' in onboard_data:
        try:
            birthday = onboard_data['birthday']
            profile_data['birthday'] = birthday
            # Calculate age
            from datetime import datetime
            birth_date = datetime.strptime(birthday, '%Y-%m-%d')
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            profile_data['age'] = age
        except:
            pass
    
    # Parse height and convert to cm
    if 'height' in onboard_data:
        height_data = onboard_data['height']
        if height_data['unit'] == 'cm':
            height_cm = float(height_data['value'])
        else:  # ft/in
            ft = float(height_data.get('ft', 0))
            inches = float(height_data.get('in', 0))
            height_cm = (ft * 12 + inches) * 2.54
        profile_data['height_cm'] = int(height_cm)
        profile_data['height_meters'] = height_cm / 100.0
    
    # Parse current weight and convert to kg
    if 'weight' in onboard_data:
        weight_data = onboard_data['weight']
        weight_value = float(weight_data['value'])
        if weight_data['unit'] == 'lbs':
            weight_kg = weight_value * 0.453592
        else:
            weight_kg = weight_value
        profile_data['current_weight'] = weight_kg
    
    # Parse goal weight and convert to kg
    if 'goal_weight' in onboard_data:
        goal_data = onboard_data['goal_weight']
        goal_value = float(goal_data['value'])
        if goal_data['unit'] == 'lbs':
            goal_kg = goal_value * 0.453592
        else:
            goal_kg = goal_value
        profile_data['target_weight'] = goal_kg
        
        # Calculate weight to lose
        if 'current_weight' in profile_data:
            profile_data['weight_to_lose'] = profile_data['current_weight'] - goal_kg
    
    # Calculate BMI if we have height and weight
    if 'height_meters' in profile_data and 'current_weight' in profile_data:
        height_m = profile_data['height_meters']
        weight = profile_data['current_weight']
        bmi = weight / (height_m ** 2)
        profile_data['bmi'] = round(bmi, 1)
    
    # Add goal type
    if 'goal' in onboard_data:
        profile_data['goal_type'] = onboard_data['goal']
    
    # Set default activity level and weekly goal
    profile_data['activity_level'] = 'moderately_active'
    profile_data['weekly_goal'] = 0.5
    
    # Save to profile_entries collection
    db.collection('profile_entries').add(profile_data)
    
    # Also create initial weight entry
    if 'current_weight' in profile_data:
        weight_entry = {
            'user_id': user_id,
            'weight': profile_data['current_weight'],
            'notes': 'Initial weight from onboarding',
            'date': datetime.utcnow()
        }
        db.collection('weight_entries').add(weight_entry)
    
    # Create goal entry
    if 'target_weight' in profile_data:
        goal_entry = {
            'user_id': user_id,
            'target_weight': profile_data['target_weight'],
            'deadline': datetime.utcnow(),  # Can be updated later
            'weekly_goal': profile_data.get('weekly_goal', 0.5),
            'created_at': datetime.utcnow(),
            'is_active': True
        }
        db.collection('goals').add(goal_entry)

@onboarding_bp.route('/goal', methods=['GET','POST'])
def goal():
    _init_onboard()
    if request.method == 'POST':
        choice = request.form.get('goal')
        session['onboarding']['goal'] = choice
        session.modified = True
        return redirect(url_for('onboarding.sex'))
    return render_template('onboarding/goal.html')

@onboarding_bp.route('/sex', methods=['GET','POST'])
def sex():
    _init_onboard()
    if request.method == 'POST':
        sex = request.form.get('sex')
        session['onboarding']['sex'] = sex
        session.modified = True
        return redirect(url_for('onboarding.name'))
    return render_template('onboarding/sex.html')

@onboarding_bp.route('/name', methods=['GET','POST'])
def name():
    _init_onboard()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        session['onboarding']['name'] = name
        session.modified = True
        return redirect(url_for('onboarding.nice'))
    return render_template('onboarding/name.html')

@onboarding_bp.route('/nice', methods=['GET','POST'])
def nice():
    _init_onboard()
    name = session['onboarding'].get('name', '')
    if request.method == 'POST':
        return redirect(url_for('onboarding.birthday'))
    return render_template('onboarding/nice.html', name=name)

@onboarding_bp.route('/birthday', methods=['GET','POST'])
def birthday():
    _init_onboard()
    if request.method == 'POST':
        birthday = request.form.get('birthday')
        session['onboarding']['birthday'] = birthday
        session.modified = True
        return redirect(url_for('onboarding.height'))
    return render_template('onboarding/birthdayy.html')

@onboarding_bp.route('/height', methods=['GET','POST'])
def height():
    _init_onboard()
    if request.method == 'POST':
        unit = request.form.get('height_unit')
        if unit == 'cm':
            cm = request.form.get('height_cm')
            session['onboarding']['height'] = {'value': cm, 'unit': 'cm'}
        else:
            ft = request.form.get('height_ft')
            inch = request.form.get('height_in')
            session['onboarding']['height'] = {'value': f"{ft}'{inch}\"", 'unit': 'ftin', 'ft': ft, 'in': inch}
        session.modified = True
        return redirect(url_for('onboarding.weight'))
    return render_template('onboarding/height.html')

@onboarding_bp.route('/weight', methods=['GET','POST'])
def weight():
    _init_onboard()
    if request.method == 'POST':
        unit = request.form.get('weight_unit')
        weight = request.form.get('weight_value')
        session['onboarding']['weight'] = {'value': weight, 'unit': unit}
        session.modified = True
        return redirect(url_for('onboarding.goal_weight'))
    return render_template('onboarding/weight.html')

@onboarding_bp.route('/goal_weight', methods=['GET','POST'])
def goal_weight():
    _init_onboard()
    if request.method == 'POST':
        unit = request.form.get('goal_weight_unit')
        goal = request.form.get('goal_weight_value')
        session['onboarding']['goal_weight'] = {'value': goal, 'unit': unit}
        session.modified = True
        return redirect(url_for('onboarding.plan_ready'))
    return render_template('onboarding/setgoal.html')

@onboarding_bp.route('/plan_ready', methods=['GET','POST'])
def plan_ready():
    _init_onboard()
    if request.method == 'POST':
        # Check if user is logged in
        user_id = session.get('user_id')
        if user_id:
            # User is logged in, save onboarding data now
            from app import get_db
            db = get_db()
            if db:
                try:
                    save_onboarding_data(db, user_id)
                    # Mark onboarding as completed
                    db.collection('users').document(user_id).update({'onboarding_completed': True})
                    # Clear onboarding session data
                    session.pop('onboarding', None)
                    session.modified = True
                    return redirect(url_for('dashboard.dashboard'))
                except Exception as e:
                    print(f"Error saving onboarding data: {e}")
        
        # User not logged in, redirect to signup
        return redirect(url_for('auth.signup'))
    return render_template('onboarding/planready.html')

@onboarding_bp.route('/welcome')
def welcome():
    return render_template('welcome.html')

@onboarding_bp.route('/homeintro')
def homeintro():
    return render_template('homeintro.html')
