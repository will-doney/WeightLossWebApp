"""
Task Management Routes
======================
Handles daily task CRUD operations and API endpoints.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from firebase_admin import firestore
from datetime import datetime
from .task_library import get_task_suggestions

tasks_bp = Blueprint('tasks', __name__)


# ============================================================
# ROUTE: Daily Tasks (HTML)
# ============================================================
@tasks_bp.route('/tasks')
def tasks():
    """Display daily tasks and challenges with user-specific data."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        flash('Please login to access tasks', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user_tasks = []
    suggested_tasks = []
    
    if db:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_data['id'] = task_doc.id
            user_tasks.append(task_data)
        
        # Get personalized task suggestions, filtering out existing tasks
        existing_task_names = [task.get('name', '') for task in user_tasks]
        suggested_tasks = get_task_suggestions(db, user_id, existing_task_names)
    
    return render_template('tasks.html', tasks=user_tasks, suggested_tasks=suggested_tasks)


# ============================================================
# ROUTE: Add New Task
# ============================================================
@tasks_bp.route('/add_task', methods=['POST'])
def add_task():
    """Add a new task for the current user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    
    if not task_name:
        flash('Task name is required!', 'error')
        return redirect(url_for('tasks.tasks'))
    
    if db:
        task_data = {
            'user_id': session['user_id'],
            'name': task_name,
            'description': task_description,
            'completed': False
        }
        
        db.collection('tasks').add(task_data)
        flash(f'Task "{task_name}" added successfully!', 'success')
    else:
        flash('Database not available', 'error')
    
    return redirect(url_for('tasks.tasks'))


# ============================================================
# ROUTE: Toggle Task Completion
# ============================================================
@tasks_bp.route('/toggle_task/<task_id>', methods=['POST'])
def toggle_task(task_id):
    """Toggle completion status of a task and update avatar points."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database not available', 'error')
        return redirect(url_for('tasks.tasks'))
    
    try:
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()
        
        if not task_doc.exists:
            flash('Task not found', 'error')
            return redirect(url_for('tasks.tasks'))
        
        task_data = task_doc.to_dict()
        
        if task_data.get('user_id') != session['user_id']:
            flash('Unauthorized task access', 'error')
            return redirect(url_for('tasks.tasks'))
        
        # Toggle completion status
        new_completed = not task_data.get('completed', False)
        task_ref.update({'completed': new_completed})
        
        # Update avatar points atomically
        try:
            avatar_ref = db.collection('avatars').document(session['user_id'])
            point_change = 10 if new_completed else -10
            
            avatar_ref.set({
                'user_id': session['user_id'],
                'points': firestore.Increment(point_change),
                'updated_at': datetime.utcnow()
            }, merge=True)
            
            # Ensure points don't go below zero
            avatar_doc = avatar_ref.get()
            if avatar_doc.exists:
                points = int(avatar_doc.to_dict().get('points', 0) or 0)
                if points < 0:
                    avatar_ref.update({'points': 0})
        except Exception as e:
            print(f"Error updating avatar points: {e}")
        
        # Flash appropriate message
        task_name = task_data.get('name', 'Unknown')
        if new_completed:
            flash(f'Task "{task_name}" completed! (+10 pts)', 'success')
        else:
            flash(f'Task "{task_name}" reopened! (-10 pts)', 'warning')
            
    except Exception as e:
        flash('Error updating task', 'error')
        print(f"Task toggle error: {e}")
    
    return redirect(url_for('tasks.tasks'))


# ============================================================
# ROUTE: Delete Task
# ============================================================
@tasks_bp.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    """Delete a task for the current user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database not available', 'error')
        return redirect(url_for('tasks.tasks'))
    
    try:
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()
        
        if not task_doc.exists:
            flash('Task not found', 'error')
            return redirect(url_for('tasks.tasks'))
        
        task_data = task_doc.to_dict()
        
        if task_data.get('user_id') != session['user_id']:
            flash('Unauthorized task access', 'error')
            return redirect(url_for('tasks.tasks'))
        
        task_name = task_data.get('name', 'Unknown')
        task_ref.delete()
        flash(f'Task "{task_name}" deleted successfully!', 'success')
            
    except Exception as e:
        flash('Error deleting task', 'error')
        print(f"Task deletion error: {e}")
    
    return redirect(url_for('tasks.tasks'))


# ============================================================
# ROUTE: Edit Task
# ============================================================
@tasks_bp.route('/edit_task/<task_id>', methods=['POST'])
def edit_task(task_id):
    """Edit a task for the current user."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if not db:
        flash('Database not available', 'error')
        return redirect(url_for('tasks.tasks'))
    
    task_name = request.form.get('task_name', '').strip()
    task_description = request.form.get('task_description', '').strip()
    
    if not task_name:
        flash('Task name is required!', 'error')
        return redirect(url_for('tasks.tasks'))
    
    try:
        task_ref = db.collection('tasks').document(task_id)
        task_doc = task_ref.get()
        
        if not task_doc.exists:
            flash('Task not found', 'error')
            return redirect(url_for('tasks.tasks'))
        
        task_data = task_doc.to_dict()
        
        if task_data.get('user_id') != session['user_id']:
            flash('Unauthorized task access', 'error')
            return redirect(url_for('tasks.tasks'))
        
        task_ref.update({
            'name': task_name,
            'description': task_description
        })
        flash(f'Task "{task_name}" updated successfully!', 'success')
            
    except Exception as e:
        flash('Error updating task', 'error')
        print(f"Task edit error: {e}")
    
    return redirect(url_for('tasks.tasks'))


# ============================================================
# ROUTE: Daily Tasks (JSON API)
# ============================================================
@tasks_bp.route('/api/tasks')
def tasks_api():
    """Return daily tasks as JSON for frontend or integrations."""
    from app import get_db
    db = get_db()
    
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user_id']
    tasks_list = []
    
    if db:
        tasks_ref = db.collection('tasks').where(filter=firestore.FieldFilter('user_id', '==', user_id))
        for task_doc in tasks_ref.stream():
            task_data = task_doc.to_dict()
            task_data['id'] = task_doc.id
            tasks_list.append(task_data)
    
    return jsonify(tasks_list)
