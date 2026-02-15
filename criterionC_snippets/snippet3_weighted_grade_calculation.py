# snippet3_weighted_grade_calculation.py
# Demonstrates weighted grade calculation algorithm for student reports
# Source: routes/teacher.py, lines 870-890
























































def calculate_weighted_average(marks):
    """Calculate weighted average from assessment marks
    
    Args:
        marks: List of tuples containing (title, date, max_score, weight, score, comment)
    
    Returns:
        float: Weighted average percentage (0-100)
    """
    total_weighted_score = 0
    total_weight = 0
    
    for mark in marks:
        max_score = mark[2]
        weight = mark[3]
        score = mark[4]
        
        if score is not None:  # Only include completed assessments
            percentage = (score / max_score) * 100  # Convert to percentage
            total_weighted_score += percentage * weight  # Apply weight
            total_weight += weight
    
    # Calculate final weighted average
    weighted_average = total_weighted_score / total_weight if total_weight > 0 else 0
    return weighted_average

# Example usage in student report generation
def generate_student_report(student_id, class_id, subject_name, teacher_id, from_date=None, to_date=None):
    """Generate individual student report with weighted grades"""
    conn = get_db()
    cur = conn.cursor()
    
    # Build date filter for assessments
    date_filter = ""
    params = [class_id, subject_name, teacher_id, student_id]
    if from_date:
        date_filter += " AND a.assessment_date >= ?"
        params.append(from_date)
    if to_date:
        date_filter += " AND a.assessment_date <= ?"
        params.append(to_date)
    
    # Get student's marks with assessment details
    cur.execute(f'''
        SELECT 
            a.title,
            a.assessment_date,
            a.max_score,
            a.weight,
            m.score,
            m.comment
        FROM assessments a
        INNER JOIN marks m ON a.id = m.assessment_id
        WHERE a.class_id = ? AND a.subject_name = ? AND a.teacher_id = ? AND m.student_id = ?
        {date_filter}
        ORDER BY a.assessment_date DESC
    ''', params)
    
    marks = cur.fetchall()
    
    # Calculate weighted average using the algorithm above
    weighted_average = calculate_weighted_average(marks)
    
    conn.close()
    return marks, weighted_average
