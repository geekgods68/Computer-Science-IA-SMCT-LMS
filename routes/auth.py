from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib

auth_bp = Blueprint('auth', __name__)
DATABASE = 'users.db'

def simple_hash_password(password):
    """Simple password hashing function"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(stored_password, provided_password):
    """Check if provided password matches stored password"""
    return stored_password == simple_hash_password(provided_password)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        
        # Get user
        cur.execute('SELECT id, username, password, role FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        
        if user and check_password(user[2], password):
            # Set session
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            
            conn.close()
            
            # Redirect based on user role
            if user[3] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user[3] == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user[3] == 'student':
                return redirect(url_for('student.dashboard'))
            else:
                flash('Unknown user role!', 'error')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid username or password!', 'error')
            conn.close()
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('auth.login'))
