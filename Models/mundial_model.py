from fastapi import HTTPException
from fastapi.responses import JSONResponse
from Services import mundial_service, juegos_service, ciudad_service
import Utils.clasificacion_util as clasificacion_util
from bson import ObjectId

def get_mundial(logger):
    try:
        mundiales = mundial_service.get_mundiales_list(logger)
        
        if not mundiales:
            fase_id = 1
            clasificacion_util.create_first_anfitrion(logger)

            # creacion de grupos para todas las confederaciones de fase 1
            array_grupos = []
            for confederacion_id in range(1, 7):
                grupos = clasificacion_util.create_grupos(confederacion_id, fase_id, logger)
                array_grupos.append(grupos)

            resultado_jornadas = clasificacion_util.create_juegos(array_grupos, True, fase_id, logger)
            
            # Asignar fechas a los juegos por jornada
            juegos_con_fechas = asignar_fechas_por_jornada(resultado_jornadas, logger)
            # Guardar los juegos con fechas en MongoDB
            juegos = juegos_con_fechas.get('juegos')
            juegos_service.create_juegos(juegos, logger)
        
        juegos_pendientes = juegos_service.get_juegos_por_estado("pendiente", logger)
        juegos_finalizados = juegos_service.get_juegos_por_estado("finalizado", logger)
        todos_juegos = juegos_pendientes + juegos_finalizados
        mundial = mundial_service.get_mundial_activo(logger)

        # Convertir ObjectId a string para serialización JSON
        mundial_serializable = convertir_objectid_a_string(mundial)
        juegos_serializables = convertir_objectid_a_string(todos_juegos)

        return JSONResponse(content={"mundial": mundial_serializable, "juegos": juegos_serializables})
    except Exception as e:
        logger.error(f"Error al obtener el mundial: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener el mundial: {str(e)}")


