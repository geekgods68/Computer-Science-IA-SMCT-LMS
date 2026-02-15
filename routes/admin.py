from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import sqlite3
import os
import json
import uuid
import hashlib
from werkzeug.utils import secure_filename
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def simple_hash_password(password):
    """Simple password hashing function"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    """Get database connection"""
    return sqlite3.connect('users.db')

def get_current_user():
    """Get current user from session"""
    class User:
        def __init__(self, user_id, username):
            self.id = user_id
            self.username = username
    
    if 'user_id' in session:
        return User(session['user_id'], session.get('username', ''))
    return None

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all users for display
    cur.execute('SELECT id, username FROM users ORDER BY id')
    users = cur.fetchall()
    
    conn.close()
    return render_template('admin/dashboard.html', users=users)

@admin_bp.route('/users')
def users():
    """Add new users page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get roles
    cur.execute('SELECT id, role_name FROM user_roles ORDER BY role_name')
    roles = cur.fetchall()
    
    # Get all classes for student assignment
    cur.execute('SELECT id, name, type FROM classes WHERE status = "active" ORDER BY name')
    classes = cur.fetchall()
    
    # Fixed subjects list
    subjects = ['Math', 'Science', 'Social Science', 'English', 'Hindi']
    
    # Get existing users for display
    cur.execute('''
        SELECT u.id, u.username, u.role, u.name, u.email, u.created_on
        FROM users u
        ORDER BY u.id
    ''')
    users_list = cur.fetchall()
    
    conn.close()
    return render_template('admin/add_user.html', roles=roles, classes=classes, subjects=subjects, users=users_list)

@admin_bp.route('/add_user', methods=['POST'])
def add_user():
    """Add new user"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    current_user = get_current_user()
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Check if username already exists
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cur.fetchone():
            flash('Username already exists!', 'error')
            return redirect(url_for('admin.users'))
        
        # Create user
        hashed_password = simple_hash_password(password)
        cur.execute('INSERT INTO users (username, password, role, name, email, created_by) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, hashed_password, role, name, email, current_user.id))
        user_id = cur.lastrowid
        
        # Get role_id for user_role_map
        cur.execute('SELECT id FROM user_roles WHERE role_name = ?', (role,))
        role_result = cur.fetchone()
        if role_result:
            role_id = role_result[0]
            cur.execute('INSERT INTO user_role_map (user_id, role_id, assigned_by) VALUES (?, ?, ?)',
                       (user_id, role_id, current_user.id))
        
        # Handle student assignments
        if role == 'student':
            # Assign to classes
            class_assignments = request.form.getlist('student_classes')
            for class_id in class_assignments:
                cur.execute('INSERT INTO student_class_map (student_id, class_id, assigned_by) VALUES (?, ?, ?)',
                           (user_id, class_id, current_user.id))
            
            # Assign subjects
            subject_assignments = request.form.getlist('subjects')
            for subject in subject_assignments:
                cur.execute('INSERT INTO student_subjects (student_id, subject_name, assigned_by) VALUES (?, ?, ?)',
                           (user_id, subject, current_user.id))
        
        # Handle teacher assignments
        elif role == 'teacher':
            # Assign to classes
            class_assignments = request.form.getlist('teacher_classes')
            for class_id in class_assignments:
                cur.execute('INSERT INTO teacher_class_map (teacher_id, class_id, assigned_by) VALUES (?, ?, ?)',
                           (user_id, class_id, current_user.id))
            
            # If no classes assigned, assign to first available class to prevent errors
            if not class_assignments:
                cur.execute('SELECT id FROM classes WHERE status = "active" LIMIT 1')
                first_class = cur.fetchone()
                if first_class:
                    cur.execute('INSERT INTO teacher_class_map (teacher_id, class_id, assigned_by) VALUES (?, ?, ?)',
                               (user_id, first_class[0], current_user.id))
            
            # Assign subjects
            subject_assignments = request.form.getlist('teacher_subjects')
            for subject in subject_assignments:
                cur.execute('INSERT INTO teacher_subjects (teacher_id, subject_name, assigned_by) VALUES (?, ?, ?)',
                           (user_id, subject, current_user.id))
            
            # If no subjects assigned, assign Math as default to prevent errors
            if not subject_assignments:
                cur.execute('INSERT INTO teacher_subjects (teacher_id, subject_name, assigned_by) VALUES (?, ?, ?)',
                           (user_id, 'Math', current_user.id))
        
        conn.commit()
        flash(f'User {username} created successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error creating user: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/manage_users')
def manage_users():
    """Manage users page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    current_user = get_current_user()
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all users with their roles
    cur.execute('''
        SELECT u.id, u.username, u.created_on, u.role, u.name, u.email
        FROM users u
        ORDER BY u.id
    ''')
    users = cur.fetchall()
    
    conn.close()
    return render_template('admin/manage_users.html', users=users, current_user=current_user)

