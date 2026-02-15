from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import os

student_bp = Blueprint('student', __name__, url_prefix='/student')

def get_db():
    """Get database connection"""
    return sqlite3.connect('users.db')

@student_bp.route('/site')
def site():
    """Deprecated: Redirect to dashboard"""
    return redirect(url_for('student.dashboard'))

@student_bp.route('/classes')
def classes():
    """Display student's enrolled classes"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_classes.html')

@student_bp.route('/homework')
def homework():
    """Display homework assignments"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_homework.html')

@student_bp.route('/feedback')
def feedback():
    """Submit anonymous feedback"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_feedback.html')

@student_bp.route('/announcements')
def announcements():
    """View announcements"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_announcements.html')

@student_bp.route('/doubts')
def doubts():
    """Ask doubts/questions"""
    if 'role' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_doubts.html')
