from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import re
import pytz

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    materials = db.relationship('EducationalMaterial', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

    @staticmethod
    def is_valid_username(username):
        """Validate username format"""
        return bool(re.match(r'^[a-zA-Z0-9_]{4,20}$', username))

    @staticmethod
    def is_valid_email(email):
        """Validate email format"""
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def is_valid_password(password):
        """Validate password strength"""
        return len(password) >= 6 and any(char.isdigit() for char in password)

    def __repr__(self):
        return f'<User {self.username}>'

class EducationalMaterial(db.Model):
    """Model for educational materials"""
    __tablename__ = 'educational_material'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(50), nullable=True)
    grade_level = db.Column(db.String(20), nullable=True)
    material_type = db.Column(db.String(30), nullable=True)
    image_file = db.Column(db.String(20), nullable=True, default='default.jpg')
    file_path = db.Column(db.String(255), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='material', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<EducationalMaterial {self.title}>'

class Contact(db.Model):
    """Model for contact form submissions"""
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.now(pytz.UTC))

    def __repr__(self):
        return f'<Contact {self.email}: {self.subject}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('educational_material.id'), nullable=False)
