"""
Automated Reminder System for 30-minute class notifications
This script runs as a background service to send reminders
"""
import sqlite3
import time
from datetime import datetime, timedelta
import json
import threading
import os

class ReminderScheduler:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
    
    def get_upcoming_classes(self):
        """Get classes starting in exactly 30 minutes"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        now = datetime.now()
        target_time = now + timedelta(minutes=30)
        current_day = now.strftime('%A')
        target_time_str = target_time.strftime('%H:%M')
        
        print(f"Looking for classes at {target_time_str} on {current_day}")
        
        # Find classes starting in 30 minutes
        cur.execute('''
            SELECT c.id, c.name, c.schedule_time_start, c.schedule_days,
                   u.username as teacher_name, u.id as teacher_id
            FROM classes c
            JOIN teacher_class_map tcm ON c.id = tcm.class_id
            JOIN users u ON tcm.teacher_id = u.id
            WHERE c.status = 'active' 
            AND c.schedule_time_start = ?
            AND (c.schedule_days LIKE ? OR c.schedule_days LIKE ? OR c.schedule_days = ?)
        ''', (target_time_str, f'%"{current_day}"%', f'%{current_day}%', current_day))
        
        upcoming_classes = cur.fetchall()
        conn.close()
        
        print(f"Found {len(upcoming_classes)} upcoming classes")
        return upcoming_classes
    
    def get_class_students(self, class_id):
        """Get students enrolled in a class"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute('''
            SELECT u.id, u.username, u.email
            FROM users u
            JOIN student_class_map scm ON u.id = scm.student_id
            WHERE scm.class_id = ? AND scm.status = 'active'
        ''', (class_id,))
        
        students = cur.fetchall()
        conn.close()
        return students
    
    def send_notification(self, user_id, user_type, message):
        """Store notification in database for the web app to display"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Create notifications table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_type TEXT,
                message TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Insert notification
        cur.execute('''
            INSERT INTO notifications (user_id, user_type, message)
            VALUES (?, ?, ?)
        ''', (user_id, user_type, message))
        
        conn.commit()
        conn.close()
        print(f"Notification sent to {user_type} {user_id}: {message}")
        return True
    
    def log_reminder(self, class_id, user_id, reminder_type, status, message):
        """Log reminder in database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute('''
            INSERT INTO reminders (class_id, user_id, reminder_type, status, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (class_id, user_id, reminder_type, status, message))
        
        conn.commit()
        conn.close()
    
    def check_already_sent(self, class_id, user_id, reminder_type):
        """Check if reminder was already sent today"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cur.execute('''
            SELECT COUNT(*) FROM reminders 
            WHERE class_id = ? AND user_id = ? AND reminder_type = ? 
            AND DATE(sent_at) = ?
        ''', (class_id, user_id, reminder_type, today))
        
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    
    def check_and_send_reminders(self):
        """Main function to check and send reminders"""
        current_time = datetime.now().strftime('%H:%M')
        print(f"Checking for reminders at {current_time}...")
        
        upcoming_classes = self.get_upcoming_classes()
        reminder_count = 0
        
        for class_info in upcoming_classes:
            class_id, class_name, start_time, schedule_days, teacher_name, teacher_id = class_info
            
            print(f"Processing class: {class_name} at {start_time}")
            
            # Send reminder to teacher (check if not already sent today)
            if not self.check_already_sent(class_id, teacher_id, 'teacher_reminder'):
                teacher_message = f"⏰ Reminder: Your class '{class_name}' starts in 30 minutes at {start_time}. Get ready!"
                self.send_notification(teacher_id, 'teacher', teacher_message)
                self.log_reminder(class_id, teacher_id, 'teacher_reminder', 'sent', teacher_message)
                reminder_count += 1
            
            # Send reminders to students
            students = self.get_class_students(class_id)
            for student_id, student_name, student_email in students:
                if not self.check_already_sent(class_id, student_id, 'student_reminder'):
                    student_message = f"⏰ Reminder: Your class '{class_name}' starts in 30 minutes at {start_time}. Don't be late!"
                    self.send_notification(student_id, 'student', student_message)
                    self.log_reminder(class_id, student_id, 'student_reminder', 'sent', student_message)
                    reminder_count += 1
        
        if reminder_count > 0:
            print(f"✓ Sent {reminder_count} reminders successfully!")
        else:
            print("📋 No new reminders to send at this time.")
        
        return reminder_count
    
    def run_scheduler(self, interval_minutes=2):
        """Run the scheduler continuously"""
        print("↗ Starting automated reminder scheduler...")
        print(f"📅 Checking every {interval_minutes} minutes for classes starting in 30 minutes")
        print(f"🕐 Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        while True:
            try:
                self.check_and_send_reminders()
                print(f"⏸ Sleeping for {interval_minutes} minutes...\n")
                time.sleep(interval_minutes * 60)  # Check every 2 minutes by default
            except KeyboardInterrupt:
                print("\n⏹ Scheduler stopped by user")
                break
            except Exception as e:
                print(f"✗ Scheduler error: {e}")
                print("⏳ Waiting 1 minute before retrying...")
                time.sleep(60)  # Wait 1 minute before retrying

    def run_once(self):
        """Run scheduler once for testing"""
        print("🧪 Running scheduler once for testing...")
        return self.check_and_send_reminders()

def start_scheduler_thread():
    """Start the scheduler in a background thread"""
    def run_background():
        scheduler = ReminderScheduler()
        scheduler.run_scheduler()
    
    thread = threading.Thread(target=run_background, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    scheduler = ReminderScheduler()
    scheduler.run_scheduler()
