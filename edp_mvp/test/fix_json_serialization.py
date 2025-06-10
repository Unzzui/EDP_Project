#!/usr/bin/env python3
"""
Script to fix JSON serialization issues in manager_service.py
"""

import re

def fix_manager_service():
    file_path = '/home/unzzui/Documents/coding/EDP_Project/edp_mvp/app/services/manager_service.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all json.dumps calls to use sanitization
    replacements = [
        # Pattern 1: json.dumps(immediate_data.data)
        (
            r'json\.dumps\(immediate_data\.data\)',
            'json.dumps(self._sanitize_for_json(immediate_data.data))'
        ),
        # Pattern 2: json.dumps(components['executive_kpis'])
        (
            r'json\.dumps\(components\[\'executive_kpis\'\]\)',
            'json.dumps(self._sanitize_for_json(components[\'executive_kpis\']))'
        ),
        # Pattern 3: json.dumps(result_data)
        (
            r'json\.dumps\(result_data\)',
            'json.dumps(self._sanitize_for_json(result_data))'
        ),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed JSON serialization issues in manager_service.py")

if __name__ == "__main__":
    fix_manager_service()
