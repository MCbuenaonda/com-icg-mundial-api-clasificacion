from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 

def get_anfitrion(confederacion_id, logger):
    try:        
        logger.info(f"Consultando pais anfitrion de la confederacion {confederacion_id}")
        collection = db['paises']
        # Pipeline de agregación
        pipeline = [
            {'$match': {'confederacion_id': confederacion_id}},
            {'$sample': {'size': 1}}
        ]
        
        # Ejecutar la consulta
        anfitrion = collection.aggregate(pipeline)
        # Convertir el cursor a una lista y obtener el primer (y único) documento
        anfitrion = list(anfitrion)[0]
        return anfitrion              
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el pais: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el pais: {str(e)}")

def get_paises(confederacion_id, logger):
    try:        
        # logger.info(f"Consultando pais anfitrion de la confederacion {confederacion_id}")
        collection = db['paises']
        # Pipeline de agregación
        pipeline = [
            {'$match': {'confederacion_id': confederacion_id}}
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
