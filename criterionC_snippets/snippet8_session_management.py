# snippet8_session_management.py
# Source: routes/auth.py, lines 28-31

# Set session variables after successful authentication
session['user_id'] = user[0]
session['username'] = user[1]
session['role'] = user[3]
