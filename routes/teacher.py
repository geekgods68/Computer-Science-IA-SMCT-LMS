from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, send_from_directory
import sqlite3
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

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

def get_notifications(user_id, user_type='teacher'):
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

@teacher_bp.route('/dashboard')
def dashboard():
    """Teacher dashboard"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get assigned classes count
        cur.execute('SELECT COUNT(*) FROM teacher_class_map WHERE teacher_id = ?', (teacher_id,))
        assigned_classes_count = cur.fetchone()[0]
        
        # Get pending doubts count
        cur.execute('SELECT COUNT(*) FROM doubts WHERE status = "open"')
        pending_doubts_count = cur.fetchone()[0]
        
        # Get submissions to grade count
        cur.execute('''
            SELECT COUNT(*) FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            WHERE a.teacher_id = ? AND s.grade IS NULL
        ''', (teacher_id,))
        submissions_to_grade = cur.fetchone()[0]
        
        # Get notifications
        notifications = get_notifications(teacher_id, 'teacher')
        
        # Get today's schedule
        today = datetime.now().strftime('%A')
        cur.execute('''
            SELECT c.id, c.name, c.schedule_time_start, c.schedule_time_end
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            WHERE tcm.teacher_id = ? AND c.status = 'active'
            AND (c.schedule_days LIKE ? OR c.schedule_days LIKE ?)
            ORDER BY c.schedule_time_start
        ''', (teacher_id, f'%{today}%', f'%"{today}"%'))
        
        schedule_rows = cur.fetchall()
        todays_schedule = []
        for row in schedule_rows:
            todays_schedule.append({
                'id': row[0],
                'class_name': row[1],
                'time': f"{row[2]} - {row[3]}",
                'start_time': row[2],
                'end_time': row[3]
            })
        
        stats = {
            'assigned_classes': assigned_classes_count,
            'pending_doubts': pending_doubts_count,
            'submissions_to_grade': submissions_to_grade,
            'total_students': 0
        }
        
        return render_template('teacher/teacher_dashboard_new.html',
                             stats=stats,
                             todays_schedule=todays_schedule,
                             recent_notifications=[],
                             notifications=notifications)
    
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('teacher/teacher_dashboard_new.html',
                             stats={'assigned_classes': 0, 'pending_doubts': 0, 'submissions_to_grade': 0, 'total_students': 0},
                             todays_schedule=[],
                             recent_notifications=[],
                             notifications=[])
    finally:
        conn.close()

@teacher_bp.route('/schedule')
def schedule():
    """Teacher schedule page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get teacher's assigned classes using JOIN with teacher_class_map (same logic as my_classes)
        cur.execute('''
            SELECT c.id, c.name, c.subject, c.grade_level, c.description, c.section,
                   c.schedule_days, c.schedule_time_start, c.schedule_time_end, c.max_students,
                   COUNT(DISTINCT scm.student_id) as student_count,
                   COUNT(DISTINCT a.id) as assignment_count
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            LEFT JOIN student_class_map scm ON c.id = scm.class_id
            LEFT JOIN assignments a ON c.id = a.class_id
            WHERE tcm.teacher_id = ?
            GROUP BY c.id, c.name, c.subject, c.grade_level, c.description, c.section,
                     c.schedule_days, c.schedule_time_start, c.schedule_time_end, c.max_students
            ORDER BY c.name
        ''', (teacher_id,))
        
        all_classes = []
        for row in cur.fetchall():
            class_data = {
                'id': row[0],
                'name': row[1],
                'subject': row[2] or 'No Subject',
                'grade_level': row[3],
                'description': row[4],
                'section': row[5],
                'schedule_days': row[6],
                'schedule_time_start': row[7],
                'schedule_time_end': row[8],
                'max_students': row[9] or 0,
                'student_count': row[10] or 0,
                'assignment_count': row[11] or 0
            }
            all_classes.append(class_data)
        
        # Categorize classes based on schedule information
        classes_with_schedules = []
        classes_without_schedules = []
        
        for class_data in all_classes:
            # Consider a class to have a schedule if it has schedule_days or time info
            if class_data['schedule_days'] or class_data['schedule_time_start']:
                classes_with_schedules.append(class_data)
            else:
                classes_without_schedules.append(class_data)
        
        # Calculate statistics
        total_classes = len(all_classes)
        total_students = sum(cls['student_count'] for cls in all_classes)
        
        stats = {
            'total_classes': total_classes,
            'classes_with_pdf': len(classes_with_schedules),  # Classes with schedule info
            'classes_without_pdf': len(classes_without_schedules),  # Classes without schedule info
            'total_students': total_students
        }
        
        return render_template('teacher/schedule.html', 
                             stats=stats,
                             classes_with_schedules=classes_with_schedules,
                             classes_without_schedules=classes_without_schedules)
        
    except Exception as e:
        flash(f"Error loading schedule: {str(e)}", 'error')
        # Provide default empty data if there's an error
        stats = {
            'total_classes': 0,
            'classes_with_pdf': 0,
            'classes_without_pdf': 0,
            'total_students': 0
        }
        return render_template('teacher/schedule.html', 
                             stats=stats,
                             classes_with_schedules=[],
                             classes_without_schedules=[])
    
    finally:
        conn.close()

