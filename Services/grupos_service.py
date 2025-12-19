from bson import ObjectId
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

def get_catalogo_jornadas(num_equipos, logger):
    try:
        logger.info(f"Obtieniendo el catálogo de jornadas para {num_equipos} equipos")
        
        collection = db['dos_equipos']
        if num_equipos == 2:
            collection = db['dos_equipos']
        elif num_equipos == 3:
            collection = db['tres_equipos']
        elif num_equipos == 4:
            collection = db['cuatro_equipos']
        elif num_equipos == 5:
            collection = db['cinco_equipos']
        elif num_equipos == 6:
            collection = db['seis_equipos']
        elif num_equipos == 8:
            collection = db['ocho_equipos']
        elif num_equipos == 10:
            collection = db['diez_equipos']
        else:
            logger.error(f"Número de equipos no soportado: {num_equipos}")
        
        # Inserta el nuevo documento en la colección
        resultado = collection.find()
        resultado = convertir_objectid_a_string(list(resultado))
        return resultado
    except GoogleAPIError as e:
        logger.error(f"Error de Mongo DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener catálogo de jornadas: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener catálogo de jornadas: {str(e)}")

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