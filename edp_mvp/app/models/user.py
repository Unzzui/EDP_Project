"""
User model for SQLite database.
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from ..extensions import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(20), nullable=False, index=True)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    def __init__(self, nombre_completo, username, password, rol):
        self.nombre_completo = nombre_completo
        self.username = username
        self.set_password(password)
        self.rol = rol
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_active(self):
        """Check if user is active."""
        return self.activo
    
    @property
    def is_admin(self):
        """Check if user is admin."""
        return self.rol == 'admin'
    
    def update_last_access(self):
        """Update last access time."""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'username': self.username,
            'rol': self.rol,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None
        }
    
    @staticmethod
    def create_user(nombre_completo, username, password, rol):
        """Create a new user."""
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return None, "El nombre de usuario ya existe"
        
        # Validate role
        valid_roles = ['admin', 'controller', 'manager', 'jefe_proyecto']
        if rol not in valid_roles:
            return None, "Rol inválido"
        
        try:
            user = User(nombre_completo, username, password, rol)
            db.session.add(user)
            db.session.commit()
            return user, "Usuario creado exitosamente"
        except Exception as e:
            db.session.rollback()
            return None, f"Error al crear usuario: {str(e)}"
    
    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        return User.query.filter_by(username=username, activo=True).first()
    
    @staticmethod
    def get_all_active():
        """Get all active users."""
        return User.query.filter_by(activo=True).all()
    
    @staticmethod
    def get_stats():
        """Get user statistics by role."""
        stats = {}
        for rol in ['admin', 'controller', 'manager', 'jefe_proyecto']:
            stats[rol] = User.query.filter_by(rol=rol, activo=True).count()
        stats['total'] = User.query.filter_by(activo=True).count()
        return stats
    
    def __repr__(self):
        return f'<User {self.username} ({self.rol})>' 