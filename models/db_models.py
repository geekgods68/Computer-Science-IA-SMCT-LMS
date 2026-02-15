# Subject table: represents subjects for each class
class SubjectDB:
    def __init__(self, id, class_id, name, description=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.class_id = class_id
        self.name = name
        self.description = description
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

# Teacher-Subject mapping: assign teachers to subjects
class TeacherSubjectMapDB:
    def __init__(self, id, teacher_id, subject_id, assigned_on=None, assigned_by=None):
        self.id = id
        self.teacher_id = teacher_id
        self.subject_id = subject_id
        self.assigned_on = assigned_on
        self.assigned_by = assigned_by

# Student-Class mapping: allocate students to classes
class StudentClassMapDB:
    def __init__(self, id, student_id, class_id, assigned_on=None, assigned_by=None):
        self.id = id
        self.student_id = student_id
        self.class_id = class_id
        self.assigned_on = assigned_on
        self.assigned_by = assigned_by

# Updated Class model to support multiple subjects and teacher assignments
class ClassDB:
    def __init__(self, id, name, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.name = name
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on
import sqlite3
from datetime import datetime

DATABASE = 'users.db'


class UserDB:
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    def __init__(self, id, username, password_hash, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT id, username, password, created_by, created_on, updated_by, updated_on FROM users WHERE id = ?', (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return UserDB(*row)
        return None

    @staticmethod
    def find_by_username(username):
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        cur.execute('SELECT id, username, password, created_by, created_on, updated_by, updated_on FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            return UserDB(*row)
        return None

class UserRoleDB:
    def __init__(self, id, role_name, description):
        self.id = id
        self.role_name = role_name
        self.description = description

class UserRoleMapDB:
    def __init__(self, id, user_id, role_id, assigned_on, assigned_by=None):
        self.id = id
        self.user_id = user_id
        self.role_id = role_id
        self.assigned_on = assigned_on
        self.assigned_by = assigned_by

class UserProfileDB:
    def __init__(self, id, user_id, email, name, phone=None, address=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.user_id = user_id
        self.email = email
        self.name = name
        self.phone = phone
        self.address = address
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

class ClassSessionDB:
    def __init__(self, id, subject, batch, teacher_id, start_time, end_time, zoom_link=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.subject = subject
        self.batch = batch
        self.teacher_id = teacher_id
        self.start_time = start_time
        self.end_time = end_time
        self.zoom_link = zoom_link
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

class AttendanceDB:
    def __init__(self, id, class_id, student_id, status, timestamp=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.class_id = class_id
        self.student_id = student_id
        self.status = status
        self.timestamp = timestamp
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

class ResourceDB:
    def __init__(self, id, class_id, uploader_id, type, filename, upload_time=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.class_id = class_id
        self.uploader_id = uploader_id
        self.type = type
        self.filename = filename
        self.upload_time = upload_time
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

class DoubtDB:
    def __init__(self, id, student_id, class_id, question, anonymous=1, posted_time=None, response=None, responder_id=None, response_time=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.student_id = student_id
        self.class_id = class_id
        self.question = question
        self.anonymous = anonymous
        self.posted_time = posted_time
        self.response = response
        self.responder_id = responder_id
        self.response_time = response_time
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on

class AssessmentDB:
    def __init__(self, id, student_id, class_id, type, score, max_score, assessment_date=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.student_id = student_id
        self.class_id = class_id
        self.type = type
        self.score = score
        self.max_score = max_score
        self.assessment_date = assessment_date
        self.created_by = created_by
        self.created_on = created_on
        self.updated_by = updated_by
        self.updated_on = updated_on
