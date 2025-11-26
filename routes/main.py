"""
Main Routes
===========
Handles home page and error pages.
"""

from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


# ============================================================
# ROUTE: Home Page
# ============================================================
@main_bp.route('/')
def home():
    """Display the home/landing page."""
    return render_template('home.html')


# ============================================================
# ERROR HANDLERS
# ============================================================
@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Handle 404 Not Found errors with custom page."""
    return render_template('404.html'), 404