def asignar_fechas_por_jornada(resultado_jornadas, logger):
    """
    Asigna fechas a los juegos organizados por jornada con distribución inteligente por confederación.
    
    Args:
        resultado_jornadas: Diccionario con estructura {jornadas: {...}, juegos: [...]}
        logger: Logger para registrar información
    
    Returns:
        dict: Estructura actualizada con fechas asignadas
    """
    from datetime import datetime, timedelta
    
    # Fechas del torneo
    fecha_inicio = datetime(1896, 1, 7)
    fecha_fin = datetime(1899, 12, 31)
    dias_totales = (fecha_fin - fecha_inicio).days
    
    # Agrupar jornadas por confederación
    jornadas_por_confederacion = {}
    
    for jornada_nombre, partidos in resultado_jornadas['jornadas'].items():
        if partidos:  # Si hay partidos en esta jornada
            confederacion_id = partidos[0].get('confederacion_id')
            if confederacion_id not in jornadas_por_confederacion:
                jornadas_por_confederacion[confederacion_id] = []
            jornadas_por_confederacion[confederacion_id].append(jornada_nombre)
    
    # Ordenar jornadas por número dentro de cada confederación
    for confederacion_id in jornadas_por_confederacion:
        jornadas_por_confederacion[confederacion_id].sort(
            key=lambda x: int(x.split()[1])
        )
    
    logger.info(f"Distribuyendo fechas desde {fecha_inicio.strftime('%Y-%m-%d')} hasta {fecha_fin.strftime('%Y-%m-%d')}")
    
    # Calcular distribución de tiempo por confederación
    confederaciones_info = {
        1: {"nombre": "UEFA", "peso": 0.30},      # 30% del tiempo (más jornadas)
        2: {"nombre": "CONMEBOL", "peso": 0.15},  # 15% del tiempo 
        3: {"nombre": "CONCACAF", "peso": 0.10},  # 10% del tiempo
        4: {"nombre": "CAF", "peso": 0.25},       # 25% del tiempo (muchas jornadas)
        5: {"nombre": "OFC", "peso": 0.05},       # 5% del tiempo (pocas jornadas)
        6: {"nombre": "AFC", "peso": 0.15}        # 15% del tiempo
    }
    
    fecha_actual = fecha_inicio
    
    # Procesar cada confederación secuencialmente
    for confederacion_id in sorted(jornadas_por_confederacion.keys()):
        jornadas_conf = jornadas_por_confederacion[confederacion_id]
        num_jornadas = len(jornadas_conf)
        
        if num_jornadas == 0:
            continue
            
        # Calcular días disponibles para esta confederación
        peso_confederacion = confederaciones_info[confederacion_id]["peso"]
        dias_confederacion = int(dias_totales * peso_confederacion)
        
        # Calcular días entre jornadas para esta confederación
        if num_jornadas > 1:
            dias_entre_jornadas = dias_confederacion // (num_jornadas - 1)
        else:
            dias_entre_jornadas = dias_confederacion
            
        # Mínimo de 7 días entre jornadas
        dias_entre_jornadas = max(7, dias_entre_jornadas)
        
        conf_nombre = confederaciones_info[confederacion_id]["nombre"]
        logger.info(f"Confederación {conf_nombre}: {num_jornadas} jornadas, {dias_entre_jornadas} días entre jornadas")
        
        # Asignar fechas y horas a las jornadas de esta confederación
        for i, jornada_nombre in enumerate(jornadas_conf):
            fecha_base = fecha_actual + timedelta(days=i * dias_entre_jornadas)
            partidos_jornada = resultado_jornadas['jornadas'][jornada_nombre]
            
            # Asignar fechas variables y horarios a cada partido
            partidos_con_horarios = asignar_fechas_y_horarios_distribuidos(partidos_jornada, fecha_base, logger)
            
            # Actualizar los partidos en la jornada
            resultado_jornadas['jornadas'][jornada_nombre] = partidos_con_horarios
            
            fecha_str = fecha_base.strftime("%Y-%m-%d")
            logger.info(f"  {jornada_nombre} ({conf_nombre}): {fecha_str} (±3 días) - {len(partidos_con_horarios)} partidos distribuidos")
        
        # Mover la fecha actual al final del período de esta confederación
        fecha_actual += timedelta(days=dias_confederacion)
    
    # También actualizar las fechas y horas en el array completo de juegos
    for juego in resultado_jornadas['juegos']:
        jornada_juego = juego.get('jornada')
        if jornada_juego in resultado_jornadas['jornadas']:
            # Buscar el partido correspondiente en la jornada actualizada
            partidos_jornada = resultado_jornadas['jornadas'][jornada_juego]
            
            # Encontrar el partido que coincida por equipos y grupo
            for partido_jornada in partidos_jornada:
                if (juego.get('grupo') == partido_jornada.get('grupo') and
                    juego.get('equipo_local') == partido_jornada.get('equipo_local') and
                    juego.get('equipo_visitante') == partido_jornada.get('equipo_visitante')):
                    
                    # Sincronizar todos los campos de fecha y hora
                    juego['fecha'] = partido_jornada['fecha']
                    juego['hora'] = partido_jornada['hora']
                    juego['fecha_completa'] = partido_jornada['fecha_completa']
                    juego['fecha_hora_str'] = partido_jornada['fecha_hora_str']
                    break
        juego['ubicacion'] = ciudad_service.get_ciudad_anfitrion(juego.get("equipo_local", {}).get("id"), logger)
    
    logger.info(f"Fechas asignadas exitosamente a {resultado_jornadas['total_juegos']} juegos")
    
    return resultado_jornadas


def convertir_objectid_a_string(data):
    """
    Convierte recursivamente todos los ObjectId a strings para serialización JSON.
    
    Args:
        data: Puede ser dict, list, ObjectId o cualquier otro tipo
    
    Returns:
        Los mismos datos con ObjectId convertidos a string
    """
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convertir_objectid_a_string(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convertir_objectid_a_string(item) for item in data]
    else:
        return data


