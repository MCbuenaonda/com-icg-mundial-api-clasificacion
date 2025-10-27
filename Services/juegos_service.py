from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 

def create_juegos(juegos, logger):
    try:
        logger.info(f"Creando nuevos Juegos")
        collection = db['juegos']
        # Inserta el nuevo documento en la colección
        resultado = collection.insert_many(juegos)        
        logger.info(f"Juegos creados exitosamente")
        return True
    except GoogleAPIError as e:
        logger.error(f"Error de Mongo DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al crear el juego: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al crear el juego: {str(e)}")

def get_juegos_por_estado(estado, logger):
    try:
        logger.info(f"Consultando juegos con estado {estado}")
        collection = db['juegos']
        # Pipeline de agregación
        pipeline = [
            {'$match': {'estado': estado}},
            # Agregar campo temporal para extraer el número de jornada
            {
                '$addFields': {
                    'jornada_numero': {
                        '$toInt': {
                            '$arrayElemAt': [
                                {'$split': ['$jornada', ' ']}, 1
                            ]
                        }
                    }
                }
            },
            # Ordenar por número de jornada y luego por fecha_hora_str
            {'$sort': {
                'jornada_numero': 1,
                'fecha_hora_str': 1
            }},
            # Remover el campo temporal
            {
                '$project': {
                    'jornada_numero': 0
                }
            }
        ]
        
        # Ejecutar la consulta
        juegos = collection.aggregate(pipeline)
        # Convertir el cursor a una lista
        juegos = list(juegos)
        return juegos
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener los juegos: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener los juegos: {str(e)}")

def get_ultimo_juego_confederacion(confederacion_id, logger):
    """
    Obtiene el último juego de una confederación específica ordenado por fecha
    
    Args:
        confederacion_id: ID de la confederación
        logger: Logger para registrar información
    
    Returns:
        dict: Último juego de la confederación o None si no se encuentra
    """
    try:
        logger.info(f"Consultando último juego de la confederación {confederacion_id}")
        collection = db['juegos']
        
        # Buscar el último juego de la confederación ordenado por fecha descendente
        ultimo_juego = collection.find_one(
            {'confederacion_id': confederacion_id, 'fecha': {'$exists': True, '$ne': None}},
            sort=[('fecha', -1)]  # Ordenar por fecha descendente
        )
        
        if ultimo_juego:
            logger.info(f"Último juego encontrado: {ultimo_juego.get('fecha')} - {ultimo_juego.get('tag', 'Sin tag')}")
            # Convertir ObjectId a string si existe
            if '_id' in ultimo_juego:
                ultimo_juego['_id'] = str(ultimo_juego['_id'])
            return ultimo_juego
        else:
            logger.info(f"No se encontraron juegos para la confederación {confederacion_id}")
            return None
            
    except GoogleAPIError as e:
        logger.error(f"Error de MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoDB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el último juego de la confederación: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el último juego de la confederación: {str(e)}")