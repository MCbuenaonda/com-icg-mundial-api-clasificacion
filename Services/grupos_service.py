from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 
collection = db['grupos']

def get_grupo(query, logger):
    try: 
        result = collection.find_one(query)
        return result
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el grupo: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el grupo: {str(e)}")

def create_grupos(grupos_data, logger):
    try:
        logger.info(f"Creando nuevos Grupos")
        # Inserta el nuevo documento en la colección
        resultado = collection.insert_one(grupos_data)
        grupos_data['_id'] = str(resultado.inserted_id)
        logger.info(f"Grupo creado exitosamente con ID: {resultado.inserted_id}")
        return {"_id": str(resultado.inserted_id), **grupos_data}
    except GoogleAPIError as e:
        logger.error(f"Error de Mongo DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al crear el grupo: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al crear el grupo: {str(e)}")