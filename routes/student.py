from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file, send_from_directory
import sqlite3
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__, url_prefix='/student')

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.png', '.jpg', '.jpeg'}

def ensure_upload_dirs():
    """Ensure upload directories exist"""
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'assignments'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'submissions'), exist_ok=True)

def get_db():
    """Get database connection"""
    return sqlite3.connect('users.db')

def get_notifications(user_id, user_type='student'):
    """Get unread notifications for a user"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, message, created_at
        FROM notifications
        WHERE user_id = ? AND user_type = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 10
    ''', (user_id, user_type))
    
    notifications = cur.fetchall()
    conn.close()
    return notifications

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE notifications 
        SET is_read = 1 
        WHERE id = ?
    ''', (notification_id,))
    
    conn.commit()
    conn.close()

@student_bp.route('/site')
def site():
    """Deprecated: Redirect to dashboard"""
    return redirect(url_for('student.dashboard'))

@student_bp.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    """Mark all notifications as read for the current student"""
    if 'role' not in session or session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE notifications 
            SET is_read = 1 
            WHERE user_id = ? AND user_type = 'student'
        ''', (student_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Notifications marked as read'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@student_bp.route('/classes')
def classes():
    """Display student's enrolled classes"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get enrolled classes with teacher information and assignment counts
        cur.execute('''
            SELECT DISTINCT
                c.id, c.name, c.grade_level, c.subject, c.type, c.description,
                c.schedule_days, c.schedule_time_start, c.schedule_time_end,
                u.name as teacher_name,
                COUNT(a.id) as assignment_count,
                COUNT(CASE WHEN a.due_date >= datetime('now') THEN 1 END) as pending_assignments
            FROM student_class_map scm
            JOIN classes c ON scm.class_id = c.id
            LEFT JOIN teacher_class_map tcm ON c.id = tcm.class_id
            LEFT JOIN users u ON tcm.teacher_id = u.id
            LEFT JOIN assignments a ON c.id = a.class_id AND a.status = 'active'
            WHERE scm.student_id = ? AND scm.status = 'active'
            GROUP BY c.id, c.name, c.grade_level, c.subject, u.name
            ORDER BY c.grade_level, c.name
        ''', (student_id,))
        
        classes_data = []
        for row in cur.fetchall():
            classes_data.append({
                'id': row[0],
                'name': row[1],
                'grade_level': row[2],
                'subject': row[3],
                'type': row[4] or 'Regular',
                'description': row[5] or 'No description available',
                'schedule_days': row[6] or 'TBA',
                'schedule_time_start': row[7] or '',
                'schedule_time_end': row[8] or '',
                'teacher_name': row[9] or 'TBA',
                'assignment_count': row[10],
                'pending_assignments': row[11]
            })
        
        conn.close()
        return render_template('student/student_classes.html', 
                             student_classes=classes_data,
                             student_name=session.get('name'))
    
    except Exception as e:
        conn.close()
        flash(f'Error loading classes: {str(e)}', 'error')
        return render_template('student/student_classes.html', 
                             student_classes=[],
                             student_name=session.get('name'))

