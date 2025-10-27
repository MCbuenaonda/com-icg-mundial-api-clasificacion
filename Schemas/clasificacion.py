from pydantic import BaseModel
from typing import Optional, List
from Schemas.pais import Pais

class Clasificacion(BaseModel):
    mundial_id: Optional[int]
    grupo: Optional[str]
    confederacion_id: Optional[int]
    fase_id: Optional[int]
    paises: Optional[List[Pais]]