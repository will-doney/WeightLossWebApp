# Other Routes Module
# ===================
# Handles settings, avatar customization, and avatar points API.

from flask import Blueprint, render_template, request, session, jsonify
from datetime import datetime
import os
import requests
from firebase_admin import auth as admin_auth

other_bp = Blueprint('other', __name__)

# Static milestone definitions
MILESTONES = [
    {'id': 'm50', 'title': 'First Steps', 'pts': 50, 'reward': 'Bronze Badge'},
    {'id': 'm100', 'title': 'On The Move', 'pts': 100, 'reward': 'Silver Badge'},
    {'id': 'm250', 'title': 'Committed', 'pts': 250, 'reward': 'Gold Badge'},
    {'id': 'm500', 'title': 'Halfway Hero', 'pts': 500, 'reward': 'Platinum Badge'},
    {'id': 'm1000', 'title': 'Legend', 'pts': 1000, 'reward': 'Diamond Badge'}
]

@other_bp.route('/settings')
def settings():
    # Display user preferences and settings page.
    return render_template('settings.html')

@other_bp.route('/myavatar')
def myavatar():
    # Display avatar customization page with points system.
    return render_template('myavatar.html')

@other_bp.route('/api/avatar/points', methods=['POST'])
def avatar_points_api():
    # Save avatar points to Firestore for authenticated user.
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

@other_bp.route('/api/avatar/points', methods=['GET'])
def avatar_points_get():
    # Retrieve avatar points from Firestore for authenticated user.
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


# ============================================================
# API: Milestones & Rewards (GET)
# ============================================================
@other_bp.route('/api/avatar/rewards', methods=['GET'])
def avatar_rewards_get():
    """
    Return milestones (public) and claimed rewards (per-user, if logged in).
    Uses separate 'milestones' collection.
    """
    from app import get_db
    db = get_db()
    uid = session.get('user_id')

    # Base response always includes milestones
    resp = {
        'milestones': MILESTONES,
        'claimed': []
    }

    if not db or not uid:
        return jsonify(resp), 200

    try:
        # Query milestones collection for this user's claimed milestones
        milestones_ref = db.collection('milestones')
        query = milestones_ref.where('user_id', '==', uid)
        docs = query.stream()
        
        claimed_ids = []
        for doc in docs:
            data = doc.to_dict()
            milestone_id = data.get('milestone_id')
            if milestone_id:
                claimed_ids.append(str(milestone_id))
        
        resp['claimed'] = claimed_ids
        return jsonify(resp), 200
        
    except Exception as e:
        print(f"[rewards:get] Error for {uid}: {e}")
        return jsonify(resp), 200


# ============================================================
# API: Claim Reward (POST)
# ============================================================
@other_bp.route('/api/avatar/rewards', methods=['POST'])
def avatar_rewards_post():
    """
    Claim a reward for the current user:
    - Requires authentication
    - Validates milestone ID and required points
    - Creates document in 'milestones' collection
    """
    from app import get_db
    db = get_db()

    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    if not db:
        return jsonify({'error': 'Database unavailable'}), 500

    uid = session['user_id']
    payload = request.get_json(silent=True) or {}
    reward_id = str(payload.get('reward_id', '')).strip()

    # Validate reward ID against server milestones
    milestone = next((m for m in MILESTONES if m['id'] == reward_id), None)
    if not milestone:
        return jsonify({'error': 'invalid_reward_id'}), 400

    try:
        # Check if already claimed in milestones collection
        milestone_doc_id = f"{uid}_{reward_id}"
        milestone_ref = db.collection('milestones').document(milestone_doc_id)
        
        if milestone_ref.get().exists:
            return jsonify({'error': 'already_claimed'}), 409

        # Check user's current points from avatars collection
        avatar_ref = db.collection('avatars').document(uid)
        snap = avatar_ref.get()
        current_points = 0
        if snap.exists:
            data = snap.to_dict() or {}
            current_points = int(data.get('points', 0) or 0)

        # Enough points?
        required = int(milestone['pts'])
        if current_points < required:
            return jsonify({'error': 'insufficient_points', 'required': required, 'have': current_points}), 403

        # Create milestone claim document
        milestone_ref.set({
            'user_id': uid,
            'milestone_id': reward_id,
            'milestone_title': milestone['title'],
            'points_required': required,
            'reward': milestone['reward'],
            'claimed_at': datetime.utcnow()
        })

        return jsonify({'ok': True, 'claimed': reward_id}), 200

    except Exception as e:
        print(f"[rewards:post] Error for {uid}: {e}")
        return jsonify({'error': 'db_error'}), 500


