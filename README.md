# SMCT Learning Management System (LMS)

## 📚 Project Overview

The SMCT Learning Management System is a comprehensive web-based educational platform built with Flask that facilitates academic management for schools. The system provides role-based access for administrators, teachers, and students, enabling efficient management of classes, assignments, attendance, and academic communications.

## 🏗️ System Architecture

### Technology Stack
- **Backend Framework**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Session-based with SHA-256 password hashing
- **Task Scheduling**: Background thread-based reminder system

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Admin     │ │   Teacher   │ │       Student           ││
│  │  Dashboard  │ │  Dashboard  │ │      Dashboard          ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │    Auth     │ │   Routes    │ │      Middleware         ││
│  │  Blueprint  │ │ (Admin,     │ │   (Session Mgmt)        ││
│  │             │ │ Teacher,    │ │                         ││
│  │             │ │ Student)    │ │                         ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                     Business Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │   Models    │ │ Schedulers  │ │     Utilities           ││
│  │ (DB Models) │ │ (Reminders) │ │  (Password Hashing)     ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│           ┌─────────────────────────────────────┐           │
│           │            SQLite Database           │           │
│           │    (users.db with normalized        │           │
│           │     relational schema)              │           │
│           └─────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Computer-Science-IA-SMCT-LMS/
├── app.py                      # Main application entry point
├── init_database.py           # Database initialization script
├── reminder_scheduler.py      # Background reminder system
├── requirements.txt           # Python dependencies
├── users.db                   # SQLite database file
├── config/
│   └── config.py             # Application configuration
├── criterionC_snippets/      # Code documentation snippets
├── database/
│   └── schema.sql            # Database schema definition
├── models/
│   └── db_models.py          # Database models and utilities
├── routes/
│   ├── admin.py              # Administrator routes
│   ├── auth.py               # Authentication routes
│   ├── main.py               # General application routes
│   ├── student.py            # Student dashboard routes
│   └── teacher.py            # Teacher dashboard routes
├── static/
│   ├── site.css              # Global styles
│   ├── site.js               # Global JavaScript
│   ├── css/                  # Additional stylesheets
│   └── images/               # Static image assets
├── templates/
│   ├── admin/                # Admin interface templates
│   ├── student/              # Student interface templates
│   └── teacher/              # Teacher interface templates
└── uploads/
    ├── assignments/          # Assignment files
    └── submissions/          # Student submissions
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd Computer-Science-IA-SMCT-LMS
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**
   The database will be automatically created when you first run the application.

4. **Run the Application**
   ```bash
   python app.py
   ```

5. **Access the System**
   Open your web browser and navigate to: `http://127.0.0.1:5014`

## 🔧 Configuration

### Database Configuration
- **Database Type**: SQLite3
- **Database File**: `users.db` (created automatically)
- **Schema**: Defined in `database/schema.sql`

### Security Configuration
- **Session Management**: Flask sessions with secure secret key
- **Password Security**: SHA-256 hashing
- **Role-based Access**: Admin, Teacher, Student roles

### Application Settings
- **Debug Mode**: Enabled for development
- **Port**: 5014 (configurable in `app.py`)
- **Auto-reload**: Enabled in debug mode

## 👥 User Roles & Access

### Default Test Accounts

| Role      | Username  | Password    | Access Level |
|-----------|-----------|-------------|--------------|
| Admin     | admin     | admin123    | Full system access |
| Teacher   | teacher1  | teacher123  | Class management |
| Student   | student1  | student123  | Personal dashboard |
| Student   | student2  | student123  | Personal dashboard |
| Student   | student3  | student123  | Personal dashboard |

### Role Permissions

#### 👑 Administrator
- **User Management**: Create, edit, delete users
- **Class Management**: Create classes, assign teachers
- **System Oversight**: View all activities and reports
- **Data Management**: Import/export capabilities
- **Attendance Reports**: System-wide attendance analytics

#### 👨‍🏫 Teacher
- **Class Management**: Manage assigned classes
- **Assignment Creation**: Create and grade assignments
- **Attendance Tracking**: Mark and track student attendance
- **Announcements**: Post class and general announcements
- **Grade Management**: Input and manage student grades
- **Student Progress**: View individual student performance

#### 👨‍🎓 Student
- **Dashboard Access**: Personal academic dashboard
- **Assignment Submission**: Submit assignments online
- **Grade Viewing**: View personal grades and feedback
- **Schedule Access**: View class schedules and timetables
- **Announcements**: Receive class and school announcements
- **Attendance History**: View personal attendance records

## 🔄 Core Functionality

### Authentication System
- **Secure Login**: SHA-256 password hashing
- **Session Management**: Server-side session handling
- **Role-based Routing**: Automatic redirection based on user role
- **Logout Functionality**: Secure session termination

### Class Management
- **Class Creation**: Admin can create classes with subjects and grades
- **Teacher Assignment**: Link teachers to specific classes
- **Student Enrollment**: Enroll students in multiple classes
- **Class Scheduling**: Schedule management for regular classes

### Assignment System
- **Assignment Creation**: Teachers create assignments with due dates
- **File Uploads**: Support for assignment file attachments
- **Submission Tracking**: Monitor student submission status
- **Grading System**: Weighted grade calculations
- **Feedback System**: Teacher feedback on submissions

