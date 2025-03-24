# create_admin.py
from app import app, db
from models import User

with app.app_context():
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Create admin user
        admin = User(
            username='admin',
            password='admin123',  # Change this to a secure password
            is_admin=True,
            sandboxes='Vagrant,AWS'  # Grant access to both Vagrant and AWS
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user 'admin' created successfully with password 'admin123'.")
    else:
        print("Admin user 'admin' already exists.")