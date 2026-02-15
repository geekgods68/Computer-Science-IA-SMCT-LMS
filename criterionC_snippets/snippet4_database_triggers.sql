# snippet4_database_triggers.sql
-- Database triggers for automatic data integrity and business logic
-- Source: database/schema.sql, lines 385-420

-- ============================================================================
-- TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- Trigger to update user updated_on timestamp
CREATE TRIGGER update_users_timestamp 
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_on = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to update class updated_on timestamp
CREATE TRIGGER update_classes_timestamp 
    AFTER UPDATE ON classes
    FOR EACH ROW
BEGIN
    UPDATE classes SET updated_on = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger to automatically resolve doubts when response is added
-- This demonstrates business logic automation at the database level
CREATE TRIGGER auto_resolve_doubts 
    AFTER UPDATE ON doubts
    FOR EACH ROW
    WHEN NEW.response IS NOT NULL AND OLD.response IS NULL
BEGIN
    UPDATE doubts 
    SET status = 'answered', 
        resolved_on = CURRENT_TIMESTAMP,
        response_time = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Additional trigger for marks validation (if implemented)
-- This would ensure scores don't exceed maximum allowed values
CREATE TRIGGER validate_marks_score
    BEFORE INSERT ON marks
    FOR EACH ROW
BEGIN
    -- Get the maximum score for this assessment
    SELECT CASE 
        WHEN NEW.score > (SELECT max_score FROM assessments WHERE id = NEW.assessment_id)
        THEN RAISE(ABORT, 'Score cannot exceed maximum score for assessment')
        WHEN NEW.score < 0
        THEN RAISE(ABORT, 'Score cannot be negative')
    END;
END;

-- Trigger to update marks timestamp
CREATE TRIGGER update_marks_timestamp
    AFTER UPDATE ON marks
    FOR EACH ROW
BEGIN
    UPDATE marks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
