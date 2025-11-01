from fastapi import HTTPException
from collections import defaultdict
from Services import pais_service, grupos_service, ciudad_service
import random
from datetime import datetime, timedelta
from Services import juegos_service

def clasificados_fase_1(tabla_posiciones, confederacion_id, logger):
    """
    Lógica para determinar los equipos clasificados en la fase 1
    """
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []
    
    # CONCACAF, OCF, AFC al ser grupos de 2 equipos, clasifican 1 y elimina 1
    if confederacion_id == 3 or confederacion_id == 5 or confederacion_id == 6:
        clasificados_ronda.append(tabla_posiciones[0])
        eliminados.append(tabla_posiciones[1])
    
    # UEFA Califica al mundial el 1er lugar y a la sigunda ronda el 2do lugar, esperando los 4 mejores 3ros lugares
    if confederacion_id == 1:
        clasificados_mundial.append(tabla_posiciones[0])
        clasificados_ronda.append(tabla_posiciones[1])

    if confederacion_id == 2:
        clasificados_mundial.extend(tabla_posiciones[:6])  # Los primeros 6 lugares van al mundial
        clasificados_repechaje.append(tabla_posiciones[6]) # El 7mo lugar va al repechaje
        eliminados.extend(tabla_posiciones[7:]) # Los demás quedan eliminados

    if confederacion_id == 4:
        clasificados_mundial.append(tabla_posiciones[0])  # El primer lugar va al mundial
        clasificados_ronda.extend(tabla_posiciones[1:5])  # Los siguientes 4 lugares van a la ronda 2
        eliminados.extend(tabla_posiciones[5:])  # Los demás quedan eliminados

    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

def clasificados_fase_2(tabla_posiciones, confederacion_id, logger):
    """
    Lógica para determinar los equipos clasificados en la fase 2
    """
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []
    
    # UEFA 1er lugar de cada grupo califica a tercera ronda, el resto quedan eliminados
    if confederacion_id == 1:
        clasificados_ronda.append(tabla_posiciones[0])
        eliminados.extend(tabla_posiciones[1:])

    # CONCACAF, OFC, AFC 1ro y 2do de cada grupo pasa a siguiente ronda, el resto quedan eliminados
    if confederacion_id == 3 or confederacion_id == 5 or confederacion_id == 6:
        clasificados_ronda.extend(tabla_posiciones[0:2])
        eliminados.extend(tabla_posiciones[2:])

    # CAF 1er lugar de cada grupo califica a tercera ronda, el resto quedan eliminados
    if confederacion_id == 4:
        clasificados_ronda.append(tabla_posiciones[0])  # Los siguientes 4 lugares van a la ronda 2
        eliminados.extend(tabla_posiciones[1:])  # Los demás quedan eliminados

    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

def clasificados_fase_3(tabla_posiciones, confederacion_id, logger):
    """
    Lógica para determinar los equipos clasificados en la fase 2
    """
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []
    
    # UEFA 1er lugar de cada grupo califica a tercera ronda, el resto quedan eliminados
    if confederacion_id == 1:
        clasificados_mundial.append(tabla_posiciones[0])
        eliminados.extend(tabla_posiciones[1:])

    # CONCACAF 1ro y 2do de cada grupo pasa a siguiente ronda, el resto quedan eliminados 
    if confederacion_id == 3:
        clasificados_mundial.extend(tabla_posiciones[0:2])

    # CAF 1er lugar califica a repechaje, el resto quedan eliminados
    if confederacion_id == 4:
        clasificados_repechaje.append(tabla_posiciones[0])
        eliminados.extend(tabla_posiciones[1:])  # Los demás quedan eliminados

    # OFC 1er lugar califica a siguiente ronda, el resto quedan eliminados
    if confederacion_id == 5:
        clasificados_ronda.append(tabla_posiciones[0])
        eliminados.extend(tabla_posiciones[1:])  # Los demás quedan eliminados

    # AFC 1ro y 2do de cada grupo pasa al mundial, 3er y 4to lugar pasan a siguiente ronda, el resto quedan eliminados
    if confederacion_id == 6:
        clasificados_mundial.extend(tabla_posiciones[0:2])
        clasificados_ronda.extend(tabla_posiciones[2:4])
        eliminados.extend(tabla_posiciones[4:])

    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

