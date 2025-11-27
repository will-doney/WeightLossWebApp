# Main Routes Module
# ==================
# Handles the home page and error handlers for the application.

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Display the landing page with login/signup options.
    return render_template('home.html')

@main_bp.app_errorhandler(404)
def page_not_found(e):
    # Handle 404 Not Found errors with custom page.
    return render_template('404.html'), 404
