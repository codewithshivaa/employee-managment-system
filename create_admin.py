from app import app
from models import db, User
from werkzeug.security import generate_password_hash


with app.app_context():

    existing_user = User.query.filter_by(
        username="admin"
    ).first()

    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()

    password_hash = generate_password_hash("admin123")

    admin = User(
        username="admin",
        password=password_hash
    )

    db.session.add(admin)
    db.session.commit()

    print("Admin user created with hashed password!")