def clasificados_fase_4(tabla_posiciones, confederacion_id, logger):
    """
    Lógica para determinar los equipos clasificados en la fase 2
    """
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []

    # OFC 1er lugar califica al mundial, el perdedor a repechaje
    if confederacion_id == 5:
        clasificados_mundial.append(tabla_posiciones[0])  
        clasificados_repechaje.append(tabla_posiciones[1])

    # AFC 1ro de cada grupo pasa al mundial, 2do a siguiente ronda, el resto quedan eliminados
    if confederacion_id == 6:
        clasificados_mundial.append(tabla_posiciones[0])
        clasificados_ronda.append(tabla_posiciones[1])
        eliminados.extend(tabla_posiciones[2:])

    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

def clasificados_fase_5(tabla_posiciones, confederacion_id, logger):
    """
    Lógica para determinar los equipos clasificados en la fase 5
    """
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []

    # AFC 1ro de de grupo pasa al repechaje, el resto quedan eliminados
    if confederacion_id == 6:
        clasificados_repechaje.append(tabla_posiciones[0])
        eliminados.append(tabla_posiciones[1])

    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

def create_grupos(mundial_id, confederacion_id, fase_id, logger):
    clasificado_directo = None
    paises = pais_service.get_paises(confederacion_id, 'disponible', logger)
    
    NUM_GRUPOS = 1
    NUM_EQUIPOS = 1
    if fase_id == 2:
        # Mapeo de confederacion_id a (NUM_GRUPOS, NUM_EQUIPOS)
        configuraciones_fase_2 = {
            1: (8, 2),  # UEFA: 8 grupos de 2
            3: (6, 5),  # CONCACAF: 6 grupos de 5
            4: (2, 2),  # CAF: 2 grupos de 2
            5: (2, 4),  # OFC: 2 grupos de 4
            6: (9, 4)   # AFC: 9 grupos de 4
        }

        # Intenta obtener la configuración y asignar las variables
        if confederacion_id in configuraciones_fase_2:
            NUM_GRUPOS, NUM_EQUIPOS = configuraciones_fase_2[confederacion_id]

    if fase_id == 3:    
        # Mapeo de confederacion_id a (NUM_GRUPOS, NUM_EQUIPOS)
        configuraciones_fase_3 = {
            1: (4, 2),  # UEFA: 4 grupos de 2
            3: (3, 4),  # CONCACAF: 3 grupos de 4
            4: (1, 2),  # CAF: 1 grupo de 2
            5: (2, 2),  # OFC: 2 grupos de 2
            6: (3, 6)   # AFC: 3 grupos de 6
        }

        # Intenta obtener la configuración y asignar las variables
        if confederacion_id in configuraciones_fase_3:
            NUM_GRUPOS, NUM_EQUIPOS = configuraciones_fase_3[confederacion_id]
    
    if fase_id == 4:
        # Mapeo de confederacion_id a (NUM_GRUPOS, NUM_EQUIPOS)
        configuraciones_fase_4 = {
            5: (1, 2),  # OFC: 1 grupo de 2
            6: (2, 3)   # AFC: 2 grupos de 3
        }

        # Intenta obtener la configuración y asignar las variables
        if confederacion_id in configuraciones_fase_4:
            NUM_GRUPOS, NUM_EQUIPOS = configuraciones_fase_4[confederacion_id]
    
    if fase_id == 5:
        # Mapeo de confederacion_id a (NUM_GRUPOS, NUM_EQUIPOS)
        configuraciones_fase_5 = {
            6: (1, 2)   # AFC: 1 grupo de 2
        }

        # Intenta obtener la configuración y asignar las variables
        if confederacion_id in configuraciones_fase_5:
            NUM_GRUPOS, NUM_EQUIPOS = configuraciones_fase_5[confederacion_id]

    grupos_config = [NUM_EQUIPOS] * NUM_GRUPOS 

    # 1. División en 12 grupos
    grupos = defaultdict(list)
    equipos_shuffled = paises[:]
    random.shuffle(equipos_shuffled)
            
    # Reparto de equipos   
    equipo_idx = 0
    for i in range(NUM_GRUPOS):
        tamano_grupo = grupos_config[i]
        grupos[f"Grupo {chr(65 + i)}"] = equipos_shuffled[equipo_idx : equipo_idx + tamano_grupo]
        equipo_idx += tamano_grupo
            
    documento_grupos = {
        "mundial_id": mundial_id,
        "confederacion_id": confederacion_id,
        "fase_id": fase_id,
        "clasificado_directo": clasificado_directo,
        "grupos": grupos
    }

    grupos_service.create_grupos(documento_grupos, logger)
    
    # Retornar la estructura completa incluyendo el confederacion_id
    return documento_grupos


