#!/usr/bin/env python3
"""
Generador de datos demo para cuando Google Sheets no está disponible
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_demo_edp_data():
    """Generar datos demo para EDP cuando Google Sheets no está disponible"""
    
    # Datos de ejemplo
    states = ['Pendiente', 'En Proceso', 'Completado', 'Cancelado']
    departments = ['Ventas', 'Marketing', 'IT', 'RRHH', 'Finanzas']
    clients = ['Cliente A', 'Cliente B', 'Cliente C', 'Cliente D', 'Cliente E']
    project_managers = ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martín']
    
    # Generar 50 registros de ejemplo
    data = []
    for i in range(50):
        start_date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        data.append({
            'id': f'EDP-{i+1:03d}',
            'proyecto': f'Proyecto {chr(65 + i % 26)}-{i+1}',
            'cliente': random.choice(clients),
            'departamento': random.choice(departments),
            'estado': random.choice(states),
            'fecha_inicio': start_date.strftime('%Y-%m-%d'),
            'fecha_fin': (start_date + timedelta(days=random.randint(30, 180))).strftime('%Y-%m-%d'),
            'monto': random.randint(10000, 500000),
            'gestor': random.choice(project_managers),
            'descripcion': f'Descripción del proyecto {i+1}',
            'prioridad': random.choice(['Alta', 'Media', 'Baja']),
            'progreso': random.randint(0, 100),
            'presupuesto': random.randint(50000, 1000000),
            'categoria': random.choice(['Desarrollo', 'Consultoría', 'Soporte', 'Implementación'])
        })
    
    return pd.DataFrame(data)

def generate_demo_log_data():
    """Generar datos demo para LOG cuando Google Sheets no está disponible"""
    
    actions = ['Creado', 'Modificado', 'Completado', 'Cancelado', 'Revisado']
    users = ['admin', 'user1', 'user2', 'manager1']
    
    data = []
    for i in range(100):
        timestamp = datetime.now() - timedelta(hours=random.randint(0, 720))
        
        data.append({
            'id': i+1,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': random.choice(users),
            'accion': random.choice(actions),
            'edp_id': f'EDP-{random.randint(1, 50):03d}',
            'descripcion': f'Acción {random.choice(actions)} realizada',
            'ip': f'192.168.1.{random.randint(1, 254)}'
        })
    
    return pd.DataFrame(data)

def get_demo_data(range_name):
    """
    Obtener datos demo basados en el rango solicitado
    
    Args:
        range_name: Rango de Google Sheets solicitado
        
    Returns:
        DataFrame con datos demo apropiados
    """
    print(f"🎭 Generando datos demo para {range_name}")
    
    if 'edp!' in range_name.lower():
        return generate_demo_edp_data()
    elif 'log!' in range_name.lower():
        return generate_demo_log_data()
    else:
        # Datos genéricos
        return pd.DataFrame({
            'columna1': ['Valor1', 'Valor2', 'Valor3'],
            'columna2': [100, 200, 300],
            'columna3': ['Demo', 'Data', 'Mode']
        })

if __name__ == "__main__":
    # Test
    print("Generando datos demo de EDP...")
    edp_df = generate_demo_edp_data()
    print(f"✅ Generados {len(edp_df)} registros EDP demo")
    
    print("Generando datos demo de LOG...")
    log_df = generate_demo_log_data()
    print(f"✅ Generados {len(log_df)} registros LOG demo")
