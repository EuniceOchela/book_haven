from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # remove old broken admin if it exists
    existing_admin = User.query.filter_by(email="admin@bookhaven.com").first()
    if existing_admin:
        db.session.delete(existing_admin)
        db.session.commit()

    admin = User(
        full_name="Admin User",
        email="admin@bookhaven.com",
        is_admin=True
    )

    admin.set_password("Admin@12345")
    db.session.add(admin)
    db.session.commit()

    print("Admin created successfully")