def create_juegos(mundial_id, confederacion_id, grupos_doc, ida_y_vuelta=False, fase_id=None, logger=None):
    jornadas = {}
    juegos_creados = []
    grupos = grupos_doc['grupos']

    for grupo_name, equipos in grupos.items():
        num_equipos = len(equipos)
        logger.info(f"Creando juegos para {grupo_name} (Confederación {confederacion_id}) con {num_equipos} equipos.")
            
        # Crear fixture completo para el grupo (todos vs todos)
        fixture_grupo = generar_fixture_grupo(mundial_id, equipos, grupo_name, confederacion_id, ida_y_vuelta, logger)
            
        # Organizar por jornadas
        jornadas_grupo = organizar_por_jornadas(fixture_grupo, num_equipos, ida_y_vuelta)
            
        # Agregar las jornadas al diccionario principal
        for jornada_num, partidos in jornadas_grupo.items():
            if jornada_num not in jornadas:
                jornadas[jornada_num] = []
            jornadas[jornada_num].extend(partidos)
                
        # Agregar todos los juegos con jornada asignada a la lista completa
        for jornada_nombre, partidos in jornadas_grupo.items():
            for partido in partidos:
                partido['fase_id'] = fase_id
                # Ya tienen el atributo 'jornada' asignado en asignar_partidos_a_jornadas
                juegos_creados.append(partido)
    
    
    # Log de resumen
    logger.info(f"Se crearon {len(juegos_creados)} juegos distribuidos en {len(jornadas)} jornadas")
    
    return {
        "jornadas": jornadas,
        "juegos": juegos_creados,
        "total_jornadas": len(jornadas),
        "total_juegos": len(juegos_creados)
    }    


def generar_fixture_grupo(mundial_id, equipos, grupo_name, confederacion_id, ida_y_vuelta, logger):
    """
    Genera todos los partidos para un grupo específico.
    """
    fixture = []
    num_equipos = len(equipos)
    
    for i in range(num_equipos):
        for j in range(i + 1, num_equipos):
            # Alternar quién es local/visitante basado en la posición
            if (i + j) % 2 == 0:
                equipo_local = equipos[i]
                equipo_visitante = equipos[j]
            else:
                equipo_local = equipos[j]
                equipo_visitante = equipos[i]
            
            # Crear juego de ida
            juego_ida = {
                "mundial_id": mundial_id,
                "grupo": grupo_name,
                "confederacion_id": confederacion_id,
                "equipo_local": equipo_local,
                "equipo_visitante": equipo_visitante,
                "tipo": "ida" if ida_y_vuelta else "unico",
                "fecha": None,
                "resultado": None,
                "estado": "pendiente",
                "tag": f"#{equipo_local['siglas']}{equipo_visitante['siglas']}"
            }
            
            fixture.append(juego_ida)
            logger.info(f"Juego {'de ida' if ida_y_vuelta else ''}: {equipo_local['nombre']} (Local) vs {equipo_visitante['nombre']} (Visitante)")
            
            # Si se requieren juegos de ida y vuelta
            if ida_y_vuelta:
                juego_vuelta = {
                    "mundial_id": mundial_id,
                    "grupo": grupo_name,
                    "confederacion_id": confederacion_id,
                    "equipo_local": equipo_visitante,
                    "equipo_visitante": equipo_local,
                    "tipo": "vuelta",
                    "fecha": None,
                    "resultado": None,
                    "estado": "pendiente",
                    "tag": f"#{equipo_local['siglas']}{equipo_visitante['siglas']}"
                }
                
                fixture.append(juego_vuelta)
                logger.info(f"Juego de vuelta: {equipo_visitante['nombre']} (Local) vs {equipo_local['nombre']} (Visitante)")
    
    return fixture

