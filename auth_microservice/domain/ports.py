from abc import ABC, abstractmethod
from typing import Optional
from .entities import User

class UserRepositoryPort(ABC):
    """
    PUERTO (Port): Esta es la interfaz que define cómo el dominio
    se comunica con el exterior (Base de datos) sin saber qué base
    de datos se está usando.
    """
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        pass
    
    @abstractmethod
    def save_user(self, user: User) -> None:
        pass
