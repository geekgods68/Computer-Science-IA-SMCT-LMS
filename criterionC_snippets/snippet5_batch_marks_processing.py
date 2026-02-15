# snippet5_batch_marks_processing.py
# Demonstrates batch marks processing with transaction handling
# Source: routes/teacher.py, lines 665-750

@teacher_bp.route('/marks/save', methods=['POST'])
def save_marks():
    """Save marks for multiple students in a single transaction"""
    if 'role' not in session or session['role'] != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    
    teacher_id = session.get('user_id')
    
    try:
        # Parse JSON request data
        data = request.get_json()
        assessment_id = data.get('assessment_id')
        items = data.get('items', [])  # List of student marks to save
        
        if not assessment_id or not items:
            return jsonify({'error': 'assessment_id and items are required'}), 400
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        
        # Verify teacher owns this assessment and get constraints
        cur.execute('''
            SELECT class_id, subject_name, max_score FROM assessments 
            WHERE id = ? AND teacher_id = ?
        ''', (assessment_id, teacher_id))
        
        assessment = cur.fetchone()
        if not assessment:
            return jsonify({'error': 'Assessment not found or access denied'}), 403
        
        max_score = assessment[2]
        
        # Process marks in transaction for data consistency
        results = {'saved': 0, 'updated': 0, 'skipped': 0, 'errors': []}
        
        # Batch process all student marks
        for item in items:
            student_id = item.get('student_id')
            score = item.get('score')
            comment = item.get('comment', '')
            
            # Skip empty scores
            if not student_id or score == '':
                results['skipped'] += 1
                continue
            
            try:
                score = float(score)
                
                # Validate score is within acceptable range
                if score < 0 or score > max_score:
                    results['errors'].append(
                        f'Score {score} for student {student_id} is out of range (0-{max_score})'
                    )
                    continue
                
                # Check if mark already exists (UPDATE vs INSERT)
                cur.execute('''
                    SELECT id FROM marks 
                    WHERE assessment_id = ? AND student_id = ?
                ''', (assessment_id, student_id))
                
                existing = cur.fetchone()
                
                if existing:
                    # Update existing mark
                    cur.execute('''
                        UPDATE marks 
                        SET score = ?, comment = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE assessment_id = ? AND student_id = ?
                    ''', (score, comment, assessment_id, student_id))
                    results['updated'] += 1
                else:
                    # Insert new mark
                    cur.execute('''
                        INSERT INTO marks (assessment_id, student_id, score, comment)
                        VALUES (?, ?, ?, ?)
                    ''', (assessment_id, student_id, score, comment))
                    results['saved'] += 1
                
            except ValueError:
                results['errors'].append(f'Invalid score format for student {student_id}')
            except Exception as e:
                results['errors'].append(f'Error processing student {student_id}: {str(e)}')
        
        # Commit all changes in single transaction
        conn.commit()
        conn.close()
        
        # Return processing summary
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': f'Failed to save marks: {str(e)}'}), 500
