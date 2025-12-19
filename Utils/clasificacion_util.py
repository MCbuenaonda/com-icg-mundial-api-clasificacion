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
        # jornadas_grupo = organizar_por_jornadas(fixture_grupo, num_equipos, ida_y_vuelta)
            
        # # Agregar las jornadas al diccionario principal
        # for jornada_num, partidos in jornadas_grupo.items():
        #     if jornada_num not in jornadas:
        #         jornadas[jornada_num] = []
        #     jornadas[jornada_num].extend(partidos)
                
        # Agregar todos los juegos con jornada asignada a la lista completa
        for partido in fixture_grupo:
            partido['fase_id'] = fase_id
            # Ya tienen el atributo 'jornada' asignado en asignar_partidos_a_jornadas
            juegos_creados.append(partido)
            
    
    
    # Log de resumen
    #logger.info(f"Se crearon {len(juegos_creados)} juegos distribuidos en {len(jornadas)} jornadas")
    
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
    cat_jornadas = grupos_service.get_catalogo_jornadas(num_equipos, logger)

    tipo_juego = "ida" if ida_y_vuelta else "unico"

    for jornada in cat_jornadas:
        logger.info(f"Procesando Jornada ID: {jornada['jornada_id']}")

        # Iteramos de 2 en 2 para cubrir los pares (1,2), (3,4), etc.
        for i in range(1, num_equipos + 1, 2):
            key_local = f'pos{i}'
            key_visitante = f'pos{i+1}'

            # Verificamos si las llaves existen en el objeto jornada
            if key_local in jornada and key_visitante in jornada:
                idx_local = jornada[key_local]
                idx_visitante = jornada[key_visitante]

                # Validamos que los índices existan en nuestra lista de equipos
                if idx_local < num_equipos and idx_visitante < num_equipos:
                    equipo_local = equipos[idx_local]
                    equipo_visitante = equipos[idx_visitante]

                    # Si es ida y vuelta, verificamos si ya pasamos la mitad de las jornadas
                    if ida_y_vuelta:
                        limite = 1 if num_equipos == 2 else (num_equipos - 1 if num_equipos % 2 == 0 else num_equipos)
                        if jornada['jornada_id'] > limite:
                            tipo_juego = "vuelta"

                    juego = {
                        "mundial_id": mundial_id,
                        "grupo": grupo_name,
                        "confederacion_id": confederacion_id,
                        "equipo_local": equipo_local,
                        "equipo_visitante": equipo_visitante,
                        "tipo": tipo_juego,
                        "fecha": None,
                        "resultado": None,
                        "estado": "pendiente",
                        "jornada": f"Jornada {jornada['jornada_id']}",
                        "tag": f"#{equipo_local['siglas']}{equipo_visitante['siglas']}"
                    }

                    fixture.append(juego)
                    logger.info(f"Juego {tipo_juego}: {equipo_local['nombre']} vs {equipo_visitante['nombre']}")

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

def asignar_fechas_por_jornada(resultado_jornadas, confederacion_id, logger):
    """
    Asigna fechas a los juegos según su número de jornada y configuración de confederación.
    - Todas las jornadas 1 inician desde la fecha base (±2 días)
    - Cada confederación tiene su ritmo de días entre jornadas
    - Cada fecha tiene variación de ±2 días para distribuir partidos
    
    Args:
        resultado_jornadas: Diccionario con estructura {jornadas: {...}, juegos: [...]}
        logger: Logger para registrar información
    
    Returns:
        dict: Estructura actualizada con fechas asignadas
    """
    # Fechas del torneo
    ultima_fecha = obtener_ultima_fecha(confederacion_id, logger)
    fecha_inicio = datetime.strptime(ultima_fecha, '%Y-%m-%d')    
    
    logger.info(f"Fecha inicio base del torneo: {fecha_inicio.strftime('%Y-%m-%d')}")
    
    # Configuración de días entre jornadas por confederación
    confederaciones_config = {
        1: {"nombre": "UEFA", "dias_entre_jornadas": 7},           # 7 días entre jornadas
        2: {"nombre": "CONMEBOL", "dias_entre_jornadas": 10},      # 10 días entre jornadas
        3: {"nombre": "CONCACAF", "dias_entre_jornadas": 14},      # 14 días entre jornadas
        4: {"nombre": "CAF", "dias_entre_jornadas": 6},            # 6 días entre jornadas
        5: {"nombre": "OFC", "dias_entre_jornadas": 30},           # 30 días entre jornadas
        6: {"nombre": "AFC", "dias_entre_jornadas": 8}             # 8 días entre jornadas
    }
    
    # Agrupar juegos por confederación y jornada
    juegos_por_confederacion = {}
    
    for juego in resultado_jornadas['juegos']:
        confederacion_id = juego.get('confederacion_id')
        jornada_str = juego.get('jornada', '')
        
        if not confederacion_id or not jornada_str:
            continue
        
        # Extraer el número de jornada (ej: "Jornada 1" -> 1)
        try:
            num_jornada = int(jornada_str.split()[1])
        except (IndexError, ValueError):
            logger.warning(f"No se pudo extraer número de jornada de: {jornada_str}")
            continue
        
        if confederacion_id not in juegos_por_confederacion:
            juegos_por_confederacion[confederacion_id] = {}
        
        if num_jornada not in juegos_por_confederacion[confederacion_id]:
            juegos_por_confederacion[confederacion_id][num_jornada] = []
        
        juegos_por_confederacion[confederacion_id][num_jornada].append(juego)
    
    logger.info(f"Procesando {len(juegos_por_confederacion)} confederaciones")
    
    # Procesar cada confederación
    for confederacion_id in sorted(juegos_por_confederacion.keys()):
        config = confederaciones_config.get(confederacion_id, {"nombre": f"Conf {confederacion_id}", "dias_entre_jornadas": 7})
        conf_nombre = config["nombre"]
        dias_entre_jornadas = config["dias_entre_jornadas"]
        
        jornadas_dict = juegos_por_confederacion[confederacion_id]
        num_jornadas = len(jornadas_dict)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Confederación: {conf_nombre} (ID: {confederacion_id})")
        logger.info(f"Jornadas: {num_jornadas}")
        logger.info(f"Días entre jornadas: {dias_entre_jornadas}")
        logger.info(f"{'='*60}")
        
        # Procesar cada jornada en orden
        for num_jornada in sorted(jornadas_dict.keys()):
            juegos_jornada = jornadas_dict[num_jornada]
            
            # Calcular fecha base para esta jornada
            if num_jornada == 1:
                # Jornada 1: fecha inicio ±2 días
                dias_variacion = random.randint(-2, 2)
                fecha_base_jornada = fecha_inicio + timedelta(days=dias_variacion)
            else:
                # Jornadas siguientes: fecha_inicio + (num_jornada-1) * dias_entre_jornadas ±2 días
                dias_desde_inicio = (num_jornada - 1) * dias_entre_jornadas
                dias_variacion = random.randint(-2, 2)
                fecha_base_jornada = fecha_inicio + timedelta(days=dias_desde_inicio + dias_variacion)
            
            logger.info(f"  Jornada {num_jornada}: {fecha_base_jornada.strftime('%Y-%m-%d')} ({len(juegos_jornada)} juegos)")
            
            # Asignar fechas y horarios a los juegos de esta jornada
            asignar_fechas_y_horarios_a_juegos(juegos_jornada, fecha_base_jornada, conf_nombre, logger)
    
    # Asignar ubicación a cada juego
    logger.info(f"\nAsignando ubicaciones...")
    for juego in resultado_jornadas['juegos']:
        juego['ubicacion'] = ciudad_service.get_ciudad_anfitrion(juego.get("equipo_local", {}).get("id"), logger)
    
    logger.info(f"\n✅ Fechas asignadas exitosamente a {len(resultado_jornadas['juegos'])} juegos")
    
    return resultado_jornadas

