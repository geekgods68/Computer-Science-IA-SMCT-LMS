# snippet6_attendance_aggregation.py
# Demonstrates attendance data aggregation and reporting queries
# Source: routes/teacher.py, lines 270-320 and routes/admin.py attendance functions

def get_attendance_summary(class_id, from_date=None, to_date=None):
    """Generate attendance summary statistics for a class
    
    Args:
        class_id: ID of the class to analyze
        from_date: Start date for analysis (YYYY-MM-DD)
        to_date: End date for analysis (YYYY-MM-DD)
    
    Returns:
        dict: Attendance statistics including present/absent counts and percentages
    """
    conn = get_db()
    cur = conn.cursor()
    
    # Build date filter
    date_filter = ""
    params = [class_id]
    if from_date:
        date_filter += " AND attendance_date >= ?"
        params.append(from_date)
    if to_date:
        date_filter += " AND attendance_date <= ?"
        params.append(to_date)
    
    # Get attendance statistics aggregated by status
    cur.execute(f'''
        SELECT 
            status,
            COUNT(*) as count,
            COUNT(DISTINCT student_id) as unique_students,
            COUNT(DISTINCT attendance_date) as unique_dates
        FROM attendance a
        WHERE class_id = ? {date_filter}
        GROUP BY status
        ORDER BY status
    ''', params)
    
    status_counts = cur.fetchall()
    
    # Get overall class statistics
    cur.execute(f'''
        SELECT 
            COUNT(DISTINCT student_id) as total_students,
            COUNT(DISTINCT attendance_date) as total_dates,
            COUNT(*) as total_records
        FROM attendance a
        WHERE class_id = ? {date_filter}
    ''', params)
    
    overall_stats = cur.fetchone()
    
    # Calculate attendance percentages
    summary = {
        'total_students': overall_stats[0] if overall_stats else 0,
        'total_dates': overall_stats[1] if overall_stats else 0,
        'total_records': overall_stats[2] if overall_stats else 0,
        'by_status': {}
    }
    
    for status_data in status_counts:
        status = status_data[0]
        count = status_data[1]
        percentage = (count / summary['total_records'] * 100) if summary['total_records'] > 0 else 0
        
        summary['by_status'][status] = {
            'count': count,
            'percentage': round(percentage, 2)
        }
    
    conn.close()
    return summary

def get_student_attendance_record(student_id, class_id, from_date=None, to_date=None):
    """Get individual student's attendance record with trend analysis"""
    conn = get_db()
    cur = conn.cursor()
    
    # Build date filter
    date_filter = ""
    params = [student_id, class_id]
    if from_date:
        date_filter += " AND attendance_date >= ?"
        params.append(from_date)
    if to_date:
        date_filter += " AND attendance_date <= ?"
        params.append(to_date)
    
    # Get detailed attendance records
    cur.execute(f'''
        SELECT 
            attendance_date,
            status,
            remarks,
            marked_on
        FROM attendance
        WHERE student_id = ? AND class_id = ? {date_filter}
        ORDER BY attendance_date DESC
    ''', params)
    
    records = cur.fetchall()
    
    # Calculate attendance rate
    total_days = len(records)
    present_days = len([r for r in records if r[1] == 'present'])
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    conn.close()
    return {
        'records': records,
        'total_days': total_days,
        'present_days': present_days,
        'attendance_rate': round(attendance_rate, 2)
    }
