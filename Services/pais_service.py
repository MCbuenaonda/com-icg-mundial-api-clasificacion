from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 
collection = db['paises']

def update_pais(query, values, logger):
    try:        
        result = collection.update_one(query, values)
        return result
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al actualizar el estado del pais: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al actualizar el estado del pais: {str(e)}")

def get_paises(confederacion_id, estado, logger):
    try:        
        # logger.info(f"Consultando pais anfitrion de la confederacion {confederacion_id}")
        collection = db['paises']
        # Pipeline de agregación
        pipeline = [
            {'$match': {'confederacion_id': confederacion_id, 'estado': estado}},
        ]
        
        # Ejecutar la consulta
        paises = collection.aggregate(pipeline)
        # Convertir el cursor a una lista
        paises = list(paises)
        return paises
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el pais: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el pais: {str(e)}")
