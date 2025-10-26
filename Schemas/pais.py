from pydantic import BaseModel
from typing import Optional, List

class Pais(BaseModel):
    _id: Optional[str]    
    id: Optional[int]
    nombre: Optional[str]
    siglas: Optional[str]
    iso: Optional[str]
    rankin: Optional[int]
    puntos: Optional[int]
    jj: Optional[int]
    jg: Optional[int]
    je: Optional[int]
    jp: Optional[int]
    gf: Optional[int]
    gc: Optional[int]
    lat: Optional[float]
    lng: Optional[float]
    federacion: Optional[str]
    confederacion_id: Optional[int]
    valor: Optional[int]
    p_ofensiva: Optional[int]
    p_defensiva: Optional[int]
    p_posesion: Optional[int]
    tactica_id: Optional[int]
    poder: Optional[int]
    efectividad_gol: Optional[float]
    promedio_gol: Optional[float]
    user_id: Optional[int]

		