@admin_bp.route('/get_user_details/<int:user_id>')
def get_user_details(user_id):
    """Get user details for modal display"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get user basic info
        cur.execute('''
            SELECT u.id, u.username, u.role, u.name, u.email, u.created_on
            FROM users u
            WHERE u.id = ?
        ''', (user_id,))
        user_info = cur.fetchone()
        
        if not user_info:
            return jsonify({'error': 'User not found'}), 404
        
        user_id_db, username, role, name, email, created_on = user_info
        data = {
            'id': user_id_db,
            'username': username,
            'role': role,
            'name': name,
            'email': email,
            'created_on': created_on,
            'classes': [],
            'subjects': []
        }
        
        # Get assignments based on role
        if role == 'student':
            # Get assigned classes
            cur.execute('''
                SELECT c.name, c.type 
                FROM classes c 
                JOIN student_class_map scm ON c.id = scm.class_id 
                WHERE scm.student_id = ? AND scm.status = 'active'
                ORDER BY c.name
            ''', (user_id,))
            classes_data = cur.fetchall()
            data['classes'] = [f"{row[0]} ({row[1]})" for row in classes_data]
            
            # Get assigned subjects
            cur.execute('SELECT subject_name FROM student_subjects WHERE student_id = ? ORDER BY subject_name', (user_id,))
            subjects_data = cur.fetchall()
            data['subjects'] = [row[0] for row in subjects_data]
            
        elif role == 'teacher':
            # Get assigned classes
            cur.execute('''
                SELECT c.name, c.type 
                FROM classes c 
                JOIN teacher_class_map tcm ON c.id = tcm.class_id 
                WHERE tcm.teacher_id = ?
                ORDER BY c.name
            ''', (user_id,))
            classes_data = cur.fetchall()
            data['classes'] = [f"{row[0]} ({row[1]})" for row in classes_data]
            
            # Get assigned subjects
            cur.execute('SELECT subject_name FROM teacher_subjects WHERE teacher_id = ? ORDER BY subject_name', (user_id,))
            subjects_data = cur.fetchall()
            data['subjects'] = [row[0] for row in subjects_data]
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

@admin_bp.route('/edit_student/<int:student_id>')
def edit_student(student_id):
    """Edit student page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get student info
    cur.execute('SELECT username FROM users WHERE id = ?', (student_id,))
    student = cur.fetchone()
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Get all classes
    cur.execute('SELECT id, name, type FROM classes WHERE status = "active" ORDER BY name')
    all_classes = cur.fetchall()
    
    # Get assigned classes
    cur.execute('''
        SELECT c.id, c.name, c.type
        FROM classes c
        JOIN student_class_map scm ON c.id = scm.class_id
        WHERE scm.student_id = ?
        ORDER BY c.name
    ''', (student_id,))
    assigned_classes = cur.fetchall()
    
    # Fixed subjects list
    available_subjects = ['Math', 'Science', 'Social Science', 'English', 'Hindi']
    
    # Get assigned subjects
    cur.execute('SELECT subject_name FROM student_subjects WHERE student_id = ? ORDER BY subject_name', (student_id,))
    assigned_subjects_data = cur.fetchall()
    assigned_subjects = [row[0] for row in assigned_subjects_data]
    
    conn.close()
    
    return render_template('admin/edit_student.html',
                         student_id=student_id,
                         student_name=student[0],
                         all_classes=all_classes,
                         assigned_classes=[cls[0] for cls in assigned_classes],
                         available_subjects=available_subjects,
                         assigned_subjects=assigned_subjects)

@admin_bp.route('/edit_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    """Update student assignments"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    current_user = get_current_user()
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get assigned classes and subjects
        classes = request.form.getlist('classes')
        subjects = request.form.getlist('subjects')
        
        # Remove existing assignments
        cur.execute('DELETE FROM student_class_map WHERE student_id = ?', (student_id,))
        cur.execute('DELETE FROM student_subjects WHERE student_id = ?', (student_id,))
        
        # Add new class assignments
        for class_id in classes:
            cur.execute('INSERT INTO student_class_map (student_id, class_id, assigned_by) VALUES (?, ?, ?)',
                       (student_id, class_id, current_user.id))
        
        # Add new subject assignments
        for subject in subjects:
            cur.execute('INSERT INTO student_subjects (student_id, subject_name, assigned_by) VALUES (?, ?, ?)',
                       (student_id, subject, current_user.id))
        
        conn.commit()
        flash('Student assignments updated successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error updating student: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.edit_student', student_id=student_id))

