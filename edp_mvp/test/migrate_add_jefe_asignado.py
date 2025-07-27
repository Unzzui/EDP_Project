"""
Migration script to add jefe_asignado column to usuarios table.
This script adds the new column to support the enhanced user role system.
"""

import sqlite3
import os
import sys
from datetime import datetime

def migrate_database():
    """Add jefe_asignado column to usuarios table."""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'edp_database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("Please ensure the database exists before running this migration.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'jefe_asignado' in columns:
            print("✅ Column 'jefe_asignado' already exists in usuarios table.")
            conn.close()
            return True
        
        # Add the new column
        print("📝 Adding 'jefe_asignado' column to usuarios table...")
        cursor.execute("""
            ALTER TABLE usuarios 
            ADD COLUMN jefe_asignado TEXT
        """)
        
        # Create index for better performance
        print("📝 Creating index on jefe_asignado column...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_usuarios_jefe_asignado 
            ON usuarios(jefe_asignado)
        """)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Migration completed successfully!")
        print("   - Added 'jefe_asignado' column to usuarios table")
        print("   - Created index for better performance")
        print(f"   - Migration completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def rollback_migration():
    """Remove jefe_asignado column from usuarios table (if needed)."""
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'edp_system.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
        print("⚠️  Warning: This will recreate the usuarios table without jefe_asignado column")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Migration rollback cancelled.")
            conn.close()
            return False
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(usuarios)")
        columns_info = cursor.fetchall()
        
        # Filter out jefe_asignado column
        columns_without_jefe = [col for col in columns_info if col[1] != 'jefe_asignado']
        
        # Create new table structure
        column_definitions = []
        for col in columns_without_jefe:
            col_def = f"{col[1]} {col[2]}"
            if col[3]:  # NOT NULL
                col_def += " NOT NULL"
            if col[4] is not None:  # DEFAULT
                col_def += f" DEFAULT {col[4]}"
            if col[5]:  # PRIMARY KEY
                col_def += " PRIMARY KEY"
            column_definitions.append(col_def)
        
        # Create temporary table
        create_temp_sql = f"""
            CREATE TABLE usuarios_temp (
                {', '.join(column_definitions)}
            )
        """
        cursor.execute(create_temp_sql)
        
        # Copy data (excluding jefe_asignado column)
        column_names = [col[1] for col in columns_without_jefe]
        copy_sql = f"""
            INSERT INTO usuarios_temp ({', '.join(column_names)})
            SELECT {', '.join(column_names)} FROM usuarios
        """
        cursor.execute(copy_sql)
        
        # Drop old table and rename temp table
        cursor.execute("DROP TABLE usuarios")
        cursor.execute("ALTER TABLE usuarios_temp RENAME TO usuarios")
        
        # Recreate indexes (if any)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(rol)")
        
        conn.commit()
        conn.close()
        
        print("✅ Rollback completed successfully!")
        print("   - Removed 'jefe_asignado' column from usuarios table")
        print("   - Recreated table with original structure")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error during rollback: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during rollback: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔄 EDP System Database Migration")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        print("🔄 Running rollback migration...")
        success = rollback_migration()
    else:
        print("🔄 Running forward migration...")
        success = migrate_database()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1) 