def organizar_por_jornadas(fixture, num_equipos, ida_y_vuelta):
    """
    Organiza los partidos en jornadas evitando que un equipo juegue más de una vez por jornada.
    Calcula las jornadas específicas para cada confederación según el número de equipos.
    
    Args:
        fixture: Lista de todos los partidos del grupo
        num_equipos: Número de equipos en el grupo
        ida_y_vuelta: Si incluye partidos de ida y vuelta
    
    Returns:
        dict: Jornadas organizadas con sus respectivos partidos
    """
    jornadas = {}
    
    # Calcular número de jornadas específicas según el número de equipos
    if num_equipos <= 1:
        total_jornadas = 1
    elif num_equipos == 2:
        # 2 equipos: ida y vuelta = 2 jornadas
        total_jornadas = 2 if ida_y_vuelta else 1
    elif num_equipos == 4:
        # 4 equipos: 3 jornadas de ida + 3 jornadas de vuelta = 6 jornadas
        total_jornadas = 6 if ida_y_vuelta else 3
    elif num_equipos == 5:
        # 5 equipos: 4 jornadas de ida + 4 jornadas de vuelta = 8 jornadas
        total_jornadas = 8 if ida_y_vuelta else 4
    elif num_equipos == 6:
        # 6 equipos: 5 jornadas de ida + 5 jornadas de vuelta = 10 jornadas
        total_jornadas = 10 if ida_y_vuelta else 5
    elif num_equipos == 10:
        # 10 equipos: 9 jornadas de ida + 9 jornadas de vuelta = 18 jornadas
        total_jornadas = 18 if ida_y_vuelta else 9
    else:
        # Fórmula general: para n equipos, (n-1) jornadas por vuelta
        if ida_y_vuelta:
            total_jornadas = (num_equipos - 1) * 2
        else:
            total_jornadas = (num_equipos - 1)
    
    # Separar partidos de ida y vuelta
    partidos_ida = [p for p in fixture if p['tipo'] in ['ida', 'unico']]
    partidos_vuelta = [p for p in fixture if p['tipo'] == 'vuelta']
    
    jornada_actual = 1
    
    # Asignar partidos de ida
    jornadas_ida = asignar_partidos_a_jornadas(partidos_ida, jornada_actual)
    jornadas.update(jornadas_ida)
    
    # Si hay partidos de vuelta, asignarlos consecutivamente después de las jornadas de ida
    if partidos_vuelta:
        # Calcular la siguiente jornada disponible (después de las de ida)
        jornada_inicial_vuelta = len(jornadas_ida) + 1
        jornadas_vuelta = asignar_partidos_a_jornadas(partidos_vuelta, jornada_inicial_vuelta)
        jornadas.update(jornadas_vuelta)
    
    return jornadas

