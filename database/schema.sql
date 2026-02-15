-- SMCT Learning Management System Database Schema
-- Database structure only - no test data

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table - Core user management
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    created_by INTEGER,
    updated_by INTEGER,
    updated_on DATETIME,
    created_on DATETIME
);

-- Classes table - Class/course management
CREATE TABLE classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject TEXT,
    grade_level TEXT,
    teacher_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    type TEXT DEFAULT 'regular',
    status TEXT DEFAULT 'active',
    schedule_days TEXT,
    schedule_time_start TEXT,
    schedule_time_end TEXT,
    section TEXT,
    schedule_pdf_path TEXT,
    meeting_link TEXT,
    max_students INTEGER DEFAULT 30,
    created_by INTEGER,
    updated_by INTEGER,
    updated_on DATETIME,
    created_on DATETIME,
    FOREIGN KEY (teacher_id) REFERENCES users (id)
);

-- Student-Class mapping
CREATE TABLE student_class_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    class_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    assigned_by INTEGER
);

-- Teacher-Class mapping
CREATE TABLE teacher_class_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER,
    class_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    role TEXT DEFAULT 'primary',
    FOREIGN KEY (teacher_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);

-- Assignments table
CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    class_id INTEGER,
    teacher_id INTEGER,
    due_date DATETIME,
    total_marks INTEGER DEFAULT 100,
    assignment_type TEXT DEFAULT 'assignment',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path TEXT,
    original_filename TEXT,
    points INTEGER,
    allow_late_submission INTEGER DEFAULT 0,
    FOREIGN KEY (class_id) REFERENCES classes (id),
    FOREIGN KEY (teacher_id) REFERENCES users (id)
);

-- Assignment submissions
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    submitted_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'submitted',
    grade REAL,
    feedback TEXT,
    graded_by INTEGER,
    graded_on DATETIME,
    FOREIGN KEY (assignment_id) REFERENCES assignments (id),
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (graded_by) REFERENCES users (id)
);

-- Student marks tracking
CREATE TABLE student_marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    assignment_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    marks_obtained REAL,
    total_marks REAL,
    percentage REAL,
    grade TEXT,
    remarks TEXT,
    marked_by INTEGER,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (assignment_id) REFERENCES assignments (id),
    FOREIGN KEY (class_id) REFERENCES classes (id),
    FOREIGN KEY (marked_by) REFERENCES users (id)
);

-- Grade reports
CREATE TABLE grade_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    total_marks REAL,
    obtained_marks REAL,
    percentage REAL,
    grade TEXT,
    rank INTEGER,
    teacher_remarks TEXT,
    generated_by INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id),
    FOREIGN KEY (generated_by) REFERENCES users (id)
);

-- Assessments table
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assessment_date DATE NOT NULL,
    max_score REAL NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);

-- Marks for assessments
CREATE TABLE marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    score REAL NOT NULL,
    comment TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    marked_by INTEGER,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (assessment_id) REFERENCES assessments (id)
);

-- Attendance tracking
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    attendance_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'present',
    marked_by INTEGER NOT NULL,
    marked_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id),
    FOREIGN KEY (marked_by) REFERENCES users (id)
);

-- Announcements
CREATE TABLE announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    class_id INTEGER,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    target_audience TEXT DEFAULT 'class',
    FOREIGN KEY (teacher_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);

-- Student doubts/questions
CREATE TABLE doubts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subject TEXT,
    doubt_text TEXT,
    submitted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_on DATETIME,
    resolved_by INTEGER
);

-- Doubt replies from teachers
CREATE TABLE doubt_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doubt_id INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    reply_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doubt_id) REFERENCES doubts(id),
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

-- Notifications system
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_type TEXT,
    message TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects management
CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    grade_level TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- User roles system
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-role mapping
CREATE TABLE user_role_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (role_id) REFERENCES user_roles (id),
    FOREIGN KEY (assigned_by) REFERENCES users (id)
);

-- Student-subject mapping
CREATE TABLE student_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    assigned_by INTEGER,
    assigned_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id),
    FOREIGN KEY (assigned_by) REFERENCES users (id)
);

-- Teacher-subject mapping
CREATE TABLE teacher_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    assigned_by INTEGER,
    assigned_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users (id),
    FOREIGN KEY (assigned_by) REFERENCES users (id)
);

-- Feedback system
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    feedback_text TEXT NOT NULL,
    rating INTEGER,
    submitted_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users (id)
);

-- Reminders system
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER,
    user_id INTEGER,
    reminder_type TEXT,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    message TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (class_id) REFERENCES classes (id)
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_assignments_class_id ON assignments(class_id);
CREATE INDEX IF NOT EXISTS idx_submissions_assignment_id ON submissions(assignment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_student_id ON submissions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_class_map_student_id ON student_class_map(student_id);
CREATE INDEX IF NOT EXISTS idx_student_class_map_class_id ON student_class_map(class_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_map_teacher_id ON teacher_class_map(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_map_class_id ON teacher_class_map(class_id);
CREATE INDEX IF NOT EXISTS idx_attendance_student_id ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_class_id ON attendance(class_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date);
CREATE INDEX IF NOT EXISTS idx_announcements_teacher_id ON announcements(teacher_id);
CREATE INDEX IF NOT EXISTS idx_announcements_class_id ON announcements(class_id);
CREATE INDEX IF NOT EXISTS idx_student_marks_student_id ON student_marks(student_id);
CREATE INDEX IF NOT EXISTS idx_student_marks_assignment_id ON student_marks(assignment_id);
CREATE INDEX IF NOT EXISTS idx_doubts_student_id ON doubts(student_id);
CREATE INDEX IF NOT EXISTS idx_doubt_replies_doubt_id ON doubt_replies(doubt_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
