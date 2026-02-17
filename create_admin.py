#!/usr/bin/env python3
"""
Script para crear usuario administrador en CocoCRM
"""
from app import app, db, User

def create_admin():
    with app.app_context():
        # Verificar si ya existe
        admin = User.query.filter_by(username='admin').first()

        if admin:
            print("⚠️  Usuario 'admin' ya existe!")
            print(f"   Username: admin")
            print(f"   Email: {admin.email}")
            print(f"   Telegram ID: {admin.telegram_id}")

            # Actualizar password
            admin.set_password('admin123')
            db.session.commit()
            print("\n✅ Password actualizada a: admin123")
        else:
            # Crear nuevo admin
            admin = User(
                username='admin',
                email='admin@cococrm.com',
                first_name='Admin',
                last_name='CocoCRM'
            )
            admin.set_password('admin123')

            db.session.add(admin)
            db.session.commit()

            print("✅ Usuario admin creado exitosamente!")

        print("\n" + "="*50)
        print("🔑 CREDENCIALES DE ADMIN")
        print("="*50)
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Email: admin@cococrm.com")
        print("="*50)

        # Mostrar todos los usuarios
        print(f"\n📊 Total de usuarios en DB: {User.query.count()}")
        print("\nUsuarios registrados:")
        for user in User.query.all():
            print(f"  - {user.username} (ID: {user.id}, Telegram: {user.telegram_id or 'N/A'})")

if __name__ == '__main__':
    create_admin()
