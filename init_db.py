#!/usr/bin/env python3
"""
Script to initialize the database and create default users
Run this once on Render after deployment
"""
from app import app, db, User
import os

def init_database():
    """Initialize database and create default users"""
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created")

        # Create admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@cococrm.com',
                first_name='Admin',
                last_name='CocoCRM'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Created admin user (admin/admin123)")
        else:
            print("ℹ️  Admin user already exists")

        # Create Coco user (openclaw)
        coco = User.query.filter_by(username='coco').first()
        if not coco:
            coco = User(
                username='coco',
                email='coco@openclaw.ai',
                first_name='Coco',
                last_name='OpenClaw'
            )
            coco.set_password('coco123')
            db.session.add(coco)
            print("✅ Created coco user (coco/coco123)")
        else:
            print("ℹ️  Coco user already exists")

        # Commit changes
        db.session.commit()

        # Show summary
        total_users = User.query.count()
        print(f"\n{'='*50}")
        print("📊 DATABASE SUMMARY")
        print(f"{'='*50}")
        print(f"Total users: {total_users}")
        print("\nUsers:")
        for user in User.query.all():
            print(f"  - {user.username} ({user.email or 'no email'})")
        print(f"{'='*50}")
        print("\n✅ Database initialization complete!")
        print("\n🔑 LOGIN CREDENTIALS:")
        print("   Admin: admin / admin123")
        print("   Coco:  coco / coco123")
        print(f"{'='*50}\n")

if __name__ == '__main__':
    init_database()