# ============================================================
# API: Account password change (server-side)
# ============================================================
@other_bp.route('/api/account/change_password', methods=['POST'])
def account_change_password():
    """
    Change the user's password server-side by verifying the current password
    with Firebase REST API and then updating via Firebase Admin SDK.

    Expected JSON: { email, current_password, new_password }
    Requires the user to be logged into the Flask session (session['user_id']).
    """
    from app import get_db
    db = get_db()

    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    current = payload.get('current_password') or ''
    new_pwd = payload.get('new_password') or ''

    if not email or not current or not new_pwd:
        return jsonify({'error': 'missing_fields'}), 400

    if len(new_pwd) < 8:
        return jsonify({'error': 'weak_password', 'message': 'Password must be at least 8 characters.'}), 400

    # Use Firebase Identity Toolkit REST API to verify email+password
    # API key should match the Firebase project used by the Admin SDK
    FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY') or 'AIzaSyBn3O0A7K9OEJzFZEFdz4qC6b-PHeAfuD4'
    verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

    try:
        resp = requests.post(verify_url, json={
            'email': email,
            'password': current,
            'returnSecureToken': True
        }, timeout=10)
    except Exception as e:
        print(f"[change_password] REST request error: {e}")
        return jsonify({'error': 'auth_service_unreachable'}), 502

    if resp.status_code != 200:
        # Authentication failed
        try:
            data = resp.json()
            msg = data.get('error', {}).get('message', '')
        except Exception:
            msg = 'invalid_credentials'
        print(f"[change_password] verify failed for {email}: {msg}")
        return jsonify({'error': 'invalid_credentials', 'message': msg}), 401

    data = resp.json()
    uid = data.get('localId')

    # Ensure the session user matches the authenticated Firebase user
    if session.get('user_id') and session.get('user_id') != uid:
        return jsonify({'error': 'session_mismatch'}), 403

    # Update password using Admin SDK
    try:
        admin_auth.update_user(uid, password=new_pwd)
        return jsonify({'ok': True, 'message': 'Password updated.'}), 200
    except Exception as e:
        print(f"[change_password] admin update error for {uid}: {e}")
        return jsonify({'error': 'update_failed', 'message': str(e)}), 500


# ============================================================
# API: Generate password reset link (server-side) and return it
# ============================================================
@other_bp.route('/api/account/send_reset', methods=['POST'])
def account_send_reset():
    """
    Generate a Firebase password reset link for the provided email and
    return it in the response. In production you should send the link
    via your own email provider instead of returning it.

    Expected JSON: { email }
    """
    payload = request.get_json(silent=True) or {}
    email = (payload.get('email') or '').strip()
    if not email:
        return jsonify({'error': 'missing_email'}), 400

    try:
        link = admin_auth.generate_password_reset_link(email)
        # In production, send `link` via email provider. For now return it.
        return jsonify({'ok': True, 'resetLink': link}), 200
    except Exception as e:
        print(f"[send_reset] error generating link for {email}: {e}")
        return jsonify({'error': 'generate_failed', 'message': str(e)}), 500


# ============================================================
# API: Save display name to session and Firestore
# ============================================================
@other_bp.route('/api/account/save_display_name', methods=['POST'])
def save_display_name():
    """
    Save the user's display name to the Flask session and Firestore.
    
    Expected JSON: { displayName }
    Requires the user to be logged into the Flask session (session['user_id']).
    """
    from app import get_db
    db = get_db()

    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    payload = request.get_json(silent=True) or {}
    display_name = (payload.get('displayName') or '').strip()

    if not display_name:
        return jsonify({'error': 'display_name_required'}), 400

    uid = session['user_id']

    # Save to session
    session['display_name'] = display_name
    session.modified = True

    # Save to Firestore
    if db:
        try:
            db.collection('users').document(uid).set({
                'user_id': uid,
                'display_name': display_name,
                'updated_at': datetime.utcnow()
            }, merge=True)
        except Exception as e:
            print(f"[save_display_name] error saving for {uid}: {e}")
            # Still return success since session was saved

    return jsonify({'ok': True, 'display_name': display_name}), 200
