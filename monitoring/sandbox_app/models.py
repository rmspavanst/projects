# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    sandboxes = db.Column(db.String(200))

class SandboxInstance(db.Model):
    __tablename__ = 'sandbox_instances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sandbox_type = db.Column(db.String(50), nullable=False)
    instance_name = db.Column(db.String(50), nullable=False)
    instance_id = db.Column(db.String(50), unique=True, nullable=False)
    public_ip = db.Column(db.String(50))
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    ports = db.Column(db.String(255))  # For AWS
    auto_terminate_time = db.Column(db.DateTime)
    launch_time = db.Column(db.DateTime)  # For remaining time calculation
    status = db.Column(db.String(20), default='running')