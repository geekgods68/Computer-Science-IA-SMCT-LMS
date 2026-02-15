# snippet15_flash_messages.py
# Source: routes/admin.py and routes/teacher.py - flash message examples

# Success message example
flash('Attendance marked for 25 students', 'success')

# Error message example  
flash('Error saving attendance: Database connection failed', 'error')

# Validation error message
flash('All required fields must be filled', 'error')

# Authentication error message
flash('Invalid username or password!', 'error')

# Permission error message
flash('Access denied to this class', 'error')

# Success message with dynamic content
flash(f'Assessment "{title}" created successfully', 'success')

# Database error message
flash(f'Database error: {str(e)}', 'error')

# Logout success message
flash('You have been logged out successfully!', 'success')
