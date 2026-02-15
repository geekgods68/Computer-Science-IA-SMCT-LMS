-- snippet12_score_check.sql
-- Source: database/schema.sql, lines 226-230

-- Assessments table with score validation constraints
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    subject_name TEXT NOT NULL,
    teacher_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    assessment_date DATE NOT NULL,
    max_score REAL NOT NULL CHECK(max_score > 0),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0 AND weight <= 1),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(class_id, subject_name, title, assessment_date)
);

-- Student marks with score validation
CREATE TABLE marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    score REAL NOT NULL CHECK(score >= 0),
    comment TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(assessment_id, student_id)
);
