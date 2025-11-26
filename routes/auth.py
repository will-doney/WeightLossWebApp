"""
Authentication Routes
=====================
Handles user login, signup, and logout functionality using Firebase Authentication.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase_admin import auth
from datetime import datetime, UTC

auth_bp = Blueprint('auth', __name__)

# ============================================================
# ROUTE: User Login
# ============================================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login with Firebase Authentication."""
    from app import db
    
    if request.method == 'POST':
        # Get the ID token from the client
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify the ID token
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Store user info in session
                session['user_id'] = uid
                session['email'] = email
                
                # Create or update user document in Firestore
                if db:
                    user_ref = db.collection('users').document(uid)
                    user_doc = user_ref.get()
                    
                    if not user_doc.exists:
                        # Create new user document
                        user_data = {
                            'email': email,
                            'created_at': datetime.utcnow(),
                            'avatar': 'default.png',
                            'is_active': True
                        }
                        user_ref.set(user_data)
                        # Ensure avatar document exists for this user with 0 points
                        try:
                            avatar_ref = db.collection('avatars').document(uid)
                            if not avatar_ref.get().exists:
                                avatar_ref.set({
                                    'user_id': uid,
                                    'points': 0,
                                    'updated_at': datetime.utcnow()
                                })
                        except Exception as e:
                            print(f"Warning: could not create avatar doc for {uid}: {e}")
                
                return jsonify({'success': True, 'redirect': url_for('dashboard.dashboard')})
            except Exception as e:
                print(f"Firebase Auth error: {e}")
                return jsonify({'success': False, 'error': 'Invalid authentication'})
        
        # Handle form-based fallback (if JavaScript fails)
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase login button', 'info')
    
    return render_template('login.html')


# ============================================================
# ROUTE: User Registration
# ============================================================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration with Firebase Authentication."""
    from app import db
    
    if request.method == 'POST':
        # Get the ID token from the client
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify the ID token
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                # Store user info in session
                session['user_id'] = uid
                session['email'] = email
                
                # Create user document in Firestore
                if db:
                    user_data = {
                        'email': email,
                        'created_at': datetime.now(UTC),
                        'avatar': 'default.png',
                        'is_active': True
                    }
                    db.collection('users').document(uid).set(user_data)
                # Ensure avatar doc exists for new signup
                try:
                    avatar_ref = db.collection('avatars').document(uid)
                    if not avatar_ref.get().exists:
                        avatar_ref.set({
                            'user_id': uid,
                            'points': 0,
                            'updated_at': datetime.utcnow()
                        })
                except Exception as e:
                    print(f"Warning: could not create avatar doc for {uid} on signup: {e}")
                
                return jsonify({'success': True, 'redirect': url_for('dashboard.dashboard')})
            except Exception as e:
                print(f"Firebase Auth error: {e}")
                return jsonify({'success': False, 'error': 'Registration failed'})
        
        # Handle form-based fallback (if JavaScript fails)
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase signup button', 'info')
    
    return render_template('signup.html')


# ============================================================
# ROUTE: User Logout
# ============================================================
@auth_bp.route('/logout')
def logout():
    """Clear user session and Firebase auth, redirect to home page."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))


# ============================================================
# API: Check Authentication Status
# ============================================================
@auth_bp.route('/api/check_auth', methods=['GET'])
def check_auth():
    """API endpoint to check if user is authenticated."""
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'user_id': session['user_id']})
    return jsonify({'authenticated': False})
