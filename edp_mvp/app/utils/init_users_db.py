"""
Script para inicializar la base de datos SQLite de usuarios
"""
from flask import Flask
from ..models.user import User
from ..extensions import db
from ..config import get_config

def create_tables(app):
    """Create database tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully")

def initialize_admin_user(app):
    """Create default admin user."""
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("✅ Admin user already exists")
            return True
        
        # Create default admin user
        try:
            admin_user = User(
                nombre_completo="Administrador del Sistema",
                username="admin",
                password="admin123",
                rol="admin"
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("✅ Default admin user created successfully")
            print("📋 Default admin user credentials:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  Please change this password after first login!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin user: {str(e)}")
            return False

def check_database_exists(app):
    """Check if database exists and has proper structure."""
    with app.app_context():
        try:
            # Try to query the users table
            user_count = User.query.count()
            print(f"✅ Database exists with {user_count} users")
            return True
        except Exception as e:
            print(f"❌ Database doesn't exist or has issues: {str(e)}")
            return False

def init_users_db():
    """Initialize SQLite database - can be called from command line or app startup."""
    # Create minimal Flask app for database operations
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Initialize database
    db.init_app(app)
    
    print("🔧 Checking SQLite database...")
    if not check_database_exists(app):
        print("🔧 Creating database tables...")
        create_tables(app)
    
    print("🔧 Checking admin user...")
    success = initialize_admin_user(app)
    
    return success

if __name__ == "__main__":
    init_users_db() 