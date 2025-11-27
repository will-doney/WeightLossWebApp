# Authentication Routes Module
# ============================
# Handles user authentication using Firebase Authentication.
# Provides login, signup, logout, and session management.

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase_admin import auth
from datetime import datetime, UTC

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Handle user login with Firebase ID token verification.
    # Creates or updates user document in Firestore on successful login.
    
    # Redirect if already logged in
    if session.get('user_id'):
        return redirect(url_for('dashboard.dashboard'))
    
    from app import get_db
    db = get_db()
    
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify Firebase ID token and extract user info
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                session['user_id'] = uid
                session['email'] = email
                
                if db:
                    user_ref = db.collection('users').document(uid)
                    user_doc = user_ref.get()
                    
                    # Create user document if first login
                    if not user_doc.exists:
                        user_data = {
                            'email': email,
                            'created_at': datetime.utcnow(),
                            'avatar': 'default.png',
                            'is_active': True,
                            'onboarding_completed': False
                        }
                        user_ref.set(user_data)
                        try:
                            # Initialize avatar points for gamification
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
        
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase login button', 'info')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    # Handle user registration with Firebase ID token.
    # Creates new user document in Firestore on successful signup.
    
    # Redirect if already logged in
    if session.get('user_id'):
        return redirect(url_for('dashboard.dashboard'))
    
    from app import get_db
    db = get_db()
    
    if request.method == 'POST':
        id_token = request.form.get('idToken')
        
        if id_token:
            try:
                # Verify token and create new user session
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email', '')
                
                session['user_id'] = uid
                session['email'] = email
                
                if db:
                    user_data = {
                        'email': email,
                        'created_at': datetime.now(UTC),
                        'avatar': 'default.png',
                        'is_active': True,
                        'onboarding_completed': False
                    }
                    db.collection('users').document(uid).set(user_data)
                
                # Initialize avatar points
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
                
                # Redirect to onboarding for new users
                return jsonify({'success': True, 'redirect': url_for('onboarding.goal')})
            except Exception as e:
                print(f"Firebase Auth error: {e}")
                return jsonify({'success': False, 'error': 'Registration failed'})
        
        # Handle form-based fallback (if JavaScript fails)
        email = request.form.get('email', '').strip()
        if email:
            flash('Please use the Firebase signup button', 'info')
    
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    # Clear user session and redirect to home page.
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route('/api/check_auth', methods=['GET'])
def check_auth():
    # API endpoint to check if user is authenticated.
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'user_id': session['user_id']})
    return jsonify({'authenticated': False})
