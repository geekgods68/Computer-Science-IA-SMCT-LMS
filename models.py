from datetime import datetime

class User:
    def __init__(self, id, username, password, role, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class UserProfile:
    def __init__(self, id, user_id, email, name, phone=None, address=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.user_id = user_id
        self.email = email
        self.name = name
        self.phone = phone
        self.address = address
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class ClassSession:
    def __init__(self, id, subject, batch, teacher_id, start_time, end_time, zoom_link=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.subject = subject
        self.batch = batch
        self.teacher_id = teacher_id
        self.start_time = start_time
        self.end_time = end_time
        self.zoom_link = zoom_link
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class Attendance:
    def __init__(self, id, class_id, student_id, status, timestamp=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.class_id = class_id
        self.student_id = student_id
        self.status = status
        self.timestamp = timestamp or datetime.now()
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class Resource:
    def __init__(self, id, class_id, uploader_id, type, filename, upload_time=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.class_id = class_id
        self.uploader_id = uploader_id
        self.type = type
        self.filename = filename
        self.upload_time = upload_time or datetime.now()
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class Doubt:
    def __init__(self, id, student_id, class_id, question, anonymous=1, posted_time=None, response=None, responder_id=None, response_time=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.student_id = student_id
        self.class_id = class_id
        self.question = question
        self.anonymous = anonymous
        self.posted_time = posted_time or datetime.now()
        self.response = response
        self.responder_id = responder_id
        self.response_time = response_time
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on

class Assessment:
    def __init__(self, id, student_id, class_id, type, score, max_score, assessment_date=None, created_by=None, created_on=None, updated_by=None, updated_on=None):
        self.id = id
        self.student_id = student_id
        self.class_id = class_id
        self.type = type
        self.score = score
        self.max_score = max_score
        self.assessment_date = assessment_date or datetime.now()
        self.created_by = created_by
        self.created_on = created_on or datetime.now()
        self.updated_by = updated_by
        self.updated_on = updated_on
