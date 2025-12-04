# Main Routes Module
# ==================
# Handles the home page and error handlers for the application.

from flask import Blueprint, render_template, redirect, url_for, session

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Display the home page for logged-in users.
    # Redirect to login if not authenticated
    if not session.get('user_id'):
        return redirect(url_for('auth.login'))
    return render_template('home.html')

@main_bp.app_errorhandler(404)
def page_not_found(e):
    # Handle 404 Not Found errors with custom page.
    return render_template('404.html'), 404
