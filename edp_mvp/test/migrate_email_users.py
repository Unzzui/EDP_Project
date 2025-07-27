"""
Migration script for email users tables.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.email_user import EmailUser, EmailUserProject, EmailUserClient, EmailUserPreference

def create_email_users_tables():
    """Create email users tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Crear tablas
            db.create_all()
            print("✅ Tablas de usuarios de email creadas exitosamente")
            
            # Crear usuarios de ejemplo
            create_sample_users()
            
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            return False
    
    return True

def create_sample_users():
    """Create sample email users for testing."""
    try:
        # Verificar si ya existen usuarios
        if EmailUser.query.count() > 0:
            print("ℹ️  Usuarios de email ya existen, saltando creación de ejemplos")
            return
        
        # 1. Usuario Ejecutivo
        executive = EmailUser(
            email="diegobravobe@gmail.com",
            name="Diego Bravo",
            role="executive",
            # Configuración de correo (usar configuración actual del sistema)
            mail_server="smtp.gmail.com",
            mail_port=587,
            mail_use_tls=True,
            mail_username="diegobravobe@gmail.com",  # TODO: Configurar con credenciales reales
            mail_password="",  # TODO: Configurar contraseña de aplicación
            mail_default_sender="Pagora EDP <diegobravobe@gmail.com>",
            enable_critical_alerts=True,
            enable_payment_reminders=True,
            enable_weekly_summary=True,
            enable_system_alerts=True
        )
        db.session.add(executive)
        
        # 2. Usuario Controller
        controller = EmailUser(
            email="controller@empresa.com",
            name="Controller General",
            role="controller"
        )
        db.session.add(controller)
        
        # 3. Usuario Finance
        finance = EmailUser(
            email="finance@empresa.com",
            name="Departamento Finanzas",
            role="finance"
        )
        db.session.add(finance)
        
        # 4. Jefe de Proyecto - Pedro Rojas
        pedro = EmailUser(
            email="pedro.rojas@empresa.com",
            name="Pedro Rojas",
            role="project_manager"
        )
        db.session.add(pedro)
        
        # 5. Jefe de Proyecto - Carolina López
        carolina = EmailUser(
            email="carolina.lopez@empresa.com",
            name="Carolina López",
            role="project_manager"
        )
        db.session.add(carolina)
        
        # 6. Cliente Arauco
        cliente_arauco = EmailUser(
            email="cliente.arauco@arauco.com",
            name="Cliente Arauco",
            role="client"
        )
        db.session.add(cliente_arauco)
        
        # 7. Cliente Enel
        cliente_enel = EmailUser(
            email="cliente.enel@enel.com",
            name="Cliente Enel",
            role="client"
        )
        db.session.add(cliente_enel)
        
        # Commit para obtener IDs
        db.session.commit()
        
        # Asignar proyectos a Pedro Rojas
        pedro_projects = [
            EmailUserProject(
                user_id=pedro.id,
                project_name="OT2467",
                project_manager="Pedro Rojas"
            ),
            EmailUserProject(
                user_id=pedro.id,
                project_name="OT9142",
                project_manager="Pedro Rojas"
            )
        ]
        for project in pedro_projects:
            db.session.add(project)
        
        # Asignar proyectos a Carolina López
        carolina_projects = [
            EmailUserProject(
                user_id=carolina.id,
                project_name="OT4948",
                project_manager="Carolina López"
            )
        ]
        for project in carolina_projects:
            db.session.add(project)
        
        # Asignar proyectos a Diego Bravo (como ejecutivo tiene acceso a todo)
        diego_projects = [
            EmailUserProject(
                user_id=executive.id,
                project_name="OT2467",
                project_manager="Pedro Rojas"
            ),
            EmailUserProject(
                user_id=executive.id,
                project_name="OT4948",
                project_manager="Carolina López"
            ),
            EmailUserProject(
                user_id=executive.id,
                project_name="OT4666",
                project_manager="Diego Bravo"
            ),
            EmailUserProject(
                user_id=executive.id,
                project_name="OT9142",
                project_manager="Diego Bravo"
            ),
            EmailUserProject(
                user_id=executive.id,
                project_name="OT7678",
                project_manager="Diego Bravo"
            )
        ]
        for project in diego_projects:
            db.session.add(project)
        
        # Asignar clientes
        arauco_client = EmailUserClient(
            user_id=cliente_arauco.id,
            client_name="Arauco"
        )
        db.session.add(arauco_client)
        
        enel_client = EmailUserClient(
            user_id=cliente_enel.id,
            client_name="Enel"
        )
        db.session.add(enel_client)
        
        # Crear preferencias de email por defecto
        for user in [executive, controller, finance, pedro, carolina, cliente_arauco, cliente_enel]:
            preferences = EmailUserPreference(
                user_id=user.id,
                receive_weekly_summary=True,
                receive_critical_alerts=True,
                receive_payment_reminders=True,
                receive_system_alerts=True,
                receive_performance_reports=True
            )
            db.session.add(preferences)
        
        db.session.commit()
        print("✅ Usuarios de ejemplo creados exitosamente")
        
        # Mostrar resumen
        print("\n📊 Resumen de usuarios creados:")
        for user in EmailUser.query.all():
            print(f"  - {user.name} ({user.email}) - Rol: {user.role}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creando usuarios de ejemplo: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Iniciando migración de usuarios de email...")
    success = create_email_users_tables()
    
    if success:
        print("✅ Migración completada exitosamente")
    else:
        print("❌ Migración falló")
        sys.exit(1) 