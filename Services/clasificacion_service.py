from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI
from Utils import clasificacion_util
from Services import pais_service, grupos_service, juegos_service

client = MongoClient(MONGODB_URI)
db = client['mundial'] 


def verifica_clasificacion(clasificacion, logger):
    """
    Verifica si algún equipo ha alcanzado la clasificación
    """
    logger.info(f"Generando clasificados para la confederación {clasificacion.confederacion_id} y fase {clasificacion.fase_id}")
    try:
        # Lógica para generar los equipos clasificados
        if clasificacion.fase_id == 1:            
            clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificacion_util.clasificados_fase_1(clasificacion.paises, clasificacion.confederacion_id, logger)
        
        if clasificacion.fase_id == 2:
            clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificacion_util.clasificados_fase_2(clasificacion.paises, clasificacion.confederacion_id, logger)

        if clasificacion.fase_id == 3:
            clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificacion_util.clasificados_fase_3(clasificacion.paises, clasificacion.confederacion_id, logger)

        if clasificacion.fase_id == 4:
            clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificacion_util.clasificados_fase_4(clasificacion.paises, clasificacion.confederacion_id, logger)
        
        if clasificacion.fase_id == 5:
            clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificacion_util.clasificados_fase_5(clasificacion.paises, clasificacion.confederacion_id, logger)

        ajustar_estados(clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados, logger)

        data = {
            "clasificados_mundial": clasificados_mundial,
            "clasificados_ronda": clasificados_ronda,
            "clasificados_repechaje": clasificados_repechaje,
            "eliminados": eliminados
        }

        return data
    except Exception as e:
        logger.error(f"Error al validar países: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error al validar países: {str(e)}")



def ajustar_estados(clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados, logger):
    # Definir los pares (lista_de_equipos, estado)
    actualizaciones = [
        (clasificados_mundial, "clasificado"),
        (clasificados_ronda, "disponible"),
        (clasificados_repechaje, "repechaje"),
        (eliminados, "eliminado"),
    ]

    # Iterar y aplicar la función solo si la lista no está vacía
    for lista_equipos, estado in actualizaciones:
        if lista_equipos: # Esto verifica implícitamente si len(lista) > 0
            actualiza_estado_pais(lista_equipos, estado, logger)

def actualiza_estado_pais(paises, estado, logger):
    try:        
        for pais in paises:
            logger.info(f"Actualizando estado del pais con ID {pais.nombre} a {estado}")
            query = {'nombre': pais.nombre}            
            new_values ={'$set': {'estado': estado}}            
            result = pais_service.update_pais(query, new_values, logger)            
        return True    
    except Exception as e:
        logger.error(f"Error al actualizar el estado del pais: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al actualizar el estado del pais: {str(e)}")


def verifica_grupos_fase(clasificacion, logger):
    """
    Verifica el estatus de los grupos de la confederación y fase dadas,
    y actualiza la clasificación de los equipos si es necesario.
    """
    mundial_id = clasificacion.mundial_id
    confederacion_id = clasificacion.confederacion_id
    fase_id = clasificacion.fase_id

    try:
        filtro_partidos_pendientes = {        
            "mundial_id": mundial_id,
            "confederacion_id": confederacion_id,
            "fase_id": fase_id,
            "estado": "pendiente"
        }

        if db['juegos'].count_documents(filtro_partidos_pendientes) == 0:            
            del filtro_partidos_pendientes["estado"]
            
            grupos_doc = grupos_service.get_grupo(filtro_partidos_pendientes, logger)
            
            if fase_id == 1:
                next_fase_id = 2
                if confederacion_id == 1 or confederacion_id == 4:
                    clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificar_mejores_posicionados(grupos_doc, logger)
                    ajustar_estados(clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados, logger)
            elif fase_id == 2:
                next_fase_id = 3                                                
            elif fase_id == 3:
                next_fase_id = 4
                if confederacion_id == 3:
                    clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificar_mejores_posicionados(grupos_doc, logger)
                    ajustar_estados(clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados, logger)
            elif fase_id == 4:
                next_fase_id = 5
            elif fase_id == 5:
                return False

            
            grupos = clasificacion_util.create_grupos(mundial_id, confederacion_id, next_fase_id, logger)
            resultado_jornadas = clasificacion_util.create_juegos(mundial_id, confederacion_id, grupos, True, next_fase_id, logger)
            
            # Asignar fechas a los juegos por jornada
            juegos_con_fechas = clasificacion_util.asignar_fechas_por_jornada(resultado_jornadas, logger)
            # Guardar los juegos con fechas en MongoDB
            juegos = juegos_con_fechas.get('juegos')
            juegos_service.create_juegos(juegos, logger)

        return True
    except Exception as e:
        logger.error(f"Error al verificar grupos y fases: {str(e)}")
        return False

