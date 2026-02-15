-- snippet11_attendance_constraint.sql
-- Source: database/schema.sql, lines 175-178

-- Attendance table with role-based constraint
CREATE TABLE attendance (
    -- ... other columns ...
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    attendance_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'present',
    marked_by INTEGER NOT NULL,
    -- ... other columns ...
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES users(id),
    -- Ensure student_id references a user with student role
    CONSTRAINT check_student_role CHECK (
        student_id IN (SELECT id FROM users WHERE role = 'student')
    ),
    -- Ensure only one attendance record per student per class per date
    UNIQUE(student_id, class_id, attendance_date)
);