def asignar_partidos_a_jornadas(partidos, jornada_inicial):
    """
    Asigna partidos a jornadas evitando conflictos de equipos.
    """
    jornadas = {}
    partidos_pendientes = partidos.copy()
    jornada_num = jornada_inicial
    
    while partidos_pendientes:
        jornada_key = f"Jornada {jornada_num}"
        jornadas[jornada_key] = []
        equipos_ocupados = set()
        
        # Intentar asignar partidos a la jornada actual
        partidos_para_remover = []
        
        for partido in partidos_pendientes:
            equipo_local_id = partido['equipo_local'].get('id', partido['equipo_local']['nombre'])
            equipo_visitante_id = partido['equipo_visitante'].get('id', partido['equipo_visitante']['nombre'])
            
            # Verificar si alguno de los equipos ya está ocupado en esta jornada
            if equipo_local_id not in equipos_ocupados and equipo_visitante_id not in equipos_ocupados:
                # Asignar el partido a esta jornada
                partido_con_jornada = partido.copy()
                partido_con_jornada['jornada'] = jornada_key
                jornadas[jornada_key].append(partido_con_jornada)
                
                # Marcar equipos como ocupados
                equipos_ocupados.add(equipo_local_id)
                equipos_ocupados.add(equipo_visitante_id)
                
                # Marcar para remover de pendientes
                partidos_para_remover.append(partido)
        
        # Remover partidos asignados
        for partido in partidos_para_remover:
            partidos_pendientes.remove(partido)
        
        jornada_num += 1
    
    return jornadas