@student_bp.route('/homework')
def homework():
    """Display homework assignments"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get student's enrolled classes
        cur.execute('''
            SELECT c.id, c.name, c.grade_level
            FROM classes c
            JOIN student_class_map scm ON c.id = scm.class_id
            WHERE scm.student_id = ? AND c.status = 'active'
        ''', (student_id,))
        student_classes = cur.fetchall()
        
        # Get available homework assignments for student's classes
        if student_classes:
            class_ids = [str(c[0]) for c in student_classes]
            placeholders = ','.join('?' * len(class_ids))
            
            cur.execute(f'''
                SELECT 
                    a.id, a.teacher_id, a.class_id, a.title, a.description, a.assignment_type,
                    a.due_date, a.points, a.file_path, a.original_filename, a.allow_late_submission,
                    a.created_at, a.status,
                    c.name as class_name,
                    c.subject as subject_name,
                    u.name as teacher_name
                FROM assignments a
                LEFT JOIN classes c ON a.class_id = c.id
                LEFT JOIN users u ON a.teacher_id = u.id
                WHERE a.class_id IN ({placeholders}) AND a.status = 'active'
                ORDER BY a.due_date ASC
            ''', class_ids)
            
            assignments = cur.fetchall()
            
            # Convert to objects for easier template access
            homework_assignments = []
            for row in assignments:
                # Handle datetime parsing robustly
                try:
                    due_date = datetime.strptime(row[6], '%Y-%m-%dT%H:%M') if row[6] else None
                except ValueError:
                    try:
                        due_date = datetime.strptime(row[6], '%Y-%m-%d %H:%M:%S') if row[6] else None
                    except ValueError:
                        due_date = None
                
                try:
                    if row[11] and '.' in row[11]:
                        created_on = datetime.strptime(row[11], '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        created_on = datetime.strptime(row[11], '%Y-%m-%d %H:%M:%S') if row[11] else None
                except ValueError:
                    created_on = None
                
                assignment = type('Assignment', (), {})()
                assignment.id = row[0]
                assignment.teacher_id = row[1]
                assignment.class_id = row[2]
                assignment.title = row[3]
                assignment.description = row[4]
                assignment.assignment_type = row[5]
                assignment.due_date = due_date
                assignment.points = row[7]
                assignment.file_path = row[8]
                assignment.original_filename = row[9]
                assignment.allow_late_submission = bool(row[10])
                assignment.created_on = created_on
                assignment.status = row[12] or 'active'
                assignment.class_name = row[13]
                assignment.subject_name = row[14]
                assignment.teacher_name = row[15]
                
                # Calculate if assignment is overdue
                if assignment.due_date:
                    assignment.is_overdue = datetime.now() > assignment.due_date
                    assignment.days_until_due = (assignment.due_date - datetime.now()).days
                else:
                    assignment.is_overdue = False
                    assignment.days_until_due = None
                
                homework_assignments.append(assignment)
        else:
            homework_assignments = []
        
        return render_template('student/student_homework_clean.html', 
                             student_classes=student_classes,
                             homework_assignments=homework_assignments)
    except Exception as e:
        flash(f'Error loading homework: {str(e)}', 'error')
        # Return empty data instead of redirecting
        return render_template('student/student_homework_clean.html', 
                             student_classes=[],
                             homework_assignments=[])
    finally:
        conn.close()

@student_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Submit anonymous feedback"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        feedback_text = request.form.get('feedback_text', '').strip()
        
        if not feedback_text:
            flash('Please enter your feedback before submitting.', 'error')
            return render_template('student/student_feedback.html')
        
        try:
            student_id = session.get('user_id')
            conn = get_db()
            cur = conn.cursor()
            
            # Insert feedback into database
            cur.execute('''
                INSERT INTO feedback (student_id, feedback_text, submitted_on)
                VALUES (?, ?, datetime('now'))
            ''', (student_id, feedback_text))
            
            conn.commit()
            conn.close()
            
            flash('Thank you! Your feedback has been submitted successfully.', 'success')
            return render_template('student/student_feedback.html', feedback_submitted=True)
            
        except Exception as e:
            flash('An error occurred while submitting your feedback. Please try again.', 'error')
            if conn:
                conn.close()
            return render_template('student/student_feedback.html')
    
    return render_template('student/student_feedback.html')

@student_bp.route('/announcements')
def announcements():
    """View announcements"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get announcements for student's enrolled classes
        cur.execute('''
            SELECT DISTINCT
                a.id, a.title, a.content, a.created_at, a.priority,
                u.name as teacher_name, c.name as class_name
            FROM announcements a
            JOIN users u ON a.teacher_id = u.id
            LEFT JOIN classes c ON a.class_id = c.id
            LEFT JOIN student_class_map scm ON c.id = scm.class_id
            WHERE a.is_active = 1 
            AND (a.class_id IS NULL OR scm.student_id = ?)
            ORDER BY a.created_at DESC
            LIMIT 50
        ''', (student_id,))
        
        announcements_data = []
        for row in cur.fetchall():
            announcements_data.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'created_at': row[3],
                'priority': row[4] or 'normal',
                'teacher_name': row[5],
                'class_name': row[6] or 'All Students'
            })
        
        return render_template('student/student_announcements.html', 
                             announcements=announcements_data)
    
    except Exception as e:
        flash(f'Error loading announcements: {str(e)}', 'error')
        return render_template('student/student_announcements.html', 
                             announcements=[])
    finally:
        conn.close()

