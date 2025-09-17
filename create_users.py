#!/usr/bin/env python3
"""
Create test users for NFL PickEm 2025
"""

from app import app, db, User

def create_test_users():
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("Users already exist, skipping creation")
            return
            
        # Create test users
        users_data = [
            {'username': 'admin', 'password': 'admin123'},
            {'username': 'manuel', 'password': 'manuel123'},
            {'username': 'daniel', 'password': 'daniel123'},
            {'username': 'raff', 'password': 'raff123'},
            {'username': 'haunschi', 'password': 'haunschi123'}
        ]
        
        for user_data in users_data:
            user = User(username=user_data['username'])
            user.set_password(user_data['password'])
            if user_data['username'] == 'admin':
                user.is_admin = True
            db.session.add(user)
            print(f"Created user: {user_data['username']}")
        
        db.session.commit()
        print("All test users created successfully!")

if __name__ == '__main__':
    create_test_users()

