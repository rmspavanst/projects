from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from cryptography.fernet import Fernet

db = SQLAlchemy()

key = Fernet.generate_key()
cipher = Fernet(key)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    privileges = db.Column(db.String(120), default='read')

class Server(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(80))
    ip_address = db.Column(db.String(15), unique=True, nullable=False)
    username = db.Column(db.LargeBinary, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    environment = db.Column(db.String(20), nullable=False)
    operating_system = db.Column(db.String(120))
    kernel = db.Column(db.String(80))
    total_disk_gb = db.Column(db.Integer)
    free_disk_gb = db.Column(db.Integer)
    total_ram_gb = db.Column(db.Integer)
    cpu_count = db.Column(db.Integer)
    boot_time = db.Column(db.String(80))
    status = db.Column(db.Boolean)

    def encrypt_field(self, data):
        return cipher.encrypt(data.encode())

    def decrypt_field(self, data):
        return cipher.decrypt(data).decode()

    def set_username(self, username):
        self.username = self.encrypt_field(username)

    def get_username(self):
        return self.decrypt_field(self.username)

    def set_password(self, password):
        self.password = self.encrypt_field(password)

    def get_password(self):
        return self.decrypt_field(self.password)