# snippet7_password_hash.py
# Source: routes/auth.py, lines 8-10

def simple_hash_password(password):
    """Simple password hashing function"""
    return hashlib.sha256(password.encode()).hexdigest()
