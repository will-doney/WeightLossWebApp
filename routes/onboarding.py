from flask import Blueprint, render_template, request, session, redirect, url_for

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboard')

def _init_onboard():
    if 'onboarding' not in session:
        session['onboarding'] = {}

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
        return redirect(url_for('auth.signup'))
    return render_template('onboarding/planready.html')

@onboarding_bp.route('/welcome')
def welcome():
    return render_template('welcome.html')

@onboarding_bp.route('/homeintro')
def homeintro():
    return render_template('homeintro.html')