@student_bp.route('/doubts', methods=['GET', 'POST'])
def doubts():
    """Ask doubts/questions"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        doubt_text = request.form.get('doubt_text')
        
        if subject and doubt_text:
            # Insert new doubt
            cur.execute('''
                INSERT INTO doubts (student_id, subject, doubt_text, status)
                VALUES (?, ?, ?, 'open')
            ''', (student_id, subject, doubt_text))
            conn.commit()
            flash('Your doubt has been submitted successfully!', 'success')
        else:
            flash('Please fill in all fields.', 'error')
    
    # Get student's doubts with replies
    cur.execute('''
        SELECT id, subject, doubt_text, status, submitted_on
        FROM doubts
        WHERE student_id = ?
        ORDER BY submitted_on DESC
    ''', (student_id,))
    
    doubts_data = []
    for row in cur.fetchall():
        doubt_id = row[0]
        
        # Get replies for this doubt
        cur.execute('''
            SELECT dr.reply_text, dr.created_at, u.name as teacher_name
            FROM doubt_replies dr
            JOIN users u ON dr.teacher_id = u.id
            WHERE dr.doubt_id = ?
            ORDER BY dr.created_at ASC
        ''', (doubt_id,))
        
        replies = []
        for reply_row in cur.fetchall():
            replies.append({
                'reply_text': reply_row[0],
                'created_at': reply_row[1],
                'teacher_name': reply_row[2]
            })
        
        doubts_data.append({
            'id': row[0],
            'subject': row[1],
            'doubt_text': row[2],
            'status': row[3],
            'submitted_on': row[4],
            'replies': replies
        })
    
    conn.close()
    return render_template('student/student_doubts.html', doubts=doubts_data)

@student_bp.route('/download_assignment/<int:assignment_id>')
def download_assignment(assignment_id):
    """Download assignment file"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verify student has access to this assignment through their classes
        cur.execute('''
            SELECT a.file_path, a.original_filename, a.title, c.name as class_name
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN student_class_map scm ON c.id = scm.class_id
            WHERE a.id = ? AND scm.student_id = ? AND a.status = 'active'
        ''', (assignment_id, student_id))
        
        result = cur.fetchone()
        if not result:
            flash('Assignment not found or access denied', 'error')
            return redirect(url_for('student.homework'))
        
        file_path, original_filename, assignment_title, class_name = result
        
        # Check if assignment has a file
        if not file_path or not original_filename:
            flash('No file attached to this assignment', 'warning')
            return redirect(url_for('student.homework'))
        
        # Construct full file path (handle both absolute and relative paths)
        if os.path.isabs(file_path):
            full_file_path = file_path
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
        else:
            full_file_path = os.path.join(os.getcwd(), file_path)
            directory = os.path.join(os.getcwd(), os.path.dirname(file_path))
            filename = os.path.basename(file_path)
        
        # Check if file exists
        if not os.path.exists(full_file_path):
            flash(f'Assignment file missing on server. Please contact the teacher. (Assignment: {assignment_title}, Class: {class_name})', 'error')
            return redirect(url_for('student.homework'))
        
        # Use send_from_directory for better security
        return send_from_directory(directory, filename, as_attachment=True, download_name=original_filename)
        
    except Exception as e:
        flash(f'Error downloading assignment: {str(e)}', 'error')
        return redirect(url_for('student.homework'))
    finally:
        conn.close()