def asignar_fechas_por_jornada(resultado_jornadas, logger):
    """
    Asigna fechas a los juegos organizados por jornada con distribución inteligente por confederación.
    Cada confederación tiene sus propias jornadas y variaciones de días específicas.
    
    Args:
        resultado_jornadas: Diccionario con estructura {jornadas: {...}, juegos: [...]}
        logger: Logger para registrar información
    
    Returns:
        dict: Estructura actualizada con fechas asignadas
    """
    # Obtener la confederación del primer juego para determinar la fecha de inicio
    confederacion_id = None
    if resultado_jornadas['juegos']:
        confederacion_id = resultado_jornadas['juegos'][0].get('confederacion_id')
    
    # Obtener la fecha del último juego de esta confederación desde la base de datos
    fecha_inicio = datetime(1896, 1, 7)  # Fecha por defecto
    if confederacion_id:
        try:
            # Buscar el último juego de esta confederación ordenado por fecha descendente
            ultimo_juego = juegos_service.get_ultimo_juego_confederacion(confederacion_id, logger)
            if ultimo_juego and ultimo_juego.get('fecha'):
                # Convertir la fecha string a datetime y agregar algunos días de separación
                fecha_ultimo_juego = datetime.strptime(ultimo_juego['fecha'], '%Y-%m-%d')
                fecha_inicio = fecha_ultimo_juego + timedelta(days=7)  # Iniciar 7 días después del último juego
                logger.info(f"Fecha de inicio calculada desde último juego de confederación {confederacion_id}: {fecha_inicio.strftime('%Y-%m-%d')}")
            else:
                logger.info(f"No se encontraron juegos previos para confederación {confederacion_id}, usando fecha por defecto")
        except Exception as e:
            logger.warning(f"Error al obtener último juego de confederación {confederacion_id}: {str(e)}, usando fecha por defecto")
    
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
    
    # Configuración específica por confederación
    confederaciones_info = {
        1: {  # UEFA (55 equipos en 12 grupos: 7 grupos de 5 + 5 grupos de 4)
            "nombre": "UEFA", 
            "peso": 0.30,      # 30% del tiempo total
            "dias_entre_jornadas": 14,  # 14 días entre jornadas
            "variacion_dias": 5,        # ±5 días de variación
            "descripcion": "7 grupos de 5 equipos (8 jornadas) + 5 grupos de 4 equipos (6 jornadas)"
        },
        2: {  # CONMEBOL (10 equipos en 1 grupo de 10)
            "nombre": "CONMEBOL", 
            "peso": 0.15,      # 15% del tiempo
            "dias_entre_jornadas": 21,  # 21 días entre jornadas (más espaciado)
            "variacion_dias": 4,        # ±4 días de variación
            "descripcion": "1 grupo de 10 equipos (18 jornadas ida y vuelta)"
        },
        3: {  # CONCACAF (10 equipos en 5 grupos de 2)
            "nombre": "CONCACAF", 
            "peso": 0.08,      # 8% del tiempo
            "dias_entre_jornadas": 7,   # 7 días entre jornadas (rápido)
            "variacion_dias": 2,        # ±2 días de variación
            "descripcion": "5 grupos de 2 equipos (2 jornadas ida y vuelta cada grupo)"
        },
        4: {  # CAF (54 equipos en 9 grupos de 6)
            "nombre": "CAF", 
            "peso": 0.25,      # 25% del tiempo
            "dias_entre_jornadas": 12,  # 12 días entre jornadas
            "variacion_dias": 4,        # ±4 días de variación
            "descripcion": "9 grupos de 6 equipos (10 jornadas ida y vuelta cada grupo)"
        },
        5: {  # OFC (4 equipos en 2 grupos de 2)
            "nombre": "OFC", 
            "peso": 0.05,      # 5% del tiempo
            "dias_entre_jornadas": 10,  # 10 días entre jornadas
            "variacion_dias": 3,        # ±3 días de variación
            "descripcion": "2 grupos de 2 equipos (2 jornadas ida y vuelta cada grupo)"
        },
        6: {  # AFC (20 equipos en 10 grupos de 2)
            "nombre": "AFC", 
            "peso": 0.17,      # 17% del tiempo
            "dias_entre_jornadas": 8,   # 8 días entre jornadas
            "variacion_dias": 3,        # ±3 días de variación
            "descripcion": "10 grupos de 2 equipos (2 jornadas ida y vuelta cada grupo)"
        }
    }
    
    fecha_actual = fecha_inicio
    
    # Procesar cada confederación secuencialmente
    for confederacion_id in sorted(jornadas_por_confederacion.keys()):
        jornadas_conf = jornadas_por_confederacion[confederacion_id]
        num_jornadas = len(jornadas_conf)
        
        if num_jornadas == 0:
            continue
            
        # Obtener configuración específica de la confederación
        config_conf = confederaciones_info[confederacion_id]
        peso_confederacion = config_conf["peso"]
        dias_entre_jornadas = config_conf["dias_entre_jornadas"]
        variacion_dias = config_conf["variacion_dias"]
        
        # Calcular días disponibles para esta confederación
        dias_confederacion = int(dias_totales * peso_confederacion)
        
        # Ajustar días entre jornadas si el período asignado es muy corto
        if num_jornadas > 1:
            dias_maximos_entre_jornadas = dias_confederacion // (num_jornadas - 1)
            dias_entre_jornadas = min(dias_entre_jornadas, dias_maximos_entre_jornadas)
            dias_entre_jornadas = max(5, dias_entre_jornadas)  # Mínimo 5 días
        
        conf_nombre = config_conf["nombre"]
        logger.info(f"Confederación {conf_nombre}: {num_jornadas} jornadas, {dias_entre_jornadas} días entre jornadas, ±{variacion_dias} días variación")
        logger.info(f"  Configuración: {config_conf['descripcion']}")
        
        # Asignar fechas y horas a las jornadas de esta confederación
        for i, jornada_nombre in enumerate(jornadas_conf):
            fecha_base = fecha_actual + timedelta(days=i * dias_entre_jornadas)
            partidos_jornada = resultado_jornadas['jornadas'][jornada_nombre]
            
            # Asignar fechas variables y horarios a cada partido con variación específica de la confederación
            partidos_con_horarios = asignar_fechas_y_horarios_distribuidos(
                partidos_jornada, fecha_base, variacion_dias, conf_nombre, logger
            )
            
            # Actualizar los partidos en la jornada
            resultado_jornadas['jornadas'][jornada_nombre] = partidos_con_horarios
            
            fecha_str = fecha_base.strftime("%Y-%m-%d")
            logger.info(f"  {jornada_nombre} ({conf_nombre}): {fecha_str} (±{variacion_dias} días) - {len(partidos_con_horarios)} partidos distribuidos")
        
        # Mover la fecha actual al final del período de esta confederación
        fecha_actual += timedelta(days=dias_confederacion)
        logger.info(f"Confederación {conf_nombre} finalizada. Próxima fecha disponible: {fecha_actual.strftime('%Y-%m-%d')}")
    
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

