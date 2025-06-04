#!/usr/bin/env python3
"""
Quick test to identify the exact import issue
"""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_imports():
    print("🔍 Testing import chain...")
    
    try:
        print("1. Testing date_utils...")
        from edp_mvp.app.utils.date_utils import parse_date_safe
        print("   ✅ parse_date_safe imported successfully")
    except Exception as e:
        print(f"   ❌ date_utils error: {e}")
        return False
    
    try:
        print("2. Testing format_utils...")
        from edp_mvp.app.utils.format_utils import clean_numeric_value
        print("   ✅ clean_numeric_value imported successfully")
    except Exception as e:
        print(f"   ❌ format_utils error: {e}")
        return False
    
    try:
        print("3. Testing repositories...")
        from edp_mvp.app.repositories.edp_repository import EDPRepository
        print("   ✅ EDPRepository imported successfully")
    except Exception as e:
        print(f"   ❌ repositories error: {e}")
        return False
    
    try:
        print("4. Testing services...")
        from edp_mvp.app.services.kanban_service import KanbanService
        print("   ✅ KanbanService imported successfully")
    except Exception as e:
        print(f"   ❌ services error: {e}")
        return False
    
    try:
        print("5. Testing controllers...")
        from edp_mvp.app.controllers.controller_controller import controller_controller_bp
        print("   ✅ controller_controller_bp imported successfully")
    except Exception as e:
        print(f"   ❌ controllers error: {e}")
        return False
    
    try:
        print("6. Testing app creation...")
        from edp_mvp.app import create_app
        app = create_app()
        print("   ✅ Flask app created successfully")
    except Exception as e:
        print(f"   ❌ app creation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting import test...")
    success = test_imports()
    
    if success:
        print("\n🎉 All imports successful! The app should run correctly.")
        print("💡 You can now run: python3 ./run.py")
    else:
        print("\n❌ Import test failed. Check the errors above.")
