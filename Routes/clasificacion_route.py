from fastapi import APIRouter, HTTPException
from Config.settings import PREFIX_SERVER_PATH
from Services import clasificacion_service
from Schemas.clasificacion import Clasificacion
import logging
import uuid 

route = APIRouter(prefix=PREFIX_SERVER_PATH)
tag='Classificación'
process_uuid = uuid.uuid4()

logging.basicConfig(level=logging.INFO, format=f'%(asctime)s - %(levelname)s - {process_uuid} - %(message)s')
logger = logging.getLogger(__name__)


@route.post("/verifica-clasificacion/", tags=[tag])
def verifica_clasificacion(clasificacion: Clasificacion):
    """
    Endpoint para obtener el grupo activo, si no existe, crea uno nuevo.

    Returns:
        Datos del grupo activo o el nuevo grupo creado
    Raises:
        HTTPException: Si ocurre un error durante el proceso
    """
    try:
        logger.info(f"Inicio del proceso para clasificación del grupo {clasificacion.grupo}")
        response = clasificacion_service.verifica_clasificacion(clasificacion, logger)
        if response:
            clasificacion_service.verifica_grupos_fase(clasificacion.confederacion_id, clasificacion.fase_id, logger)
        return response
    except Exception as e:
        logger.error(f"Error al obtener grupo: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al obtener grupo: {str(e)}")

