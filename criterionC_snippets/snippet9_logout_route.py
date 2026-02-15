# snippet9_logout_route.py
# Source: routes/auth.py, lines 52-56

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('auth.login'))
