from pydantic import BaseModel
from typing import Optional, List
from Schemas.pais import Pais

class Mundial(BaseModel):
    _id: Optional[str]    
    pais_id: Optional[int]
    anio: Optional[int]
    campeon: Optional[int]    
    activo: Optional[bool]
    botin: Optional[int]
    por: Optional[int]
    dfi: Optional[int]
    dfd: Optional[int]
    li: Optional[int]
    ld: Optional[int]
    mi: Optional[int]
    mc: Optional[int]
    md: Optional[int]
    ei: Optional[int]
    dc: Optional[int]
    ed: Optional[int]
    pais: Optional[Pais]