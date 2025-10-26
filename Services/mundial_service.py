from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 

def get_mundiales_list(logger):
    try:        
        logger.info(f"Consultando lista de Mundiales")
        collection = db['mundiales']
        docs = collection.find()
        return [doc for doc in docs]        
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el mundial: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el mundial: {str(e)}")

def get_mundial_activo(logger):
    try:        
        logger.info(f"Consultando datos de Mundial Activo")
        collection = db['mundiales']
        
        # Definir la etapa de filtro dentro del pipeline
        match_stage = {"$match": {"activo": True}}

        # Pipeline de agregación completo
        pipeline = [
            match_stage, # La primera etapa filtra por el campo 'activo'
            {
                "$lookup": {
                    "from": "paises",
                    "localField": "pais_id",
                    "foreignField": "id",
                    "as": "pais"
                }
            },
            {
                "$unwind": "$pais"
            }
        ]

        resultados = collection.aggregate(pipeline)
        
        # Obtener el primer (y único) resultado del cursor
        mundial_activo = next(resultados, None)
        
        if not mundial_activo:
            logger.warning(f"No se encontraron mundiales activos.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron mundiales activos.")
        else:
            mundial_activo['_id'] = str(mundial_activo['_id'])
            mundial_activo['pais']['_id'] = str(mundial_activo['pais']['_id'])

        return mundial_activo
    except GoogleAPIError as e:
        logger.error(f"Error de Mongo DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al obtener el mundial: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener el mundial: {str(e)}")


def create_mundial_service(mundial_data, logger):
    try:
        logger.info(f"Creando nuevo Mundial")
        collection = db['mundiales']
        # Inserta el nuevo documento en la colección
        resultado = collection.insert_one(mundial_data)
        mundial_data['_id'] = str(resultado.inserted_id)
        logger.info(f"Mundial creado exitosamente con ID: {resultado.inserted_id}")
        return {"_id": str(resultado.inserted_id), **mundial_data}
    except GoogleAPIError as e:
        logger.error(f"Error de Mongo DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
    except Exception as e:
        logger.error(f"Error al crear el mundial: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al crear el mundial: {str(e)}")