# snippet14_rollback.py
# Source: routes/teacher.py, lines 429-437

# Transaction rollback error handling in attendance marking
try:
    # Database operations (attendance marking)
    cur.execute('''
        INSERT INTO attendance (student_id, class_id, attendance_date, status, marked_by, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, class_id, attendance_date, status, teacher_id, notes))
    
    conn.commit()
    flash(f'Attendance marked for {attendance_saved} students', 'success')
    return redirect(url_for('teacher.attendance'))
    
except Exception as e:
    conn.rollback()
    flash(f'Error saving attendance: {str(e)}', 'error')
    return redirect(url_for('teacher.mark_attendance', class_id=class_id, date=attendance_date))
finally:
    conn.close()