@student_bp.route('/upload_submission', methods=['POST'])
def upload_submission():
    """Handle student assignment submission upload"""
    if 'role' not in session or session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    student_id = session.get('user_id')
    
    try:
        # Ensure upload directories exist
        ensure_upload_dirs()
        
        # Get form data
        assignment_id = request.form.get('assignment_id')
        
        # Validate assignment_id
        if not assignment_id:
            return jsonify({'success': False, 'message': 'Assignment ID is required'}), 400
        
        # Handle file upload
        uploaded_file = request.files.get('submission_file')
        if not uploaded_file or uploaded_file.filename == '':
            return jsonify({'success': False, 'message': 'Please select a file to upload'}), 400
        
        # Basic file validation
        file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'message': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Verify student has access to this assignment
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT a.id, a.title, c.name as class_name, a.due_date
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            JOIN student_class_map scm ON c.id = scm.class_id
            WHERE a.id = ? AND scm.student_id = ? AND a.status = 'active'
        ''', (assignment_id, student_id))
        
        assignment_info = cur.fetchone()
        if not assignment_info:
            conn.close()
            return jsonify({'success': False, 'message': 'Assignment not found or access denied'}), 403
        
        # Generate secure filename
        original_filename = uploaded_file.filename
        secure_name = secure_filename(original_filename)
        if not secure_name:  # Fallback if secure_filename returns empty
            secure_name = f"submission_{uuid.uuid4().hex[:8]}{file_ext}"
        unique_filename = f"{uuid.uuid4().hex}_{secure_name}"
        
        # Save file
        upload_dir = os.path.join(UPLOAD_FOLDER, 'submissions')
        absolute_file_path = os.path.join(upload_dir, unique_filename)
        uploaded_file.save(absolute_file_path)
        
        # Store relative path for consistent retrieval
        file_path = f"uploads/submissions/{unique_filename}"
        
        # Store submission information in database (replace if already exists)
        cur.execute('''
            INSERT OR REPLACE INTO submissions (
                assignment_id, student_id, file_path, original_filename, submitted_on, status
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (assignment_id, student_id, file_path, original_filename, datetime.now(), 'submitted'))
        
        conn.commit()
        submission_id = cur.lastrowid
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Submission uploaded successfully for "{assignment_info[1]}"!',
            'submission_id': submission_id
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'}), 500

@student_bp.route('/dashboard')
def dashboard():
    """Student dashboard"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    student_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get student's classes count
        cur.execute('SELECT COUNT(*) FROM student_class_map WHERE student_id = ?', (student_id,))
        enrolled_classes_count = cur.fetchone()[0]
        
        # Get pending assignments count
        cur.execute('''
            SELECT COUNT(*) FROM assignments a
            JOIN student_class_map scm ON a.class_id = scm.class_id
            WHERE scm.student_id = ? AND a.due_date >= date('now')
        ''', (student_id,))
        pending_assignments = cur.fetchone()[0]
        
        # Get announcements count
        cur.execute('SELECT COUNT(*) FROM announcements WHERE is_active = 1')
        announcements_count = cur.fetchone()[0]
        
        # Get notifications
        notifications = get_notifications(student_id, 'student')
        
        stats = {
            'enrolled_classes': enrolled_classes_count,
            'pending_assignments': pending_assignments,
            'announcements_count': announcements_count,
            'total_subjects': 0
        }
        
        return render_template('student/student_dashboard_new.html',
                             stats=stats,
                             notifications=notifications)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        stats = {'enrolled_classes': 0, 'pending_assignments': 0, 'announcements_count': 0, 'total_subjects': 0}
        return render_template('student/student_dashboard_new.html',
                             stats=stats,
                             notifications=[])
    finally:
        conn.close()

@student_bp.route('/submit_assignment', methods=['POST'])
def submit_assignment():
    """Submit assignment file"""
    if 'role' not in session or session['role'] != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    try:
        student_id = session.get('user_id')
        assignment_id = request.form.get('assignment_id')
        comment = request.form.get('comment', '')
        
        if not assignment_id:
            return jsonify({'success': False, 'message': 'Assignment ID is required'})
        
        # Handle file upload
        uploaded_file = request.files.get('submission_file')
        if not uploaded_file or not uploaded_file.filename:
            return jsonify({'success': False, 'message': 'Please select a file to submit'})
        
        # Create uploads directory
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'submissions')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        original_filename = uploaded_file.filename
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        uploaded_file.save(file_path)
        
        # Save submission to database
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO submissions (student_id, assignment_id, file_path, original_filename, comment, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, assignment_id, file_path, original_filename, comment, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Assignment submitted successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting assignment: {str(e)}'})
