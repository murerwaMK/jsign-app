from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from .models import User, Document, Signature, db
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

admin = Blueprint('admin', __name__)

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.username).all()
    return render_template('admin_dashboard.html', users=users)

@admin.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        flash('Username or email already exists.', category='error')
    else:
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully!', category='success')
    return redirect(url_for('admin.dashboard'))

# NEW: Route to handle editing a user
@admin.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    user.username = request.form.get('username')
    user.email = request.form.get('email')
    user.role = request.form.get('role')
    
    new_password = request.form.get('password')
    if new_password:
        user.set_password(new_password)
    
    db.session.commit()
    flash(f"User '{user.username}' updated successfully.", category='success')
    return redirect(url_for('admin.dashboard'))


# NEW: Route to handle deleting a user
@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    # Safety check: prevent an admin from deleting their own account
    if user_to_delete.id == current_user.id:
        flash("You cannot delete your own account.", category='error')
        return redirect(url_for('admin.dashboard'))
    
    # Re-assign any documents the user uploaded to the current admin
    # This prevents documents from becoming "orphaned"
    Document.query.filter_by(uploader_id=user_to_delete.id).update({'uploader_id': current_user.id})
    
    # Now, delete the user. The database will automatically delete their associated
    # signatures because of the 'cascade' rule we just added.
    db.session.delete(user_to_delete)
    
    # Commit all changes to the database at once.
    db.session.commit()
    
    flash(f"User '{user_to_delete.username}' has been deleted. Their documents have been reassigned to you.", category='success')
    return redirect(url_for('admin.dashboard'))