### Attendance Management
- **Daily Attendance**: Mark student attendance for classes
- **Attendance Reports**: Generate attendance analytics
- **Absence Tracking**: Monitor student absence patterns
- **Attendance Aggregation**: Calculate attendance percentages

### Communication System
- **Announcements**: School-wide and class-specific announcements
- **Priority Levels**: High, normal, and low priority messages
- **Notification System**: Automated reminder system
- **Class Updates**: Real-time updates for class changes

### Automated Reminders
- **Background Scheduler**: Runs in separate thread
- **Class Reminders**: 30-minute advance notifications
- **Assignment Deadlines**: Automatic deadline reminders
- **Customizable Timing**: Configurable reminder intervals

## 🗄️ Database Schema

### Core Tables
- **users**: User accounts and authentication
- **classes**: Class definitions and metadata
- **subjects**: Subject catalog and descriptions
- **assignments**: Assignment details and requirements
- **submissions**: Student assignment submissions
- **attendance**: Daily attendance records
- **announcements**: System and class announcements
- **grades**: Student grade records

### Relationship Mappings
- **student_class_map**: Student-class enrollments
- **teacher_class_map**: Teacher-class assignments
- **submission_files**: Assignment file attachments

### Data Integrity
- **Foreign Key Constraints**: Maintain referential integrity
- **Check Constraints**: Validate data ranges (e.g., scores 0-100)
- **Unique Constraints**: Prevent duplicate entries
- **Cascading Deletes**: Maintain data consistency

## 📊 Sample Data

The system includes comprehensive test data:

### Sample Classes
- **Mathematics 10A**: Advanced Mathematics for Grade 10
- **Physics 10B**: Physics fundamentals and experiments
- **Chemistry 10C**: Basic chemistry principles

### Sample Assignments
- **Algebra Test**: Quadratic equations and polynomials (50 marks)
- **Physics Lab Report**: Motion and forces experiment (25 marks)
- **Chemical Reactions Quiz**: Equation balancing (30 marks)

### Sample Announcements
- Class welcome messages
- School maintenance notices
- Assignment reminders

## 🔧 Development Features

### Debug Mode
- **Auto-reload**: Automatic server restart on code changes
- **Error Handling**: Detailed error messages and stack traces
- **Debug Console**: Flask debug toolbar integration

### Code Organization
- **Blueprint Architecture**: Modular route organization
- **Template Inheritance**: DRY principle in HTML templates
- **Static Asset Management**: Organized CSS/JS/image files
- **Configuration Management**: Centralized config handling

### Error Handling
- **Database Error Recovery**: Graceful handling of DB issues
- **Import Error Handling**: Optional blueprint loading
- **Session Error Management**: Automatic login redirect
- **File Upload Validation**: Secure file handling

## 🚦 Running the Application

### Development Mode
```bash
python app.py
```

### Production Considerations
- Change the secret key in production
- Use a production WSGI server (e.g., Gunicorn)
- Implement HTTPS for security
- Set up proper database backups
- Configure logging for production monitoring

## 📝 Logging & Monitoring

### Console Logging
- Database initialization status
- User authentication attempts
- Reminder system activity
- Error and warning messages

### System Monitoring
- Background thread health monitoring
- Database connection status
- Session management tracking
- File upload monitoring

## 🔒 Security Features

### Data Protection
- **Password Hashing**: SHA-256 encryption
- **Session Security**: Secure session cookies
- **SQL Injection Prevention**: Parameterized queries
- **File Upload Security**: Validated file uploads

### Access Control
- **Role-based Access**: Granular permission system
- **Session Validation**: Automatic login verification
- **Route Protection**: Middleware-based access control
- **CSRF Protection**: Built-in Flask security features

## 🎯 Future Enhancements

### Planned Features
- **Email Notifications**: SMTP integration for reminders
- **Mobile Responsive Design**: Enhanced mobile interface
- **Advanced Reporting**: Detailed analytics dashboard
- **Calendar Integration**: Google Calendar sync
- **File Version Control**: Assignment revision tracking
- **Real-time Chat**: Student-teacher communication
- **API Development**: RESTful API for mobile apps
- **Advanced Security**: Two-factor authentication

### Scalability Considerations
- **Database Migration**: PostgreSQL/MySQL support
- **Caching Layer**: Redis implementation
- **Load Balancing**: Multi-instance deployment
- **Cloud Integration**: AWS/Azure deployment options

## 📞 Support & Maintenance

### Troubleshooting
- Check database file permissions
- Verify Python dependencies
- Review Flask debug messages
- Check port availability (5014)

### Common Issues
- **Database Lock**: Restart application if database is locked
- **Port Conflicts**: Change port in `app.py` if 5014 is occupied
- **Import Errors**: Ensure all dependencies are installed
- **Session Issues**: Clear browser cookies if login problems persist

## 📄 License

This project is developed for educational purposes as part of a Computer Science Internal Assessment (IA). Please ensure compliance with your institution's academic integrity policies when using or modifying this code.

---

**Version**: 1.0  
**Last Updated**: February 15, 2026  
**Developer**: SMCT Development Team  
**Contact**: For support and questions, please refer to the project documentation or contact the development team.