def asignar_fechas_y_horarios_a_juegos(juegos, fecha_base, conf_nombre, logger):
    """
    Asigna fechas y horarios a los juegos de una jornada.
    Cada juego obtiene la fecha base ±2 días para distribuir la carga.
    
    Args:
        juegos: Lista de juegos de la jornada
        fecha_base: Fecha base (datetime) para la jornada
        conf_nombre: Nombre de la confederación
        logger: Logger para registrar información
    """
    from datetime import datetime, timedelta
    import random
    
    # Horarios según confederación
    horarios_por_confederacion = {
        "UEFA": ["14:00", "16:30", "19:00", "21:30"],
        "CONMEBOL": ["15:00", "17:30", "20:00", "22:00"],
        "CONCACAF": ["16:00", "18:30", "21:00"],
        "CAF": ["10:00", "12:30", "15:00", "17:30", "20:00"],
        "OFC": ["13:00", "15:30", "18:00", "20:30"],
        "AFC": ["11:00", "13:30", "16:00", "18:30", "21:00"]
    }
    
    horarios_base = horarios_por_confederacion.get(conf_nombre, ["10:00", "12:30", "15:00", "17:30", "20:00", "22:30"])
    
    # Expandir horarios si hay muchos juegos
    if len(juegos) > len(horarios_base) * 3:
        horarios_extra = []
        for i in range(len(horarios_base), len(juegos)):
            hora_extra = (datetime.strptime("08:00", "%H:%M") + timedelta(hours=2 * (i % 8))).strftime("%H:%M")
            horarios_extra.append(hora_extra)
        horarios_base.extend(horarios_extra)
    
    # Contador de juegos por fecha para distribuir horarios
    juegos_por_fecha = {}
    
    for juego in juegos:
        # Aplicar variación de ±2 días a la fecha base
        dias_variacion = random.randint(-2, 2)
        fecha_juego = fecha_base + timedelta(days=dias_variacion)
        fecha_str = fecha_juego.strftime("%Y-%m-%d")
        
        # Contar juegos en esta fecha
        if fecha_str not in juegos_por_fecha:
            juegos_por_fecha[fecha_str] = 0
        
        # Asignar horario según cuántos juegos hay ese día
        horario_index = juegos_por_fecha[fecha_str] % len(horarios_base)
        horario = horarios_base[horario_index]
        
        # Crear datetime completo
        fecha_hora = datetime.combine(fecha_juego.date(), datetime.strptime(horario, "%H:%M").time())
        
        # Actualizar el juego con fecha y hora
        juego['fecha'] = fecha_str
        juego['hora'] = horario
        juego['fecha_completa'] = fecha_hora.isoformat()
        juego['fecha_hora_str'] = fecha_hora.strftime("%Y-%m-%d %H:%M")
        
        # Incrementar contador
        juegos_por_fecha[fecha_str] += 1
    
    # Log de distribución
    total_fechas = len(juegos_por_fecha)
    logger.info(f"    → {len(juegos)} juegos distribuidos en {total_fechas} fechas diferentes")

def obtener_ultima_fecha(confederacion_id, logger):
    """
    Obtiene la última fecha de los juegos programados.
    """
    ultimo_juego = juegos_service.get_ultimo_juego_confederacion(confederacion_id, logger)
    ultima_fecha = ultimo_juego.get('fecha', None) if ultimo_juego else None
    logger.info(f"Última fecha para confederación {confederacion_id}: {ultima_fecha}")
    return ultima_fecha