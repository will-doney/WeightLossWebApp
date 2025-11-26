"""
Avatar and Settings Routes
===========================
Handles avatar customization and user settings.
"""

from flask import Blueprint, render_template, request, session, jsonify
from datetime import datetime

other_bp = Blueprint('other', __name__)


# ============================================================
# ROUTE: User Settings
# ============================================================
@other_bp.route('/settings')
def settings():
    """Display user preferences and settings."""
    return render_template('settings.html')


# ============================================================
# ROUTE: Avatar Customization
# ============================================================
@other_bp.route('/myavatar')
def myavatar():
    """Display avatar customization page."""
    return render_template('myavatar.html')


# ============================================================
# API: Persist Avatar Points (POST)
# ============================================================
@other_bp.route('/api/avatar/points', methods=['POST'])
def avatar_points_api():
    """Persist avatar points for authenticated user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json(silent=True) or {}
    try:
        points = int(data.get('points', 0))
    except Exception:
        return jsonify({'error': 'Invalid points value'}), 400

    uid = session['user_id']
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500

    try:
        db.collection('avatars').document(uid).set({
            'user_id': uid,
            'points': points,
            'updated_at': datetime.utcnow()
        }, merge=True)
        return jsonify({'ok': True})
    except Exception as e:
        print(f"Error saving avatar points for {uid}: {e}")
        return jsonify({'error': 'db_error'}), 500


# ============================================================
# API: Get Avatar Points (GET)
# ============================================================
@other_bp.route('/api/avatar/points', methods=['GET'])
def avatar_points_get():
    """Return persisted avatar points for authenticated user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    uid = session['user_id']
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500

    try:
        doc = db.collection('avatars').document(uid).get()
        if doc.exists:
            data = doc.to_dict() or {}
            return jsonify({'points': int(data.get('points', 0)), 'updated_at': data.get('updated_at')}), 200
        return jsonify({'points': 0}), 200
    except Exception as e:
        print(f"Error reading avatar points for {uid}: {e}")
        return jsonify({'error': 'db_error'}), 500
