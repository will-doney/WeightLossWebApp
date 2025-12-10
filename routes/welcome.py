# routes/welcome.py
from flask import Blueprint, render_template

welcome_bp = Blueprint('welcome', __name__)

@welcome_bp.route('/welcome')
def welcome():
    return render_template('homeintro.html')
