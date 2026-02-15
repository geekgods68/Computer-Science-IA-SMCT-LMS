-- snippet10_foreign_keys.sql
-- Source: database/schema.sql, lines 93-113

-- Student-to-class assignments with foreign key constraints
CREATE TABLE student_class_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    assigned_by INTEGER,
    assigned_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',  -- active, inactive, dropped
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    UNIQUE(student_id, class_id)
);

-- Teacher-to-class assignments with foreign key constraints
CREATE TABLE teacher_class_map (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    assigned_by INTEGER,
    assigned_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    role TEXT DEFAULT 'primary',  -- primary, assistant, substitute
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id),
    UNIQUE(teacher_id, class_id)
);
