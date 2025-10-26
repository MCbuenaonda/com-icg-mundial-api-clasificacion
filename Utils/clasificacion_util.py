from fastapi import HTTPException
from collections import defaultdict
import random

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
        clasificados_mundial.append(tabla_posiciones[:6])  # Los primeros 6 lugares van al mundial
        clasificados_repechaje.append(tabla_posiciones[6]) # El 7mo lugar va al repechaje
        eliminados.append(tabla_posiciones[7:]) # Los demás quedan eliminados

    if confederacion_id == 4:
        clasificados_mundial.append(tabla_posiciones[0])  # El primer lugar va al mundial
        clasificados_ronda.append(tabla_posiciones[1:5])  # Los siguientes 4 lugares van a la ronda 2
        eliminados.append(tabla_posiciones[5:])  # Los demás quedan eliminados
    
    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