@teacher_bp.route('/homework')
def homework():
    """Teacher homework/assignments page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get teacher's classes
        cur.execute('''
            SELECT c.id, c.name, c.grade_level
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            WHERE tcm.teacher_id = ? AND c.status = 'active'
        ''', (teacher_id,))
        teacher_classes = cur.fetchall()
        
        # Get teacher subjects from assigned classes
        cur.execute('''
            SELECT DISTINCT c.subject
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            WHERE tcm.teacher_id = ? AND c.status = 'active' AND c.subject IS NOT NULL
            ORDER BY c.subject
        ''', (teacher_id,))
        teacher_subjects = cur.fetchall()
        
        # Get assignments
        cur.execute('''
            SELECT a.id, a.teacher_id, a.class_id, a.title, a.description, a.assignment_type,
                   a.due_date, a.points, a.file_path, a.original_filename, a.allow_late_submission, 
                   a.created_at, a.status, c.name as class_name,
                   COUNT(s.id) as submission_count,
                   (SELECT COUNT(*) FROM student_class_map WHERE class_id = a.class_id) as total_students
            FROM assignments a
            JOIN classes c ON a.class_id = c.id
            LEFT JOIN submissions s ON a.id = s.assignment_id
            WHERE a.teacher_id = ?
            GROUP BY a.id, a.teacher_id, a.class_id, a.title, a.description, a.assignment_type,
                     a.due_date, a.points, a.file_path, a.original_filename, a.allow_late_submission,
                     a.created_at, a.status, c.name
            ORDER BY a.created_at DESC
        ''', (teacher_id,))
        
        assignments_data = cur.fetchall()
        teacher_assignments = []
        
        for row in assignments_data:
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
            
            assignment = type('Assignment', (), {
                'id': row[0],
                'title': row[3],
                'description': row[4],
                'assignment_type': row[5],
                'due_date': due_date,
                'points': row[7],
                'file_path': row[8],
                'original_filename': row[9],
                'allow_late_submission': bool(row[10]),
                'created_on': created_on,
                'status': row[12] or 'active',
                'class_name': row[13],
                'submission_count': row[14] or 0,
                'total_students': row[15] or 0
            })()
            teacher_assignments.append(assignment)
        
        # Assignment statistics - calculate from real data
        total_assignments = len(teacher_assignments)
        active_assignments = len([a for a in teacher_assignments if a.status == 'active'])
        completed_assignments = len([a for a in teacher_assignments if a.status == 'completed'])
        
        # Calculate real average submission rate
        if teacher_assignments:
            total_possible_submissions = sum(a.total_students for a in teacher_assignments)
            total_actual_submissions = sum(a.submission_count for a in teacher_assignments)
            avg_submission_rate = round((total_actual_submissions / total_possible_submissions * 100) if total_possible_submissions > 0 else 0, 1)
        else:
            avg_submission_rate = 0
        
        assignment_stats = {
            'total': total_assignments,
            'active': active_assignments,
            'completed': completed_assignments,
            'avg_submission_rate': avg_submission_rate
        }
        
        return render_template('teacher/teacher_homework.html',
                             teacher_classes=teacher_classes,
                             teacher_subjects=teacher_subjects,
                             teacher_assignments=teacher_assignments,
                             assignment_stats=assignment_stats)
    
    except Exception as e:
        flash(f'Error loading homework page: {str(e)}', 'error')
        return render_template('teacher/teacher_homework.html',
                             teacher_classes=[],
                             teacher_subjects=[],
                             teacher_assignments=[],
                             assignment_stats={'total': 0, 'active': 0, 'completed': 0, 'avg_submission_rate': 0})
    finally:
        conn.close()

@teacher_bp.route('/doubts')
def doubts():
    """Teacher doubts/questions page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get doubts for classes taught by this teacher
        filter_status = request.args.get('filter', '')
        
        base_query = '''
            SELECT d.id, d.student_id, d.subject, d.doubt_text, d.status, 
                   d.submitted_on, d.resolved_on, d.resolved_by,
                   u.username as student_name
            FROM doubts d
            JOIN users u ON d.student_id = u.id
            JOIN student_class_map scm ON u.id = scm.student_id
            JOIN teacher_class_map tcm ON scm.class_id = tcm.class_id
            WHERE tcm.teacher_id = ?
        '''
        
        params = [teacher_id]
        
        if filter_status == 'pending':
            base_query += " AND d.status = 'open'"
        elif filter_status == 'resolved':
            base_query += " AND d.status = 'resolved'"
        
        base_query += " ORDER BY d.submitted_on DESC"
        
        cur.execute(base_query, params)
        doubts_data = cur.fetchall()
        
        doubts = []
        for row in doubts_data:
            doubt = {
                'id': row[0],
                'student_id': row[1],
                'subject': row[2],
                'doubt_text': row[3],
                'status': row[4],
                'submitted_on': row[5],
                'resolved_on': row[6],
                'resolved_by': row[7],
                'student_name': row[8]
            }
            doubts.append(doubt)
        
        # Get statistics
        cur.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN d.status = 'open' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN d.status = 'resolved' THEN 1 ELSE 0 END) as resolved
            FROM doubts d
            JOIN users u ON d.student_id = u.id
            JOIN student_class_map scm ON u.id = scm.student_id
            JOIN teacher_class_map tcm ON scm.class_id = tcm.class_id
            WHERE tcm.teacher_id = ?
        ''', (teacher_id,))
        
        stats = cur.fetchone()
        doubt_stats = {
            'total': stats[0] or 0,
            'pending': stats[1] or 0,
            'resolved': stats[2] or 0
        }
        
        return render_template('teacher/doubts.html', 
                             doubts=doubts,
                             doubt_stats=doubt_stats,
                             filter_status=filter_status)
    
    except Exception as e:
        flash(f'Error loading doubts: {str(e)}', 'error')
        return render_template('teacher/doubts.html',
                             doubts=[],
                             doubt_stats={'total': 0, 'pending': 0, 'resolved': 0},
                             filter_status='')
    finally:
        conn.close()

@teacher_bp.route('/attendance')
def attendance():
    """Teacher attendance page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    return render_template('teacher/attendance.html')

@teacher_bp.route('/my_classes')
def my_classes():
    """Teacher classes page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get teacher's assigned classes using JOIN with teacher_class_map
        cur.execute('''
            SELECT c.id, c.name, c.subject, c.grade_level, c.description, c.section,
                   c.schedule_days, c.schedule_time_start, c.schedule_time_end, c.max_students,
                   COUNT(DISTINCT scm.student_id) as student_count,
                   COUNT(DISTINCT a.id) as assignment_count
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            LEFT JOIN student_class_map scm ON c.id = scm.class_id
            LEFT JOIN assignments a ON c.id = a.class_id
            WHERE tcm.teacher_id = ?
            GROUP BY c.id, c.name, c.subject, c.grade_level, c.description, c.section,
                     c.schedule_days, c.schedule_time_start, c.schedule_time_end, c.max_students
            ORDER BY c.name
        ''', (teacher_id,))
        
        classes = []
        for row in cur.fetchall():
            classes.append({
                'id': row[0],
                'name': row[1],
                'subject': row[2] or 'No Subject',
                'grade_level': row[3],
                'description': row[4],
                'section': row[5],
                'schedule_days': row[6],
                'schedule_time_start': row[7],
                'schedule_time_end': row[8],
                'max_students': row[9] or 0,
                'student_count': row[10] or 0,
                'assignment_count': row[11] or 0
            })
        
    except Exception as e:
        flash(f"Error loading classes: {str(e)}", 'error')
        classes = []
    finally:
        conn.close()
    
    return render_template('teacher/my_classes.html', classes=classes)

@teacher_bp.route('/upload_assignment', methods=['POST'])
def upload_assignment():
    """Upload a new assignment"""
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    teacher_id = session.get('user_id')
    
    try:
        # Ensure upload directories exist
        ensure_upload_dirs()
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description', '')
        class_id = request.form.get('class_id')
        assignment_type = request.form.get('assignment_type', 'homework')
        due_date = request.form.get('due_date')
        points = request.form.get('points', 100)
        allow_late_submission = request.form.get('allow_late_submission') == 'on'
        
        # Validation
        if not all([title, class_id, due_date]):
            return jsonify({'success': False, 'message': 'Title, class, and due date are required'}), 400
        
        # Handle file upload
        uploaded_file = request.files.get('assignment_file')
        file_path = None
        original_filename = None
        
        if uploaded_file and uploaded_file.filename:
            # Validate file extension
            file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                return jsonify({'success': False, 'message': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
            
            # Generate secure filename
            original_filename = uploaded_file.filename
            secure_name = secure_filename(original_filename)
            if not secure_name:  # Fallback if secure_filename returns empty
                secure_name = f"assignment_{uuid.uuid4().hex[:8]}{file_ext}"
            unique_filename = f"{uuid.uuid4().hex}_{secure_name}"
            
            # Save file
            upload_dir = os.path.join(UPLOAD_FOLDER, 'assignments')
            absolute_file_path = os.path.join(upload_dir, unique_filename)
            uploaded_file.save(absolute_file_path)
            
            # Store relative path for consistent retrieval
            file_path = f"uploads/assignments/{unique_filename}"
        
        # Save to database
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO assignments (teacher_id, class_id, title, description, assignment_type,
                                   due_date, points, file_path, original_filename, allow_late_submission, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, class_id, title, description, assignment_type, due_date, 
              points, file_path, original_filename, allow_late_submission, datetime.now(), 'active'))
        
        conn.commit()
        assignment_id = cur.lastrowid
        conn.close()
        
        message = f'Assignment "{title}" uploaded successfully!'
        if file_path:
            message += f' File "{original_filename}" attached.'
        
        return jsonify({'success': True, 'message': message, 'assignment_id': assignment_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error uploading assignment: {str(e)}'}), 500

@teacher_bp.route('/submissions')
def submissions():
    """View assignment submissions"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    assignment_id = request.args.get('assignment_id')
    teacher_id = session.get('user_id')
    
    if assignment_id:
        # Show specific assignment submissions with student details
        conn = get_db()
        cur = conn.cursor()
        
        try:
            # Get assignment details
            cur.execute('''
                SELECT a.id, a.title, c.name as class_name
                FROM assignments a 
                JOIN classes c ON a.class_id = c.id
                WHERE a.id = ? AND a.teacher_id = ?
            ''', (assignment_id, teacher_id))
            
            assignment = cur.fetchone()
            if not assignment:
                flash('Assignment not found or access denied', 'error')
                return redirect(url_for('teacher.submissions'))
            
            # Get submissions for this assignment
            cur.execute('''
                SELECT s.id, s.student_id, u.name as student_name, s.original_filename,
                       s.submitted_on, s.file_path
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                WHERE s.assignment_id = ?
                ORDER BY s.submitted_on DESC
            ''', (assignment_id,))
            
            submissions = []
            for row in cur.fetchall():
                submissions.append({
                    'id': row[0],
                    'student_id': row[1], 
                    'student_name': row[2],
                    'filename': row[3],
                    'submitted_on': row[4],
                    'file_exists': os.path.exists(os.path.join(os.getcwd(), row[5])) if row[5] else False
                })
            
            return render_template('teacher/assignment_submissions.html', 
                                 assignment=assignment, submissions=submissions)
                                 
        except Exception as e:
            flash(f'Error loading submissions: {str(e)}', 'error')
            return redirect(url_for('teacher.submissions'))
        finally:
            conn.close()
    else:
        # Show all assignments with submission counts
        conn = get_db()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT a.id, a.title, a.class_id, c.name as class_name,
                       COUNT(s.id) as submission_count
                FROM assignments a
                LEFT JOIN classes c ON a.class_id = c.id
                LEFT JOIN submissions s ON a.id = s.assignment_id
                WHERE a.teacher_id = ?
                GROUP BY a.id, a.title, a.class_id, c.name
                ORDER BY a.created_at DESC
            ''', (teacher_id,))
            
            assignments = cur.fetchall()
            
            return render_template('teacher/submissions_overview.html', assignments=assignments)
            
        except Exception as e:
            flash(f'Error loading submissions: {str(e)}', 'error')
            return redirect(url_for('teacher.homework'))
        finally:
            conn.close()

@teacher_bp.route('/marks_roster')
def marks_roster():
    """Teacher marks and reports page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    view_type = request.args.get('view', 'marks')  # 'marks' or 'reports'
    conn = get_db()
    cur = conn.cursor()
    
    # Get teacher's classes
    cur.execute('''
        SELECT c.id, c.name, c.subject, c.grade_level
        FROM classes c
        JOIN teacher_class_map tcm ON c.id = tcm.class_id
        WHERE tcm.teacher_id = ?
        ORDER BY c.name
    ''', (teacher_id,))
    
    classes = []
    for row in cur.fetchall():
        classes.append({
            'id': row[0],
            'name': row[1],
            'subject': row[2],
            'grade_level': row[3]
        })
    
    # Get assignments for the selected class (default to first class if available)
    selected_class_id = request.args.get('class_id', type=int)
    assignments = []
    students_data = []
    
    if not selected_class_id and classes:
        selected_class_id = classes[0]['id']
    
    if selected_class_id:
        # Get assignments for the selected class
        cur.execute('''
            SELECT id, title, points, assignment_type, due_date
            FROM assignments
            WHERE class_id = ? AND teacher_id = ?
            ORDER BY due_date DESC
        ''', (selected_class_id, teacher_id))
        
        for row in cur.fetchall():
            assignments.append({
                'id': row[0],
                'title': row[1],
                'total_marks': row[2] or 100,  # Use points as total_marks
                'type': row[3],
                'due_date': row[4]
            })
        
        # Get students in the selected class with their marks
        cur.execute('''
            SELECT DISTINCT u.id, u.name, u.username
            FROM users u
            JOIN student_class_map scm ON u.id = scm.student_id
            WHERE scm.class_id = ? AND u.role = 'student'
            ORDER BY u.name
        ''', (selected_class_id,))
        
        for student_row in cur.fetchall():
            student_id = student_row[0]
            student_data = {
                'id': student_id,
                'name': student_row[1],
                'username': student_row[2],
                'marks': {},
                'total_obtained': 0,
                'total_possible': 0,
                'percentage': 0,
                'grade': 'N/A'
            }
            
            # Get marks for each assignment
            for assignment in assignments:
                cur.execute('''
                    SELECT marks_obtained, total_marks, grade, remarks
                    FROM student_marks
                    WHERE student_id = ? AND assignment_id = ?
                ''', (student_id, assignment['id']))
                
                mark_row = cur.fetchone()
                if mark_row:
                    student_data['marks'][assignment['id']] = {
                        'obtained': mark_row[0],
                        'total': mark_row[1],
                        'grade': mark_row[2],
                        'remarks': mark_row[3]
                    }
                    student_data['total_obtained'] += mark_row[0] or 0
                else:
                    student_data['marks'][assignment['id']] = {
                        'obtained': None,
                        'total': assignment['total_marks'],
                        'grade': None,
                        'remarks': None
                    }
                
                student_data['total_possible'] += assignment['total_marks']
            
            # Calculate overall percentage and grade
            if student_data['total_possible'] > 0:
                student_data['percentage'] = round((student_data['total_obtained'] / student_data['total_possible']) * 100, 2)
                student_data['grade'] = calculate_grade(student_data['percentage'])
            
            students_data.append(student_data)
    
    conn.close()
    
    if view_type == 'reports':
        return render_template('teacher/marks_reports.html',
                             classes=classes,
                             selected_class_id=selected_class_id,
                             assignments=assignments,
                             students_data=students_data,
                             view_type=view_type)
    else:
        return render_template('teacher/marks_roster.html',
                             classes=classes,
                             selected_class_id=selected_class_id,
                             assignments=assignments,
                             students_data=students_data,
                             view_type=view_type)

def calculate_grade(percentage):
    """Calculate letter grade based on percentage"""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B+'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C'
    elif percentage >= 40:
        return 'D'
    else:
        return 'F'

@teacher_bp.route('/my_announcements', methods=['GET', 'POST'])
def my_announcements():
    """Teacher announcements page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            priority = request.form.get('priority', 'normal')
            class_id = request.form.get('class_id')
            target_audience = request.form.get('target_audience', 'class')
            
            if not title or not content:
                flash('Title and content are required.', 'error')
            else:
                # Insert new announcement
                cur.execute('''
                    INSERT INTO announcements (teacher_id, class_id, title, content, priority, target_audience)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (teacher_id, class_id if class_id else None, title, content, priority, target_audience))
                
                conn.commit()
                flash('Announcement posted successfully!', 'success')
                
        except Exception as e:
            flash(f'Error creating announcement: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('teacher.my_announcements'))
    
    try:
        # Get teacher's classes for the dropdown
        cur.execute('''
            SELECT c.id, c.name, c.grade_level
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            WHERE tcm.teacher_id = ? AND c.status = 'active'
            ORDER BY c.name
        ''', (teacher_id,))
        
        teacher_classes = []
        for row in cur.fetchall():
            teacher_classes.append({
                'id': row[0],
                'name': row[1],
                'grade_level': row[2]
            })
        
        # Get teacher's announcements
        view_filter = request.args.get('view', 'all')
        
        base_query = '''
            SELECT a.id, a.title, a.content, a.priority, a.created_at, a.is_active,
                   a.target_audience, c.name as class_name
            FROM announcements a
            LEFT JOIN classes c ON a.class_id = c.id
            WHERE a.teacher_id = ?
        '''
        
        params = [teacher_id]
        
        if view_filter == 'active':
            base_query += " AND a.is_active = 1"
        elif view_filter == 'inactive':
            base_query += " AND a.is_active = 0"
        
        base_query += " ORDER BY a.created_at DESC"
        
        cur.execute(base_query, params)
        
        announcements = []
        for row in cur.fetchall():
            announcements.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'priority': row[3],
                'created_at': row[4],
                'is_active': row[5],
                'target_audience': row[6],
                'class_name': row[7] if row[7] else 'All Classes'
            })
        
        return render_template('teacher/my_announcements.html',
                             announcements=announcements,
                             teacher_classes=teacher_classes,
                             view_filter=view_filter)
        
    except Exception as e:
        flash(f'Error loading announcements: {str(e)}', 'error')
        return render_template('teacher/my_announcements.html',
                             announcements=[],
                             teacher_classes=[],
                             view_filter='all')
    finally:
        conn.close()

@teacher_bp.route('/my_attendance')
def my_attendance():
    """Teacher attendance reports page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get teacher's classes
        cur.execute('''
            SELECT DISTINCT c.id, c.name, c.subject
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            WHERE tcm.teacher_id = ?
            ORDER BY c.name
        ''', (teacher_id,))
        teacher_classes = cur.fetchall()
        
        # Get selected class ID from query parameter
        selected_class_id = request.args.get('class_id', type=int)
        selected_class = None
        attendance_data = []
        attendance_summary = {}
        
        if selected_class_id:
            # Verify teacher has access to this class
            class_ids = [cls[0] for cls in teacher_classes]
            if selected_class_id in class_ids:
                # Get class details
                selected_class = next((cls for cls in teacher_classes if cls[0] == selected_class_id), None)
                
                # Get date filters
                start_date = request.args.get('start_date', '')
                end_date = request.args.get('end_date', '')
                status_filter = request.args.get('status', '')
                
                # Build attendance query
                attendance_query = '''
                    SELECT 
                        a.id,
                        a.attendance_date,
                        a.status,
                        a.notes,
                        u.name as student_name,
                        u.id as student_id
                    FROM attendance a
                    JOIN users u ON a.student_id = u.id
                    WHERE a.class_id = ? AND a.marked_by = ?
                '''
                params = [selected_class_id, teacher_id]
                
                if start_date:
                    attendance_query += ' AND a.attendance_date >= ?'
                    params.append(start_date)
                
                if end_date:
                    attendance_query += ' AND a.attendance_date <= ?'
                    params.append(end_date)
                
                if status_filter:
                    attendance_query += ' AND a.status = ?'
                    params.append(status_filter)
                
                attendance_query += ' ORDER BY a.attendance_date DESC, u.first_name, u.last_name'
                
                cur.execute(attendance_query, params)
                attendance_records = cur.fetchall()
                
                # Organize data by date for better display
                attendance_by_date = {}
                for record in attendance_records:
                    date = record[1]
                    if date not in attendance_by_date:
                        attendance_by_date[date] = []
                    attendance_by_date[date].append({
                        'id': record[0],
                        'student_name': record[4],
                        'student_id': record[5],
                        'status': record[2],
                        'notes': record[3] or ''
                    })
                
                attendance_data = attendance_by_date
                
                # Calculate attendance summary
                cur.execute('''
                    SELECT 
                        status,
                        COUNT(*) as count
                    FROM attendance
                    WHERE class_id = ? AND marked_by = ?
                    GROUP BY status
                ''', (selected_class_id, teacher_id))
                
                status_counts = dict(cur.fetchall())
                total_records = sum(status_counts.values())
                
                attendance_summary = {
                    'total_records': total_records,
                    'present': status_counts.get('present', 0),
                    'absent': status_counts.get('absent', 0),
                    'late': status_counts.get('late', 0),
                    'excused': status_counts.get('excused', 0),
                    'present_percentage': round((status_counts.get('present', 0) / total_records * 100), 1) if total_records > 0 else 0
                }
        
        conn.close()
        
        return render_template('teacher/my_attendance.html',
                             teacher_classes=teacher_classes,
                             selected_class=selected_class,
                             selected_class_id=selected_class_id,
                             attendance_data=attendance_data,
                             attendance_summary=attendance_summary,
                             filters={
                                 'start_date': request.args.get('start_date', ''),
                                 'end_date': request.args.get('end_date', ''),
                                 'status': request.args.get('status', '')
                             })
    
    except Exception as e:
        print(f"Error in my_attendance: {e}")
        flash('Error loading attendance data', 'error')
        conn.close()
        return render_template('teacher/my_attendance.html', teacher_classes=[], error=str(e))

@teacher_bp.route('/edit_assignment', methods=['POST'])
def edit_assignment():
    """Edit assignment details"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    try:
        teacher_id = session.get('user_id')
        assignment_id = request.form.get('assignment_id')
        title = request.form.get('title')
        description = request.form.get('description')
        due_date = request.form.get('due_date')
        
        if not assignment_id or not title:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        conn = get_db()
        cur = conn.cursor()
        
        # Verify assignment belongs to teacher
        cur.execute('SELECT id FROM assignments WHERE id = ? AND teacher_id = ?', 
                   (assignment_id, teacher_id))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Assignment not found'})
        
        # Update assignment
        cur.execute('''UPDATE assignments 
                      SET title = ?, description = ?, due_date = ? 
                      WHERE id = ? AND teacher_id = ?''',
                   (title, description, due_date, assignment_id, teacher_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Assignment updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating assignment: {str(e)}'})

@teacher_bp.route('/download_submission/<int:submission_id>')
def download_submission(submission_id):
    """Download a student submission file"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verify teacher has access to this submission
        cur.execute('''
            SELECT s.file_path, s.original_filename, a.title, u.name as student_name
            FROM submissions s
            JOIN assignments a ON s.assignment_id = a.id
            JOIN users u ON s.student_id = u.id
            WHERE s.id = ? AND a.teacher_id = ?
        ''', (submission_id, teacher_id))
        
        result = cur.fetchone()
        
        if not result:
            flash('Submission not found or access denied', 'error')
            return redirect(url_for('teacher.submissions'))
        
        file_path, original_filename, assignment_title, student_name = result
        
        if not file_path or not original_filename:
            flash('No file attached to this submission', 'warning')
            return redirect(url_for('teacher.submissions'))
        
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
            flash(f'Submission file missing on server. Please contact the administrator. (Student: {student_name}, Assignment: {assignment_title})', 'error')
            return redirect(url_for('teacher.submissions'))
        
        # Use send_from_directory for better security
        return send_from_directory(directory, filename, as_attachment=True, download_name=original_filename)
            
    except Exception as e:
        flash(f'Error downloading submission: {str(e)}', 'error')
        return redirect(url_for('teacher.submissions'))
    finally:
        conn.close()

@teacher_bp.route('/save_attendance', methods=['POST'])
def save_attendance():
    """Save attendance data"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    # Placeholder implementation
    flash('Attendance saved successfully', 'success')
    return redirect(url_for('teacher.my_attendance'))

@teacher_bp.route('/create_announcement', methods=['POST'])
def create_announcement():
    """Create a new announcement"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    # Placeholder implementation
    flash('Announcement created successfully', 'success')
    return redirect(url_for('teacher.my_announcements'))

@teacher_bp.route('/toggle_announcement/<int:announcement_id>', methods=['POST'])
def toggle_announcement(announcement_id):
    """Toggle announcement active/inactive status"""
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verify the announcement belongs to this teacher
        cur.execute('SELECT is_active FROM announcements WHERE id = ? AND teacher_id = ?', 
                   (announcement_id, teacher_id))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': 'Announcement not found'})
        
        # Toggle the active status
        new_status = 1 if result[0] == 0 else 0
        cur.execute('UPDATE announcements SET is_active = ? WHERE id = ?', 
                   (new_status, announcement_id))
        conn.commit()
        
        status_text = 'activated' if new_status == 1 else 'deactivated'
        flash(f'Announcement {status_text} successfully!', 'success')
        
        return jsonify({'success': True, 'new_status': new_status})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@teacher_bp.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
def delete_announcement(announcement_id):
    """Delete an announcement"""
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Verify the announcement belongs to this teacher
        cur.execute('SELECT id FROM announcements WHERE id = ? AND teacher_id = ?', 
                   (announcement_id, teacher_id))
        result = cur.fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': 'Announcement not found'})
        
        # Delete the announcement
        cur.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))
        conn.commit()
        
        flash('Announcement deleted successfully!', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@teacher_bp.route('/create_assessment', methods=['GET', 'POST'])
def create_assessment():
    """Create a new assessment"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Placeholder implementation
        flash('Assessment created successfully', 'success')
        return redirect(url_for('teacher.marks_roster'))
    
    # Return a simple form or redirect
    return redirect(url_for('teacher.marks_roster'))

@teacher_bp.route('/save_marks', methods=['POST'])
def save_marks():
    """Save student marks"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    class_id = request.form.get('class_id', type=int)
    assignment_id = request.form.get('assignment_id', type=int)
    
    if not class_id or not assignment_id:
        flash('Missing class or assignment information', 'error')
        return redirect(url_for('teacher.marks_roster'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verify that this assignment belongs to this teacher
    cur.execute('SELECT points FROM assignments WHERE id = ? AND teacher_id = ?', 
               (assignment_id, teacher_id))
    assignment = cur.fetchone()
    
    if not assignment:
        flash('Assignment not found or unauthorized access', 'error')
        conn.close()
        return redirect(url_for('teacher.marks_roster'))
    
    total_marks = assignment[0] or 100
    marks_saved = 0
    
    try:
        # Process each student's marks
        for key in request.form:
            if key.startswith('marks_'):
                student_id = int(key.split('_')[1])
                marks_obtained = request.form.get(key)
                remarks = request.form.get(f'remarks_{student_id}', '')
                
                if marks_obtained and marks_obtained.strip():
                    marks_obtained = float(marks_obtained)
                    
                    # Validate marks
                    if marks_obtained < 0 or marks_obtained > total_marks:
                        flash(f'Invalid marks for student ID {student_id}. Must be between 0 and {total_marks}', 'error')
                        continue
                    
                    # Calculate percentage and grade
                    percentage = (marks_obtained / total_marks) * 100
                    grade = calculate_grade(percentage)
                    
                    # Check if marks already exist for this student and assignment
                    cur.execute('''
                        SELECT id FROM student_marks 
                        WHERE student_id = ? AND assignment_id = ?
                    ''', (student_id, assignment_id))
                    
                    existing_mark = cur.fetchone()
                    
                    if existing_mark:
                        # Update existing marks
                        cur.execute('''
                            UPDATE student_marks 
                            SET marks_obtained = ?, total_marks = ?, percentage = ?, 
                                grade = ?, remarks = ?, marked_by = ?, marked_at = CURRENT_TIMESTAMP
                            WHERE student_id = ? AND assignment_id = ?
                        ''', (marks_obtained, total_marks, percentage, grade, remarks, 
                             teacher_id, student_id, assignment_id))
                    else:
                        # Insert new marks
                        cur.execute('''
                            INSERT INTO student_marks (student_id, assignment_id, class_id, 
                                                     marks_obtained, total_marks, percentage, 
                                                     grade, remarks, marked_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (student_id, assignment_id, class_id, marks_obtained, 
                             total_marks, percentage, grade, remarks, teacher_id))
                    
                    marks_saved += 1
        
        conn.commit()
        flash(f'Successfully saved marks for {marks_saved} students', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error saving marks: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('teacher.marks_roster', class_id=class_id))

@teacher_bp.route('/generate_report/<int:class_id>')
def generate_report(class_id):
    """Generate class report"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    # Verify teacher has access to this class
    cur.execute('''
        SELECT c.name, c.subject, c.grade_level
        FROM classes c
        JOIN teacher_class_map tcm ON c.id = tcm.class_id
        WHERE c.id = ? AND tcm.teacher_id = ?
    ''', (class_id, teacher_id))
    
    class_info = cur.fetchone()
    if not class_info:
        flash('Class not found or unauthorized access', 'error')
        conn.close()
        return redirect(url_for('teacher.marks_roster'))
    
    # Get comprehensive report data
    cur.execute('''
        SELECT u.name, u.username, 
               AVG(sm.percentage) as avg_percentage,
               COUNT(sm.id) as total_assessments,
               MIN(sm.percentage) as min_percentage,
               MAX(sm.percentage) as max_percentage
        FROM users u
        JOIN student_class_map scm ON u.id = scm.student_id
        LEFT JOIN student_marks sm ON u.id = sm.student_id AND sm.class_id = ?
        WHERE scm.class_id = ? AND u.role = 'student'
        GROUP BY u.id, u.name, u.username
        ORDER BY avg_percentage DESC
    ''', (class_id, class_id))
    
    students_report = []
    for i, row in enumerate(cur.fetchall()):
        students_report.append({
            'rank': i + 1,
            'name': row[0],
            'username': row[1],
            'avg_percentage': round(row[2] or 0, 2),
            'grade': calculate_grade(row[2] or 0),
            'total_assessments': row[3],
            'min_percentage': round(row[4] or 0, 2),
            'max_percentage': round(row[5] or 0, 2)
        })
    
    # Get assignment statistics
    cur.execute('''
        SELECT a.title, a.points, 
               AVG(sm.marks_obtained) as avg_marks,
               COUNT(sm.id) as submissions,
               MIN(sm.marks_obtained) as min_marks,
               MAX(sm.marks_obtained) as max_marks
        FROM assignments a
        LEFT JOIN student_marks sm ON a.id = sm.assignment_id
        WHERE a.class_id = ? AND a.teacher_id = ?
        GROUP BY a.id, a.title, a.points
        ORDER BY a.due_date DESC
    ''', (class_id, teacher_id))
    
    assignment_stats = []
    for row in cur.fetchall():
        total_marks = row[1] or 100
        assignment_stats.append({
            'title': row[0],
            'total_marks': total_marks,
            'avg_marks': round(row[2] or 0, 2),
            'avg_percentage': round((row[2] or 0) / total_marks * 100, 2),
            'submissions': row[3],
            'min_marks': row[4] or 0,
            'max_marks': row[5] or 0
        })
    
    conn.close()
    
    return render_template('teacher/class_report.html',
                         class_info={'name': class_info[0], 'subject': class_info[1], 'grade': class_info[2]},
                         students_report=students_report,
                         assignment_stats=assignment_stats,
                         class_id=class_id)

@teacher_bp.route('/resolve_doubt', methods=['POST'])
def resolve_doubt():
    """Resolve a student doubt"""
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    teacher_id = session.get('user_id')
    doubt_id = request.form.get('doubt_id')
    
    if not doubt_id:
        return jsonify({'success': False, 'message': 'Doubt ID is required'})
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Verify the doubt belongs to a student in teacher's class
        cur.execute('''
            SELECT d.id FROM doubts d
            JOIN users u ON d.student_id = u.id
            JOIN student_class_map scm ON u.id = scm.student_id
            JOIN teacher_class_map tcm ON scm.class_id = tcm.class_id
            WHERE d.id = ? AND tcm.teacher_id = ?
        ''', (doubt_id, teacher_id))
        
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Unauthorized to resolve this doubt'})
        
        # Update doubt status to resolved
        cur.execute('''
            UPDATE doubts 
            SET status = 'resolved', 
                resolved_on = datetime('now'), 
                resolved_by = ?
            WHERE id = ?
        ''', (teacher_id, doubt_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Doubt marked as resolved successfully'})
        
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Error resolving doubt: {str(e)}'})

@teacher_bp.route('/reply_doubt', methods=['POST'])
def reply_doubt():
    """Reply to a student doubt"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    doubt_id = request.form.get('doubt_id')
    reply_text = request.form.get('reply_text', '').strip()
    
    if not doubt_id or not reply_text:
        flash('Doubt ID and reply text are required', 'error')
        return redirect(url_for('teacher.doubts'))
    
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Verify the doubt belongs to a student in teacher's class
        cur.execute('''
            SELECT d.id FROM doubts d
            JOIN users u ON d.student_id = u.id
            JOIN student_class_map scm ON u.id = scm.student_id
            JOIN teacher_class_map tcm ON scm.class_id = tcm.class_id
            WHERE d.id = ? AND tcm.teacher_id = ?
        ''', (doubt_id, teacher_id))
        
        if not cur.fetchone():
            flash('Unauthorized to reply to this doubt', 'error')
            return redirect(url_for('teacher.doubts'))
        
        # Check if replies table exists, if not create it
        cur.execute('''
            CREATE TABLE IF NOT EXISTS doubt_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doubt_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                reply_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doubt_id) REFERENCES doubts (id),
                FOREIGN KEY (teacher_id) REFERENCES users (id)
            )
        ''')
        
        # Insert reply
        cur.execute('''
            INSERT INTO doubt_replies (doubt_id, teacher_id, reply_text)
            VALUES (?, ?, ?)
        ''', (doubt_id, teacher_id, reply_text))
        
        conn.commit()
        conn.close()
        
        flash('Reply sent successfully', 'success')
        return redirect(url_for('teacher.doubts'))
        
    except Exception as e:
        if conn:
            conn.close()
        flash(f'Error sending reply: {str(e)}', 'error')
        return redirect(url_for('teacher.doubts'))

@teacher_bp.route('/mark_student/<int:student_id>')
def mark_student(student_id):
    """Individual student marking page"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    class_id = request.args.get('class_id', type=int)
    
    if not class_id:
        flash('Class ID is required', 'error')
        return redirect(url_for('teacher.marks_roster'))
    
    conn = get_db()
    cur = conn.cursor()
    
    # Verify teacher has access to this class
    cur.execute('''
        SELECT c.id, c.name, c.subject, c.grade_level
        FROM classes c
        JOIN teacher_class_map tcm ON c.id = tcm.class_id
        WHERE c.id = ? AND tcm.teacher_id = ?
    ''', (class_id, teacher_id))
    
    class_info = cur.fetchone()
    if not class_info:
        flash('Class not found or unauthorized access', 'error')
        conn.close()
        return redirect(url_for('teacher.marks_roster'))
    
    # Get student information and verify they're in this class
    cur.execute('''
        SELECT u.id, u.name, u.username
        FROM users u
        JOIN student_class_map scm ON u.id = scm.student_id
        WHERE u.id = ? AND scm.class_id = ? AND u.role = 'student'
    ''', (student_id, class_id))
    
    student = cur.fetchone()
    if not student:
        flash('Student not found in this class', 'error')
        conn.close()
        return redirect(url_for('teacher.marks_roster', class_id=class_id))
    
    student_info = {
        'id': student[0],
        'name': student[1],
        'username': student[2]
    }
    
    # Get all assignments for this class with this student's marks
    cur.execute('''
        SELECT a.id, a.title, a.points, a.assignment_type, a.due_date,
               sm.marks_obtained, sm.total_marks, sm.grade, sm.remarks
        FROM assignments a
        LEFT JOIN student_marks sm ON a.id = sm.assignment_id AND sm.student_id = ?
        WHERE a.class_id = ? AND a.teacher_id = ?
        ORDER BY a.due_date DESC
    ''', (student_id, class_id, teacher_id))
    
    assignments = []
    for row in cur.fetchall():
        assignments.append({
            'id': row[0],
            'title': row[1],
            'total_marks': row[2] or 100,
            'type': row[3],
            'due_date': row[4],
            'marks_obtained': row[5],
            'student_total_marks': row[6],
            'grade': row[7],
            'remarks': row[8]
        })
    
    class_data = {
        'id': class_info[0],
        'name': class_info[1],
        'subject': class_info[2],
        'grade_level': class_info[3]
    }
    
    conn.close()
    
    return render_template('teacher/mark_individual_student.html',
                         student=student_info,
                         class_data=class_data,
                         assignments=assignments)

@teacher_bp.route('/save_individual_marks', methods=['POST'])
def save_individual_marks():
    """Save marks for individual student"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    student_id = request.form.get('student_id', type=int)
    class_id = request.form.get('class_id', type=int)
    
    if not student_id or not class_id:
        flash('Missing student or class information', 'error')
        return redirect(url_for('teacher.marks_roster'))
    
    conn = get_db()
    cur = conn.cursor()
    
    marks_saved = 0
    
    try:
        # Process each assignment's marks
        for key in request.form:
            if key.startswith('marks_'):
                assignment_id = int(key.split('_')[1])
                marks_obtained = request.form.get(key)
                remarks = request.form.get(f'remarks_{assignment_id}', '')
                
                # Verify assignment belongs to this teacher and class
                cur.execute('''
                    SELECT points FROM assignments 
                    WHERE id = ? AND teacher_id = ? AND class_id = ?
                ''', (assignment_id, teacher_id, class_id))
                
                assignment = cur.fetchone()
                if not assignment:
                    continue
                
                total_marks = assignment[0] or 100
                
                if marks_obtained and marks_obtained.strip():
                    marks_obtained = float(marks_obtained)
                    
                    # Validate marks
                    if marks_obtained < 0 or marks_obtained > total_marks:
                        flash(f'Invalid marks for assignment ID {assignment_id}. Must be between 0 and {total_marks}', 'error')
                        continue
                    
                    # Calculate percentage and grade
                    percentage = (marks_obtained / total_marks) * 100
                    grade = calculate_grade(percentage)
                    
                    # Check if marks already exist
                    cur.execute('''
                        SELECT id FROM student_marks 
                        WHERE student_id = ? AND assignment_id = ?
                    ''', (student_id, assignment_id))
                    
                    existing_mark = cur.fetchone()
                    
                    if existing_mark:
                        # Update existing marks
                        cur.execute('''
                            UPDATE student_marks 
                            SET marks_obtained = ?, total_marks = ?, percentage = ?, 
                                grade = ?, remarks = ?, marked_by = ?, marked_at = CURRENT_TIMESTAMP
                            WHERE student_id = ? AND assignment_id = ?
                        ''', (marks_obtained, total_marks, percentage, grade, remarks, 
                             teacher_id, student_id, assignment_id))
                    else:
                        # Insert new marks
                        cur.execute('''
                            INSERT INTO student_marks (student_id, assignment_id, class_id, 
                                                     marks_obtained, total_marks, percentage, 
                                                     grade, remarks, marked_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (student_id, assignment_id, class_id, marks_obtained, 
                             total_marks, percentage, grade, remarks, teacher_id))
                    
                    marks_saved += 1
                elif marks_obtained == '':  # Empty string means clear the marks
                    # Delete existing marks
                    cur.execute('''
                        DELETE FROM student_marks 
                        WHERE student_id = ? AND assignment_id = ?
                    ''', (student_id, assignment_id))
        
        conn.commit()
        if marks_saved > 0:
            flash(f'Successfully saved marks for {marks_saved} assignments', 'success')
        else:
            flash('No marks were updated', 'info')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error saving marks: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('teacher.mark_student', student_id=student_id, class_id=class_id))
