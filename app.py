from flask import Flask, redirect, url_for, session
import os
import sqlite3
import hashlib

def init_database():
    """Initialize database using schema.sql and populate with test data"""
    if not os.path.exists('users.db'):
        print("� No database found, creating from schema.sql...")
        # Create database from schema
        try:
            from init_database import create_database
            create_database()
        except Exception as e:
            print(f"✗ Failed to create database from schema: {e}")
            return False
    
    # Always check and populate test data
    populate_test_data()
    return True

def populate_test_data():
    """Populate database with test data if it doesn't exist"""
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    
    try:
        # Check if admin user exists
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            print("⚙ Adding test data...")
            
            # Hash function for passwords
            def hash_password(password):
                return hashlib.sha256(password.encode()).hexdigest()
            
            # Add test users
            test_users = [
                ('admin', hash_password('admin123'), 'admin', 'System Administrator', 'admin@smct.edu'),
                ('student1', hash_password('student123'), 'student', 'John Student', 'john@student.edu'),
                ('student2', hash_password('student123'), 'student', 'Jane Smith', 'jane@student.edu'),
                ('student3', hash_password('student123'), 'student', 'Mike Johnson', 'mike@student.edu'),
                ('teacher1', hash_password('teacher123'), 'teacher', 'Dr. Smith', 'smith@teacher.edu')
            ]
            
            for username, password, role, name, email in test_users:
                cur.execute('''
                    INSERT OR IGNORE INTO users (username, password, role, name, email, created_on) 
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (username, password, role, name, email))
            
            # Add basic subjects
            subjects = [
                ('Mathematics', 'Mathematics curriculum', '9-12'),
                ('Science', 'Science curriculum', '9-12'),
                ('English', 'English Language Arts', '9-12'),
                ('History', 'World and Local History', '9-12'),
                ('Computer Science', 'Programming and IT', '9-12')
            ]
            
            for name, description, grade_level in subjects:
                cur.execute('''
                    INSERT OR IGNORE INTO subjects (name, description, grade_level, created_by, created_at)
                    VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ''', (name, description, grade_level))
            
            # Add sample classes (teacher_id = 5 for teacher1)
            sample_classes = [
                ('Mathematics 10A', 'Mathematics', '10', 5, 'Advanced Mathematics for Grade 10'),
                ('Physics 10B', 'Physics', '10', 5, 'Physics fundamentals and experiments'),
                ('Chemistry 10C', 'Chemistry', '10', 5, 'Basic chemistry principles')
            ]
            
            for class_name, subject, grade, teacher_id, description in sample_classes:
                cur.execute('''
                    INSERT OR IGNORE INTO classes (name, subject, grade_level, teacher_id, description, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (class_name, subject, grade, teacher_id, description))
            
            # Map teacher to classes
            teacher_class_mappings = [(5, 1), (5, 2), (5, 3)]
            for teacher_id, class_id in teacher_class_mappings:
                cur.execute('''
                    INSERT OR IGNORE INTO teacher_class_map (teacher_id, class_id, created_at) 
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (teacher_id, class_id))
            
            # Map students to classes
            student_class_mappings = [(2, 1), (2, 2), (3, 1), (3, 3), (4, 2), (4, 3)]
            for student_id, class_id in student_class_mappings:
                cur.execute('''
                    INSERT OR IGNORE INTO student_class_map (student_id, class_id, status, created_at) 
                    VALUES (?, ?, 'active', CURRENT_TIMESTAMP)
                ''', (student_id, class_id))
            
            # Add sample assignments
            sample_assignments = [
                ('Algebra Test', 'Test on quadratic equations and polynomials', 1, 5, '2026-02-15 10:00:00', 50, 'test'),
                ('Physics Lab Report', 'Motion and forces experiment report', 2, 5, '2026-02-20 23:59:59', 25, 'assignment'),
                ('Chemical Reactions Quiz', 'Quiz on chemical equations balancing', 3, 5, '2026-02-18 14:00:00', 30, 'quiz')
            ]
            
            for title, desc, class_id, teacher_id, due_date, marks, assignment_type in sample_assignments:
                cur.execute('''
                    INSERT OR IGNORE INTO assignments (title, description, class_id, teacher_id, due_date, total_marks, assignment_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (title, desc, class_id, teacher_id, due_date, marks, assignment_type))
            
            # Add sample announcements
            sample_announcements = [
                (5, 1, 'Welcome to Mathematics 10A', 'Welcome to our advanced mathematics class. Please bring your textbooks.', 'normal'),
                (5, None, 'School Notice', 'Reminder: School will be closed next Friday for maintenance.', 'high')
            ]
            
            for teacher_id, class_id, title, content, priority in sample_announcements:
                cur.execute('''
                    INSERT OR IGNORE INTO announcements (teacher_id, class_id, title, content, priority, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (teacher_id, class_id, title, content, priority))
            
            print("✓ Test data added successfully!")
        else:
            print("✓ Test data already exists")
    
    except Exception as e:
        print(f"⚠ Error populating test data: {e}")
    
    finally:
        conn.commit()
        conn.close()

def create_app():
    app = Flask(__name__)
    
    # Simple configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['DATABASE'] = 'users.db'
    
    # Initialize database
    print("⚙ Initializing database...")
    try:
        init_database()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Database error: {e}")
    
    # Start reminder scheduler in background (optional)
    try:
        from reminder_scheduler import start_scheduler_thread
        scheduler_thread = start_scheduler_thread()
        print("↗ Reminder scheduler started in background thread")
    except Exception as e:
        print(f"⚠ Reminder scheduler not started: {e}")
    
    @app.route('/')
    def home():
        # Always clear session and redirect to login page
        session.clear()
        return redirect(url_for('auth.login'))
    
    @app.route('/dashboard')
    def dashboard():
        # Redirect to appropriate dashboard after login
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Redirect based on role
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('role') == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif session.get('role') == 'student':
            return redirect(url_for('student.dashboard'))
        else:
            return redirect(url_for('auth.login'))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp)
    
    # Optional: Register other blueprints if they exist
    try:
        from routes.teacher import teacher_bp
        app.register_blueprint(teacher_bp)
    except ImportError:
        pass
    
    try:
        from routes.student import student_bp
        app.register_blueprint(student_bp)
    except ImportError:
        pass
    
    try:
        from routes.main import main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        pass

    return app

if __name__ == '__main__':
    print("🏫 School Management System")
    print("=" * 50)
    print("👥 Test Accounts:")
    print("   🔑 Admin:    admin / admin123")
    print("   👤 Student:  student1 / student123")  
    print("   � Teacher:  teacher1 / teacher123")
    print(f"\n🌐 Starting server on http://127.0.0.1:5014")
    print("⚠ Press Ctrl+C to stop\n")
    
    app = create_app()
    app.run(debug=True, port=5014)
