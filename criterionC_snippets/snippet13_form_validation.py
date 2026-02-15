# snippet13_form_validation.py
# Source: routes/admin.py, lines 813-820 (doubt response validation)

# Form validation example from admin doubt response route
doubt_id = request.form.get('doubt_id')
response = request.form.get('response', '').strip()

if not doubt_id or not response:
    flash('Doubt ID and response are required!', 'error')
    return redirect(url_for('admin.view_doubts'))

# Additional validation example from teacher marks
class_id = request.form.get('class_id')
subject_name = request.form.get('subject_name')
title = request.form.get('title', '').strip()
max_score = request.form.get('max_score')

if not all([class_id, subject_name, title, max_score]):
    flash('All required fields must be filled', 'error')
    return redirect(url_for('teacher.marks'))

try:
    max_score = float(max_score)
    if max_score <= 0:
        raise ValueError("Max score must be positive")
except ValueError as e:
    flash(f'Invalid input: {e}', 'error')
    return redirect(url_for('teacher.marks'))