@admin_bp.route('/edit_teacher/<int:teacher_id>')
def edit_teacher(teacher_id):
    """Edit teacher page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get teacher info
    cur.execute('SELECT username FROM users WHERE id = ?', (teacher_id,))
    teacher = cur.fetchone()
    
    if not teacher:
        flash('Teacher not found!', 'error')
        return redirect(url_for('admin.manage_users'))
    
    # Get all classes
    cur.execute('SELECT id, name, type FROM classes WHERE status = "active" ORDER BY name')
    all_classes = cur.fetchall()
    
    # Get assigned classes
    cur.execute('''
        SELECT c.id, c.name, c.type
        FROM classes c
        JOIN teacher_class_map tcm ON c.id = tcm.class_id
        WHERE tcm.teacher_id = ?
        ORDER BY c.name
    ''', (teacher_id,))
    assigned_classes = cur.fetchall()
    
    # Fixed subjects list
    available_subjects = ['Math', 'Science', 'Social Science', 'English', 'Hindi']
    
    # Get assigned subjects
    cur.execute('SELECT subject_name FROM teacher_subjects WHERE teacher_id = ? ORDER BY subject_name', (teacher_id,))
    assigned_subjects_data = cur.fetchall()
    assigned_subjects = [row[0] for row in assigned_subjects_data]
    
    conn.close()
    
    return render_template('admin/edit_teacher.html',
                         teacher_id=teacher_id,
                         teacher_name=teacher[0],
                         all_classes=all_classes,
                         assigned_classes=[cls[0] for cls in assigned_classes],
                         available_subjects=available_subjects,
                         assigned_subjects=assigned_subjects)

@admin_bp.route('/edit_teacher/<int:teacher_id>', methods=['POST'])
def update_teacher(teacher_id):
    """Update teacher assignments"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    current_user = get_current_user()
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get assigned classes and subjects
        classes = request.form.getlist('classes')
        subjects = request.form.getlist('subjects')
        
        # Remove existing assignments
        cur.execute('DELETE FROM teacher_class_map WHERE teacher_id = ?', (teacher_id,))
        cur.execute('DELETE FROM teacher_subjects WHERE teacher_id = ?', (teacher_id,))
        
        # Add new class assignments
        for class_id in classes:
            cur.execute('INSERT INTO teacher_class_map (teacher_id, class_id, assigned_by) VALUES (?, ?, ?)',
                       (teacher_id, class_id, current_user.id))
        
        # Add new subject assignments
        for subject in subjects:
            cur.execute('INSERT INTO teacher_subjects (teacher_id, subject_name, assigned_by) VALUES (?, ?, ?)',
                       (teacher_id, subject, current_user.id))
        
        conn.commit()
        flash('Teacher assignments updated successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error updating teacher: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.edit_teacher', teacher_id=teacher_id))

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete user"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get user info before deletion
        cur.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cur.fetchone()
        
        if not user:
            flash('Deletion unsuccessful, contact tech team', 'error')
            return redirect(url_for('admin.manage_users'))
        
        # Delete all related records
        cur.execute('DELETE FROM student_class_map WHERE student_id = ?', (user_id,))
        cur.execute('DELETE FROM teacher_class_map WHERE teacher_id = ?', (user_id,))
        cur.execute('DELETE FROM student_subjects WHERE student_id = ?', (user_id,))
        cur.execute('DELETE FROM teacher_subjects WHERE teacher_id = ?', (user_id,))
        cur.execute('DELETE FROM user_role_map WHERE user_id = ?', (user_id,))
        cur.execute('DELETE FROM feedback WHERE student_id = ?', (user_id,))
        cur.execute('DELETE FROM doubts WHERE student_id = ?', (user_id,))
        cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        flash('Deletion successful', 'success')
        return redirect(url_for('admin.manage_users'))
        
    except Exception as e:
        conn.rollback()
        flash('Deletion unsuccessful, contact tech team', 'error')
        return redirect(url_for('admin.manage_users'))
    
    finally:
        conn.close()