def asignar_fechas_y_horarios_distribuidos(partidos, fecha_base, variacion_dias, conf_nombre, logger):
    """
    Asigna fechas variables y horarios diferentes a partidos para distribuir la carga.
    Cada confederación tiene su propia variación de días configurada.
    
    Args:
        partidos: Lista de partidos de una jornada
        fecha_base: Fecha base (datetime) para los partidos
        variacion_dias: Número de días de variación específico de la confederación
        conf_nombre: Nombre de la confederación para logs
        logger: Logger para registrar información
    
    Returns:
        Lista de partidos con fechas y horarios distribuidos
    """
    from datetime import datetime, timedelta
    import random
    
    # Horarios disponibles para partidos (formato 24h) según la confederación
    if conf_nombre == "UEFA":
        # Europa: horarios más tarde por tradición futbolística
        horarios_base = ["14:00", "16:30", "19:00", "21:30"]
    elif conf_nombre == "CONMEBOL":
        # Sudamérica: horarios variados, incluyendo tarde/noche
        horarios_base = ["15:00", "17:30", "20:00", "22:00"]
    elif conf_nombre == "CONCACAF":
        # Norte/Centroamérica: horarios de tarde y noche
        horarios_base = ["16:00", "18:30", "21:00"]
    elif conf_nombre == "CAF":
        # África: horarios durante el día para evitar calor extremo
        horarios_base = ["10:00", "12:30", "15:00", "17:30", "20:00"]
    elif conf_nombre == "OFC":
        # Oceanía: horarios de tarde/noche
        horarios_base = ["13:00", "15:30", "18:00", "20:30"]
    elif conf_nombre == "AFC":
        # Asia: horarios variados por zonas horarias
        horarios_base = ["11:00", "13:30", "16:00", "18:30", "21:00"]
    else:
        # Horarios por defecto
        horarios_base = ["10:00", "12:30", "15:00", "17:30", "20:00", "22:30"]
    
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
    
    logger.info(f"Distribuyendo {len(partidos)} partidos para {conf_nombre} con variación de ±{variacion_dias} días")
    
    for i, partido in enumerate(partidos):
        # Generar variación de fecha específica de la confederación
        variacion_aplicada = random.randint(-variacion_dias, variacion_dias)
        fecha_partido = fecha_base + timedelta(days=variacion_aplicada)
        fecha_str = fecha_partido.strftime("%Y-%m-%d")
        
        # Contar cuántos partidos ya están programados para esta fecha
        if fecha_str not in fechas_usadas:
            fechas_usadas[fecha_str] = 0
        
        partidos_del_dia = fechas_usadas[fecha_str]
        
        # Si ya hay muchos partidos ese día (más de 6), intentar otra fecha
        intentos = 0
        max_partidos_por_dia = 8 if conf_nombre in ["UEFA", "CAF"] else 6  # UEFA y CAF pueden tener más partidos por día
        
        while partidos_del_dia >= max_partidos_por_dia and intentos < 15:
            variacion_aplicada = random.randint(-variacion_dias, variacion_dias)
            fecha_partido = fecha_base + timedelta(days=variacion_aplicada)
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
        partido_actualizado['variacion_dias'] = variacion_aplicada  # Para debugging
        partido_actualizado['confederacion_nombre'] = conf_nombre  # Para identificación
        
        partidos_distribuidos.append(partido_actualizado)
    
    # Log de resumen de distribución para esta confederación
    total_fechas_utilizadas = len(fechas_usadas)
    promedio_partidos_por_fecha = sum(fechas_usadas.values()) / total_fechas_utilizadas if total_fechas_utilizadas > 0 else 0
    
    logger.info(f"{conf_nombre}: {len(partidos)} partidos distribuidos en {total_fechas_utilizadas} fechas")
    logger.info(f"{conf_nombre}: Promedio {promedio_partidos_por_fecha:.1f} partidos por fecha")
    logger.info(f"{conf_nombre}: Distribución por fechas: {dict(sorted(fechas_usadas.items()))}")
    
    return partidos_distribuidos