def clasificar_mejores_posicionados(grupos_doc, logger):
    clasificados_mundial = []
    clasificados_ronda = []
    clasificados_repechaje = []
    eliminados = []

    logger.info(f"Clasificando países mejor posicionados para la confederación {grupos_doc['confederacion_id']} y fase {grupos_doc['fase_id']}")
    confederacion_id = grupos_doc['confederacion_id']
    fase_id = grupos_doc['fase_id'] 
    grupos_data = grupos_doc.get('grupos', {})

    # Estructura de mapeo: (fase_id, confederacion_id) -> (posicion_en_grupo, num_clasificados, lista_destino)
    configuraciones_clasificacion = {
        # UEFA: Fase 1, 3er puesto (índice 2), 4 clasificados, a clasificados_mundial
        (1, 1): {'posicion_idx': 2, 'num_clasificados': 4, 'destino': clasificados_mundial},
        # CAF: Fase 1, 2do puesto (índice 1), 4 clasificados, a clasificados_ronda
        (1, 4): {'posicion_idx': 1, 'num_clasificados': 4, 'destino': clasificados_ronda},
        # CONCACAF: Fase 3, 3er puesto (índice 2), 2 clasificados, a clasificados_repechaje
        (3, 3): {'posicion_idx': 2, 'num_clasificados': 2, 'destino': clasificados_repechaje},
        # Se pueden añadir más lógicas aquí (ej: (1, 3): {...}, (2, 1): {...})
    }

    config = configuraciones_clasificacion.get((fase_id, confederacion_id))

    if config:
        posicion_idx = config['posicion_idx']
        num_clasificados = config['num_clasificados']
        lista_destino = config['destino']

        paises_por_posicion = []
        for lista_paises in grupos_data.values():
            # Obtener el país en la posición_idx si el grupo es lo suficientemente grande
            if len(lista_paises) > posicion_idx:
                paises_por_posicion.append(lista_paises[posicion_idx])
            # Nota: El código original tenía un error lógico en cómo manejaba los eliminados
            # y los adjuntaba de forma incorrecta (eliminados.append(lista_paises[4:])).
            # Esta simplificación se enfoca solo en la clasificación de los mejores.

        # 2. Ordenar los países por puntos
        paises_ordenados = sorted(
            paises_por_posicion, 
            key=lambda pais: pais.get('puntos', 0), # Usar .get para seguridad, 0 si no hay puntos
            reverse=True
        )

        # Clasificar y eliminar
        lista_destino.extend(paises_ordenados[:num_clasificados])
        eliminados.extend(paises_ordenados[num_clasificados:])
    
    # Manejo del error en el código original: 
    # Asegurarse de que los otros países en el grupo (los que están por debajo de 
    # la posición analizada) también se marquen como eliminados si es necesario.
    # Esta lógica es específica y debe ser revisada según el caso de uso real de su programa.
    # Por ejemplo, para UEFA (posicion_idx=2), los que estén en la posición 3 en adelante 
    # (índice 3 en adelante) deberían ser eliminados.
    if config:
        idx_restantes_eliminados = config['posicion_idx'] + 1
        for lista_paises in grupos_data.values():
            if len(lista_paises) > idx_restantes_eliminados:
                eliminados.extend(lista_paises[idx_restantes_eliminados:])


    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados