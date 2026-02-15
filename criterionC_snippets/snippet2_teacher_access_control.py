# snippet2_teacher_access_control.py
# Demonstrates teacher access control for class and subject assignments
# Source: routes/teacher.py, lines 445-463

def verify_teacher_access(teacher_id, class_id, subject_name):
    """Verify teacher has access to the given class and subject"""
    conn = get_db()
    cur = conn.cursor()
    
    # Check if teacher is assigned to the class
    cur.execute('''
        SELECT 1 FROM teacher_class_map 
        WHERE teacher_id = ? AND class_id = ?
    ''', (teacher_id, class_id))
    
    class_access = cur.fetchone() is not None
    
    # Check if teacher is assigned to the subject
    cur.execute('''
        SELECT 1 FROM teacher_subjects 
        WHERE teacher_id = ? AND subject_name = ?
    ''', (teacher_id, subject_name))
    
    subject_access = cur.fetchone() is not None
    
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
   
    conn.close()
    return class_access and subject_access

# Example usage in teacher routes with access control
@teacher_bp.route('/marks', methods=['GET'])
def marks():
    """Teacher marks management with access verification"""
    if 'role' not in session or session['role'] != 'teacher':
        return redirect(url_for('auth.login'))
    
    teacher_id = session.get('user_id')
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get teacher's assigned classes with student counts
        cur.execute('''
            SELECT 
                c.id, c.name, c.grade_level,
                COUNT(DISTINCT scm.student_id) as student_count
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            LEFT JOIN student_class_map scm ON c.id = scm.class_id AND scm.status = 'active'
            WHERE tcm.teacher_id = ? AND c.status = 'active'
            GROUP BY c.id
            ORDER BY c.grade_level, c.name
        ''', (teacher_id,))
        assigned_classes = cur.fetchall()
        
        # Get teacher's assigned subjects
        cur.execute('''
            SELECT DISTINCT subject_name 
            FROM teacher_subjects 
            WHERE teacher_id = ?
            ORDER BY subject_name
        ''', (teacher_id,))
        teacher_subjects = [row[0] for row in cur.fetchall()]
        
        return render_template('teacher/teacher_marks.html',
                             assigned_classes=assigned_classes,
                             teacher_subjects=teacher_subjects)
        
    except Exception as e:
        flash(f'Error loading marks data: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))
    finally:
        conn.close()
