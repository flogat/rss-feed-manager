#!/bin/bash

# Check if password argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <new_password>"
    echo "Example: $0 mynewpassword123"
    exit 1
fi

NEW_PASSWORD=$1

# Create and execute Python script to reset password
python3 << EOF
from app import app, db
from models import Admin

with app.app_context():
    try:
        admin = Admin.query.first()
        if not admin:
            print("Error: No admin user found in database")
            exit(1)
        
        admin.set_password("$NEW_PASSWORD")
        db.session.commit()
        print("Admin password successfully reset")
    except Exception as e:
        print(f"Error resetting password: {str(e)}")
        exit(1)
EOF

# Make script executable
chmod +x "$0"
