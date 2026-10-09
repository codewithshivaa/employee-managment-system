from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    designation = db.Column(db.String(50), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    joining_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Active")
    leave_balance = db.relationship("LeaveBalance", backref="employee", lazy=True, cascade="all, delete-orphan")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False,
        default="employee"
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=True
    )   

class Attendance(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    punch_in = db.Column(
        db.DateTime,
        nullable=True
    )

    punch_out = db.Column(
        db.DateTime,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Present"
    )

class ProfileUpdateRequest(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=False
    )

    field = db.Column(
        db.String(50),
        nullable=False
    )

    old_value = db.Column(
        db.String(200),
        nullable=False
    )

    new_value = db.Column(
        db.String(200),
        nullable=False
    )

    reason = db.Column(
        db.String(500),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

class Notification(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=False
    )

    message = db.Column(
        db.String(255),
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Leave(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey('employee.id'),
        nullable=False
    )

    leave_type = db.Column(db.String(50), nullable=False)

    from_date = db.Column(db.Date, nullable=False)

    to_date = db.Column(db.Date, nullable=False)

    reason = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        default='Pending',
        nullable=False
    )

    applied_on = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    employee = db.relationship(
        'Employee',
        backref='leave_requests'
    )
class LeaveBalance(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    employee_id = db.Column(
        db.Integer,
        db.ForeignKey("employee.id"),
        nullable=False
    )

    leave_type = db.Column(
        db.String(50),
        nullable=False
    )

    total_days = db.Column(
        db.Integer,
        nullable=False
    )

    used_days = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    
    def __repr__(self):
        return f'<Employee {self.name}>'