def asignar_fechas_y_horarios_distribuidos(partidos, fecha_base, logger):
    """
    Asigna fechas variables (±3 días) y horarios diferentes a partidos para distribuir la carga.
    
    Args:
        partidos: Lista de partidos de una jornada
        fecha_base: Fecha base (datetime) para los partidos
        logger: Logger para registrar información
    
    Returns:
        Lista de partidos con fechas y horarios distribuidos
    """
    from datetime import datetime, timedelta
    import random
    
    # Horarios disponibles para partidos (formato 24h)
    horarios_base = [
        "10:00", "12:30", "15:00", "17:30", "20:00", "22:30"
    ]
    
    # Si hay muchos partidos, expandir horarios
    if len(partidos) > len(horarios_base):
        horarios_adicionales = []
        for i in range(len(horarios_base), len(partidos)):
            # Agregar horarios cada 2 horas
            hora_extra = (datetime.strptime("08:00", "%H:%M") + 
                         timedelta(hours=2 * i)).strftime("%H:%M")
            horarios_adicionales.append(hora_extra)
        horarios_base.extend(horarios_adicionales)
    
    partidos_distribuidos = []
    fechas_usadas = {}  # Contador de partidos por fecha
    
    for i, partido in enumerate(partidos):
        # Generar variación de fecha: -3 a +3 días
        variacion_dias = random.randint(-3, 3)
        fecha_partido = fecha_base + timedelta(days=variacion_dias)
        fecha_str = fecha_partido.strftime("%Y-%m-%d")
        
        # Contar cuántos partidos ya están programados para esta fecha
        if fecha_str not in fechas_usadas:
            fechas_usadas[fecha_str] = 0
        
        partidos_del_dia = fechas_usadas[fecha_str]
        
        # Si ya hay muchos partidos ese día (más de 6), intentar otra fecha
        intentos = 0
        while partidos_del_dia >= 6 and intentos < 10:
            variacion_dias = random.randint(-3, 3)
            fecha_partido = fecha_base + timedelta(days=variacion_dias)
            fecha_str = fecha_partido.strftime("%Y-%m-%d")
            
            if fecha_str not in fechas_usadas:
                fechas_usadas[fecha_str] = 0
            partidos_del_dia = fechas_usadas[fecha_str]
            intentos += 1
        
        # Asignar horario basado en cuántos partidos ya hay ese día
        horario_index = partidos_del_dia % len(horarios_base)
        horario = horarios_base[horario_index]
        
        # Crear datetime completo con fecha y hora
        fecha_hora = datetime.combine(fecha_partido.date(), 
                                    datetime.strptime(horario, "%H:%M").time())
        
        # Actualizar contador de partidos para esta fecha
        fechas_usadas[fecha_str] += 1
        
        # Actualizar los campos del partido
        partido_actualizado = partido.copy()
        partido_actualizado['fecha'] = fecha_str
        partido_actualizado['hora'] = horario
        partido_actualizado['fecha_completa'] = fecha_hora.isoformat()
        partido_actualizado['fecha_hora_str'] = fecha_hora.strftime("%Y-%m-%d %H:%M")
        partido_actualizado['variacion_dias'] = variacion_dias  # Para debugging
        
        partidos_distribuidos.append(partido_actualizado)
    
    # Log de resumen de distribución
    logger.info(f"Distribución de partidos: {dict(fechas_usadas)}")
    
    return partidos_distribuidos


def asignar_horarios_partidos(partidos, fecha_base):
    """
    FUNCIÓN LEGACY - Mantener para compatibilidad si es necesaria.
    Asigna horarios diferentes a partidos que se juegan el mismo día.
    """
    from datetime import datetime, timedelta
    
    # Horarios disponibles para partidos (formato 24h)
    horarios_disponibles = [
        "10:00", "12:30", "15:00", "17:30", "20:00", "22:30"
    ]
    
    # Si hay más partidos que horarios, usar horarios adicionales
    if len(partidos) > len(horarios_disponibles):
        horarios_extras = []
        for i in range(len(horarios_disponibles), len(partidos)):
            # Agregar horarios cada 2.5 horas después del último
            hora_extra = (datetime.strptime("22:30", "%H:%M") + 
                         timedelta(hours=2.5 * (i - len(horarios_disponibles) + 1))).strftime("%H:%M")
            horarios_extras.append(hora_extra)
        horarios_disponibles.extend(horarios_extras)
    
    partidos_actualizados = []
    
    for i, partido in enumerate(partidos):
        # Asignar horario secuencial
        horario = horarios_disponibles[i] if i < len(horarios_disponibles) else horarios_disponibles[-1]
        
        # Crear datetime completo con fecha y hora
        fecha_hora = datetime.combine(fecha_base.date(), 
                                    datetime.strptime(horario, "%H:%M").time())
        
        # Actualizar los campos de fecha y hora
        partido_actualizado = partido.copy()
        partido_actualizado['fecha'] = fecha_base.strftime("%Y-%m-%d")
        partido_actualizado['hora'] = horario
        partido_actualizado['fecha_completa'] = fecha_hora.isoformat()
        partido_actualizado['fecha_hora_str'] = fecha_hora.strftime("%Y-%m-%d %H:%M")
        
        partidos_actualizados.append(partido_actualizado)
    
    return partidos_actualizados

 