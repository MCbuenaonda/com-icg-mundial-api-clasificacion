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