@admin_bp.route('/create_class')
def create_class():
    """Create class page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    return render_template('admin/create_class.html')

@admin_bp.route('/create_class', methods=['POST'])
def add_class():
    """Add new class"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    current_user = get_current_user()
    
    # Get form data
    name = request.form['name']
    class_type = request.form['type']
    description = request.form.get('description', '')
    grade_level = request.form.get('grade_level', '')
    section = request.form.get('section', '')
    meeting_link = request.form.get('meeting_link', '')
    max_students = request.form.get('max_students', 30)
    subject = request.form['subject']
    
    # Schedule data
    schedule_days = request.form.getlist('schedule_days')
    schedule_time_start = request.form.get('schedule_time_start', '')
    schedule_time_end = request.form.get('schedule_time_end', '')
    
    # Handle PDF upload
    schedule_pdf_path = ''
    if 'schedule_pdf' in request.files:
        file = request.files['schedule_pdf']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Create uploads directory if it doesn't exist
            upload_dir = 'static/uploads/schedules'
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            schedule_pdf_path = file_path
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Insert class
        cur.execute('''
            INSERT INTO classes (
                name, type, description, grade_level, section,
                schedule_days, schedule_time_start, schedule_time_end,
                schedule_pdf_path, meeting_link, max_students, subject, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, class_type, description, grade_level, section,
            json.dumps(schedule_days), schedule_time_start, schedule_time_end,
            schedule_pdf_path, meeting_link, max_students, subject, current_user.id
        ))
        
        conn.commit()
        flash(f'Class "{name}" created successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error creating class: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.create_class'))

@admin_bp.route('/view_classes')
def view_classes():
    """View all classes"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all classes with student/teacher counts
    cur.execute('''
        SELECT 
            c.id, c.name, c.type, c.description, c.grade_level, c.section,
            c.schedule_days, c.schedule_time_start, c.schedule_time_end,
            c.meeting_link, c.max_students, c.status, c.subject,
            COUNT(DISTINCT scm.student_id) as student_count,
            COUNT(DISTINCT tcm.teacher_id) as teacher_count
        FROM classes c
        LEFT JOIN student_class_map scm ON c.id = scm.class_id
        LEFT JOIN teacher_class_map tcm ON c.id = tcm.class_id
        GROUP BY c.id
        ORDER BY c.name
    ''')
    classes = cur.fetchall()
    
    conn.close()
    return render_template('admin/view_classes.html', classes=classes)

@admin_bp.route('/view_class/<int:class_id>')
def view_class(class_id):
    """View specific class details"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get class info
    cur.execute('SELECT * FROM classes WHERE id = ?', (class_id,))
    class_info = cur.fetchone()
    
    if not class_info:
        flash('Class not found!', 'error')
        return redirect(url_for('admin.view_classes'))
    
    # Get assigned students
    cur.execute('''
        SELECT u.id, u.username
        FROM users u
        JOIN student_class_map scm ON u.id = scm.student_id
        WHERE scm.class_id = ?
        ORDER BY u.username
    ''', (class_id,))
    students = cur.fetchall()
    
    # Get assigned teachers
    cur.execute('''
        SELECT u.id, u.username
        FROM users u
        JOIN teacher_class_map tcm ON u.id = tcm.teacher_id
        WHERE tcm.class_id = ?
        ORDER BY u.username
    ''', (class_id,))
    teachers = cur.fetchall()
    
    # Get subjects taught in this class (from assigned students and teachers)
    cur.execute('''
        SELECT DISTINCT ss.subject_name
        FROM student_subjects ss
        JOIN student_class_map scm ON ss.student_id = scm.student_id
        WHERE scm.class_id = ? AND scm.status = 'active'
        UNION
        SELECT DISTINCT ts.subject_name
        FROM teacher_subjects ts
        JOIN teacher_class_map tcm ON ts.teacher_id = tcm.teacher_id
        WHERE tcm.class_id = ?
        ORDER BY subject_name
    ''', (class_id, class_id))
    subjects_data = cur.fetchall()
    subjects = [{'name': row[0]} for row in subjects_data]
    
    conn.close()
    return render_template('admin/view_class.html',
                         class_info=class_info,
                         students=students,
                         teachers=teachers,
                         subjects=subjects)

@admin_bp.route('/add_students')
def add_students():
    """Add students to class page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all classes
    cur.execute('SELECT id, name, type FROM classes WHERE status = "active" ORDER BY name')
    classes = cur.fetchall()
    
    # Get all students (only users with role 'student')
    cur.execute('''
        SELECT u.id, u.username, u.name
        FROM users u
        WHERE u.role = 'student'
        ORDER BY u.username
    ''')
    students = cur.fetchall()
    
    conn.close()
    return render_template('admin/add_students.html', classes=classes, students=students)

@admin_bp.route('/assign_students', methods=['POST'])
def assign_students():
    """Assign students to class"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    class_id = request.form['class_id']
    student_ids = request.form.getlist('student_ids')
    current_user = get_current_user()
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        for student_id in student_ids:
            # Check if already assigned
            cur.execute('SELECT id FROM student_class_map WHERE student_id = ? AND class_id = ?',
                       (student_id, class_id))
            if not cur.fetchone():
                cur.execute('INSERT INTO student_class_map (student_id, class_id, assigned_by) VALUES (?, ?, ?)',
                           (student_id, class_id, current_user.id))
        
        conn.commit()
        flash('Students assigned successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error assigning students: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.add_students'))

# Subject creation functionality removed - using fixed subject list now
# Fixed subjects: Math, Science, Social Science, English, Hindi

@admin_bp.route('/view_feedback')
def view_feedback():
    """View all feedback submissions"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get feedback stats
    cur.execute('SELECT COUNT(*) FROM feedback')
    total_feedback = cur.fetchone()[0]
    
    # For now, create mock stats since we don't have status field in feedback table
    feedback_stats = {
        'total': total_feedback,
        'pending': total_feedback // 2,
        'reviewed': total_feedback // 3,
        'resolved': total_feedback // 4
    }
    
    # Get all feedback with user details
    cur.execute('''
        SELECT f.id, f.student_id, f.feedback_text, f.rating, f.submitted_on,
               u.username, f.status, f.admin_response, f.response_date
        FROM feedback f
        LEFT JOIN users u ON f.student_id = u.id
        ORDER BY f.submitted_on DESC
    ''')
    feedback_raw = cur.fetchall()
    
    # Get proper feedback stats
    cur.execute('SELECT COUNT(*) FROM feedback WHERE status = ?', ('pending',))
    pending_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM feedback WHERE status = ?', ('reviewed',))
    reviewed_count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM feedback WHERE status = ?', ('resolved',))
    resolved_count = cur.fetchone()[0]
    
    feedback_stats = {
        'total': total_feedback,
        'pending': pending_count,
        'reviewed': reviewed_count,
        'resolved': resolved_count
    }
    
    # Transform feedback data to match template expectations
    feedback_list = []
    for row in feedback_raw:
        feedback_list.append([
            row[0],  # id
            row[1],  # student_id
            'general',  # category (mock)
            '',  # subject (mock)
            '',  # teacher (mock)
            '',  # class (mock)
            row[3],  # rating
            row[2],  # feedback_text
            0,  # is_anonymous (mock)
            row[4],  # submitted_on
            row[6] or 'pending',  # status
            row[7] or '',  # admin_response
            row[8] or '',  # response_date
            '',  # resolved_date (mock)
            row[5]  # username
        ])
    
    conn.close()
    return render_template('admin/view_feedback.html', 
                         feedback_stats=feedback_stats, 
                         feedback_list=feedback_list)

@admin_bp.route('/respond_to_feedback', methods=['POST'])
def respond_to_feedback():
    """Respond to student feedback"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    feedback_id = request.form.get('feedback_id')
    admin_response = request.form.get('admin_response', '').strip()
    mark_resolved = 'mark_resolved' in request.form
    
    if not feedback_id or not admin_response:
        flash('Feedback ID and response are required', 'error')
        return redirect(url_for('admin.view_feedback'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Update the feedback with admin response
        status = 'resolved' if mark_resolved else 'reviewed'
        admin_id = session.get('user_id')
        
        cur.execute('''
            UPDATE feedback 
            SET admin_response = ?, response_date = CURRENT_TIMESTAMP, 
                responded_by = ?, status = ?
            WHERE id = ?
        ''', (admin_response, admin_id, status, feedback_id))
        
        conn.commit()
        
        # Check if update was successful
        if cur.rowcount > 0:
            flash(f'Response saved successfully and feedback marked as {status}!', 'success')
        else:
            flash('Feedback not found', 'error')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error saving response: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.view_feedback'))

@admin_bp.route('/update_feedback_status', methods=['POST'])
def update_feedback_status():
    """Update feedback status"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    feedback_id = request.form.get('feedback_id')
    status = request.form.get('status')
    
    if not feedback_id or not status:
        flash('Feedback ID and status are required', 'error')
        return redirect(url_for('admin.view_feedback'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE feedback SET status = ? WHERE id = ?', (status, feedback_id))
        conn.commit()
        
        if cur.rowcount > 0:
            flash(f'Feedback marked as {status}!', 'success')
        else:
            flash('Feedback not found', 'error')
            
    except Exception as e:
        conn.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin.view_feedback'))

@admin_bp.route('/view_doubts')
def view_doubts():
    """View all student doubts"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get all doubts with user details
    cur.execute('''
        SELECT d.id, d.student_id, d.subject, d.doubt_text, d.status, 
               d.submitted_on, d.resolved_on, u.username
        FROM doubts d
        LEFT JOIN users u ON d.student_id = u.id
        ORDER BY d.submitted_on DESC
    ''')
    doubts = cur.fetchall()
    
    conn.close()
    return render_template('admin/view_doubts.html', doubts=doubts)

@admin_bp.route('/respond_doubt', methods=['POST'])
def respond_doubt():
    """Respond to a student doubt"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    doubt_id = request.form.get('doubt_id')
    response = request.form.get('response')
    current_user = get_current_user()
    
    if not doubt_id or not response:
        flash('Invalid doubt ID or response provided!', 'error')
        return redirect(url_for('admin.view_doubts'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            UPDATE doubts 
            SET response = ?, status = 'answered', response_time = ?, responder_id = ?
            WHERE id = ?
        ''', (response, datetime.now(), current_user.id, doubt_id))
        
        conn.commit()
        flash('Response added successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error adding response: {str(e)}', 'error')
    
    finally:
        conn.close()
    
    return redirect(url_for('admin.view_doubts'))

@admin_bp.route('/download_schedule/<int:class_id>')
def download_schedule(class_id):
    """Download class schedule PDF"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT schedule_pdf_path, name FROM classes WHERE id = ?', (class_id,))
    result = cur.fetchone()
    conn.close()
    
    if not result or not result[0]:
        flash('Schedule PDF not found!', 'error')
        return redirect(url_for('admin.view_classes'))
    
    pdf_path, class_name = result
    
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=f"{class_name}_schedule.pdf")
    else:
        flash('Schedule file not found on server!', 'error')
        return redirect(url_for('admin.view_classes'))

@admin_bp.route('/get_class_subjects/<int:class_id>')
def get_class_subjects(class_id):
    """Get subjects for a specific class (AJAX endpoint)"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get class name
        cur.execute('SELECT name FROM classes WHERE id = ?', (class_id,))
        class_result = cur.fetchone()
        
        if not class_result:
            return jsonify({'error': 'Class not found'}), 404
        
        # Get subjects for this class
        cur.execute('SELECT id, name, description FROM subjects WHERE class_id = ? ORDER BY name', (class_id,))
        subjects_data = cur.fetchall()
        
        subjects = []
        for subject in subjects_data:
            subjects.append({
                'id': subject[0],
                'name': subject[1],
                'description': subject[2] or 'No description'
            })
        
        return jsonify({
            'class_name': class_result[0],
            'subjects': subjects
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

# Additional utility routes for enhanced admin functionality

@admin_bp.route('/delete_class/<int:class_id>', methods=['POST'])
def delete_class(class_id):
    """Delete a class and all its associations"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get class info before deletion
        cur.execute('SELECT name FROM classes WHERE id = ?', (class_id,))
        class_info = cur.fetchone()
        
        if not class_info:
            return jsonify({'success': False, 'message': 'Class not found'}), 404
        
        # Delete all related records in the correct order to avoid foreign key constraints
        
        # First delete submissions for assignments in this class
        cur.execute('''DELETE FROM submissions WHERE assignment_id IN 
                       (SELECT id FROM assignments WHERE class_id = ?)''', (class_id,))
        
        # Delete marks for assessments in this class
        cur.execute('''DELETE FROM marks WHERE assessment_id IN 
                       (SELECT id FROM assessments WHERE class_id = ?)''', (class_id,))
        
        # Delete direct class-related records
        cur.execute('DELETE FROM student_class_map WHERE class_id = ?', (class_id,))
        cur.execute('DELETE FROM teacher_class_map WHERE class_id = ?', (class_id,))
        cur.execute('DELETE FROM announcements WHERE class_id = ?', (class_id,))
        cur.execute('DELETE FROM attendance WHERE class_id = ?', (class_id,))
        cur.execute('DELETE FROM assignments WHERE class_id = ?', (class_id,))
        cur.execute('DELETE FROM assessments WHERE class_id = ?', (class_id,))
        
        # Finally delete the class itself
        cur.execute('DELETE FROM classes WHERE id = ?', (class_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': f'Class "{class_info[0]}" deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        print(f"Error deleting class {class_id}: {str(e)}")  # Add logging
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    
    finally:
        conn.close()

@admin_bp.route('/toggle_class_status/<int:class_id>', methods=['POST'])
def toggle_class_status(class_id):
    """Toggle class status between active and inactive"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get current status
        cur.execute('SELECT status, name FROM classes WHERE id = ?', (class_id,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'error': 'Class not found'}), 404
        
        current_status, class_name = result
        new_status = 'inactive' if current_status == 'active' else 'active'
        
        # Update status
        cur.execute('UPDATE classes SET status = ? WHERE id = ?', (new_status, class_id))
        
        conn.commit()
        return jsonify({
            'message': f'Class "{class_name}" status changed to {new_status}',
            'new_status': new_status
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()

@admin_bp.route('/stats')
def admin_stats():
    """Get admin dashboard statistics"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        stats = {}
        
        # Count users by role
        cur.execute('''
            SELECT ur.role_name, COUNT(u.id) as count
            FROM user_roles ur
            LEFT JOIN user_role_map urm ON ur.id = urm.role_id
            LEFT JOIN users u ON urm.user_id = u.id
            GROUP BY ur.role_name
        ''')
        role_counts = cur.fetchall()
        stats['users'] = {role: count for role, count in role_counts}
        
        # Count classes by status
        cur.execute('SELECT status, COUNT(*) FROM classes GROUP BY status')
        class_counts = cur.fetchall()
        stats['classes'] = {status: count for status, count in class_counts}
        
        # Count total subjects
        cur.execute('SELECT COUNT(*) FROM subjects')
        stats['total_subjects'] = cur.fetchone()[0]
        
        # Count pending feedback
        cur.execute('SELECT COUNT(*) FROM feedback WHERE status = "pending"')
        stats['pending_feedback'] = cur.fetchone()[0]
        
        # Count pending doubts
        cur.execute('SELECT COUNT(*) FROM doubts WHERE status = "pending"')
        stats['pending_doubts'] = cur.fetchone()[0]
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        conn.close()


# ============================================================================
# ATTENDANCE MANAGEMENT ROUTES
# ============================================================================

@admin_bp.route('/attendance')
def attendance():
    """Admin attendance management page"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get all classes for dropdown
        cur.execute('''
            SELECT id, name, grade_level 
            FROM classes 
            WHERE status = 'active'
            ORDER BY grade_level, name
        ''')
        classes = cur.fetchall()
        
        # Get attendance data for the last 30 days
        cur.execute('''
            SELECT 
                a.id,
                a.attendance_date,
                a.status,
                a.notes,
                u.name as student_name,
                c.name as class_name,
                c.grade_level,
                marker.name as marked_by_name,
                a.marked_on
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN classes c ON a.class_id = c.id
            JOIN users marker ON a.marked_by = marker.id
            WHERE a.attendance_date >= date('now', '-30 days')
            ORDER BY a.attendance_date DESC, c.name, u.name
        ''')
        attendance_records = cur.fetchall()
        
        return render_template('admin/attendance.html', 
                             classes=classes, 
                             attendance_records=attendance_records)
        
    except Exception as e:
        flash(f'Error loading attendance data: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))
    finally:
        conn.close()

@admin_bp.route('/attendance/mark', methods=['GET', 'POST'])
def mark_attendance():
    """Mark attendance for a class"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    if request.method == 'GET':
        class_id = request.args.get('class_id')
        attendance_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if not class_id:
            flash('Class ID is required', 'error')
            return redirect(url_for('admin.attendance'))
        
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Get class details
            cur.execute('SELECT name, grade_level FROM classes WHERE id = ?', (class_id,))
            class_info = cur.fetchone()
            
            if not class_info:
                flash('Class not found', 'error')
                return redirect(url_for('admin.attendance'))
            
            # Get students in this class
            cur.execute('''
                SELECT u.id, u.name
                FROM users u
                JOIN student_class_map scm ON u.id = scm.student_id
                WHERE scm.class_id = ? AND u.role = 'student' AND scm.status = 'active'
                ORDER BY u.name
            ''', (class_id,))
            students = cur.fetchall()
            
            # Get existing attendance for this date
            cur.execute('''
                SELECT student_id, status, notes
                FROM attendance
                WHERE class_id = ? AND attendance_date = ?
            ''', (class_id, attendance_date))
            existing_attendance = {row[0]: {'status': row[1], 'notes': row[2]} 
                                 for row in cur.fetchall()}
            
            return render_template('admin/mark_attendance.html',
                                 class_id=class_id,
                                 class_info=class_info,
                                 students=students,
                                 attendance_date=attendance_date,
                                 existing_attendance=existing_attendance)
            
        except Exception as e:
            flash(f'Error loading class data: {str(e)}', 'error')
            return redirect(url_for('admin.attendance'))
        finally:
            conn.close()
    
    # POST request - save attendance
    class_id = request.form.get('class_id')
    attendance_date = request.form.get('attendance_date')
    
    if not class_id or not attendance_date:
        flash('Class ID and date are required', 'error')
        return redirect(url_for('admin.attendance'))
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get all students in the class
        cur.execute('''
            SELECT u.id
            FROM users u
            JOIN student_class_map scm ON u.id = scm.student_id
            WHERE scm.class_id = ? AND u.role = 'student' AND scm.status = 'active'
        ''', (class_id,))
        students = [row[0] for row in cur.fetchall()]
        
        attendance_saved = 0
        for student_id in students:
            status = request.form.get(f'status_{student_id}', 'absent')
            notes = request.form.get(f'notes_{student_id}', '').strip()
            
            # Delete existing attendance record if any
            cur.execute('''
                DELETE FROM attendance 
                WHERE student_id = ? AND class_id = ? AND attendance_date = ?
            ''', (student_id, class_id, attendance_date))
            
            # Insert new attendance record
            cur.execute('''
                INSERT INTO attendance (student_id, class_id, attendance_date, status, marked_by, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, class_id, attendance_date, status, session['user_id'], notes))
            
            attendance_saved += 1
        
        conn.commit()
        flash(f'Attendance marked for {attendance_saved} students', 'success')
        return redirect(url_for('admin.attendance'))
        
    except Exception as e:
        conn.rollback()
        flash(f'Error saving attendance: {str(e)}', 'error')
        return redirect(url_for('admin.mark_attendance', class_id=class_id, date=attendance_date))
    finally:
        conn.close()

@admin_bp.route('/attendance/report')
def attendance_report():
    """Generate attendance report"""
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('auth.login'))
    
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Build query based on filters
        where_conditions = []
        params = []
        
        if class_id:
            where_conditions.append('a.class_id = ?')
            params.append(class_id)
        
        if start_date:
            where_conditions.append('a.attendance_date >= ?')
            params.append(start_date)
        
        if end_date:
            where_conditions.append('a.attendance_date <= ?')
            params.append(end_date)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        # Get attendance summary
        cur.execute(f'''
            SELECT 
                u.name as student_name,
                c.name as class_name,
                c.grade_level,
                COUNT(*) as total_days,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_days,
                SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) as excused_days,
                ROUND((SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) as attendance_percentage
            FROM attendance a
            JOIN users u ON a.student_id = u.id
            JOIN classes c ON a.class_id = c.id
            WHERE {where_clause}
            GROUP BY u.id, c.id
            ORDER BY c.name, u.name
        ''', params)
        report_data = cur.fetchall()
        
        # Get all classes for filter dropdown
        cur.execute('SELECT id, name, grade_level FROM classes ORDER BY grade_level, name')
        classes = cur.fetchall()
        
        return render_template('admin/attendance_report.html',
                             report_data=report_data,
                             classes=classes,
                             filters={'class_id': class_id, 'start_date': start_date, 'end_date': end_date})
        
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('admin.attendance'))
    finally:
        conn.close()

@admin_bp.route('/get_feedback/<int:feedback_id>')
def get_feedback(feedback_id):
    """Get feedback details for viewing"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT f.id, f.student_id, f.feedback_text, f.rating, f.submitted_on,
                   u.username, f.status, f.admin_response, f.response_date
            FROM feedback f
            LEFT JOIN users u ON f.student_id = u.id
            WHERE f.id = ?
        ''', (feedback_id,))
        
        row = cur.fetchone()
        if row:
            feedback_data = {
                'id': row[0],
                'student_id': row[1],
                'feedback_text': row[2],
                'rating': row[3],
                'submitted_on': row[4],
                'username': row[5],
                'status': row[6] or 'pending',
                'admin_response': row[7],
                'response_date': row[8]
            }
            return jsonify({'success': True, 'feedback': feedback_data})
        else:
            return jsonify({'success': False, 'error': 'Feedback not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@admin_bp.route('/mark_feedback_reviewed/<int:feedback_id>', methods=['POST'])
def mark_feedback_reviewed(feedback_id):
    """Mark feedback as reviewed"""
    if 'role' not in session or session['role'] != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE feedback SET status = ? WHERE id = ?', ('reviewed', feedback_id))
        conn.commit()
        
        if cur.rowcount > 0:
            return jsonify({'success': True, 'message': 'Feedback marked as reviewed'})
        else:
            return jsonify({'success': False, 'error': 'Feedback not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()


