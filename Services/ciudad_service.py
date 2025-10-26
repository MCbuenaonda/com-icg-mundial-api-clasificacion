from fastapi import HTTPException
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client['mundial'] 

def get_ciudad_anfitrion(pais_id, logger):
    try:        
        collection = db['ciudades']
        # Pipeline de agregación
        pipeline = [
            {'$match': {'pais_id': pais_id}},
            {'$sample': {'size': 1}},
            {
                '$project': {
                    '_id': 0  # 0 significa EXCLUIR el campo _id
                }
            }
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