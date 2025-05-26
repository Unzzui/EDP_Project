def calcular_dias_habiles(fecha_inicio, fecha_fin):
    dias = pd.bdate_range(start=fecha_inicio, end=fecha_fin)
    return len(dias) - 1  # no incluye el día de envío

