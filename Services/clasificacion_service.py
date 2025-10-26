from fastapi import HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from pymongo.mongo_client import MongoClient
from Config.settings import MONGODB_URI
from Utils import clasificacion_util

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
            collection = db['paises']

            query = {'nombre': pais.nombre}
            # Pipeline de actualización
            new_values ={'$set': {'estado': estado}}
            # Ejecutar la actualización
            result = collection.update_one(query, new_values)
        
        return True
    except GoogleAPIError as e:
        logger.error(f"Error de MongoBD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error de MongoBD: {str(e)}")
    except Exception as e:
        logger.error(f"Error al actualizar el estado del pais: {str(e)}")
        raise HTTPException(status_code=409, detail=f"Error al actualizar el estado del pais: {str(e)}")


def verifica_grupos_fase(confederacion_id: int, fase_id: int, logger):
    """
    Verifica el estatus de los grupos de la confederación y fase dadas,
    y actualiza la clasificación de los equipos si es necesario.
    """
    try:
        filtro_partidos_pendientes = {            
            "confederacion_id": confederacion_id,
            "fase_id": fase_id,
            "estado": "pendiente"
        }

        # Usar count_documents para contar sin iterar el cursor
        if db['juegos'].count_documents(filtro_partidos_pendientes) == 0:
            grupos_doc = db['grupos'].find_one({
                "confederacion_id": confederacion_id,
                "fase_id": fase_id
            })

            if fase_id == 1:
                if confederacion_id == 1:
                    clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados = clasificar_mejores_posicionados(grupos_doc, logger)
                    ajustar_estados(clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados)
                
            #crear_fase(confederacion_id fase):

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

    # Lógica para clasificar los países mejor posicionados
    if confederacion_id == 1:
        # UEFA
        if fase_id == 1:
            # Debe considerar los mejores terceros lugares
            paises_tercer_puesto = []
            grupos_data = grupos_doc.get('grupos', [])

            for nombre_grupo, lista_paises in grupos_data.items():
                # Comprobamos que el grupo tenga al menos 3 países para evitar un IndexError
                if len(lista_paises) >= 3:
                    pais_tercer_puesto = lista_paises[2]
                    paises_tercer_puesto.append(pais_tercer_puesto)
            
            # 2. Ordenar el array por puntos de mayor a menor
            # Utilizamos la función sorted() con una clave (key) lambda
            paises_ordenados = sorted(
                paises_tercer_puesto, 
                key=lambda pais: pais['puntos'], 
                reverse=True  # 'reverse=True' para ordenar de mayor a menor
            )

            clasificados_mundial.append(paises_ordenados[:4])  # Los 4 mejores terceros lugares van al mundial
            eliminados.append(paises_ordenados[4:]) # Los demás quedan eliminados
   
    return clasificados_mundial, clasificados_ronda, clasificados_repechaje, eliminados

# def create_grupos(grupos_data, logger):
#     try:
#         logger.info(f"Creando nuevos Grupos")
#         collection = db['grupos']
#         # Inserta el nuevo documento en la colección
#         resultado = collection.insert_one(grupos_data)
#         grupos_data['_id'] = str(resultado.inserted_id)
#         logger.info(f"Grupo creado exitosamente con ID: {resultado.inserted_id}")
#         return {"_id": str(resultado.inserted_id), **grupos_data}
#     except GoogleAPIError as e:
#         logger.error(f"Error de Mongo DB: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Error de Mongo DB: {str(e)}")
#     except Exception as e:
#         logger.error(f"Error al crear el grupo: {str(e)}")
#         raise HTTPException(status_code=409, detail=f"Error al crear el grupo: {str(e)}")