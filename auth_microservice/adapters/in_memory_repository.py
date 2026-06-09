from typing import Optional
from domain.entities import User
from domain.ports import UserRepositoryPort

class InMemoryUserRepository(UserRepositoryPort):
    """
    ADAPTADOR (Adapter): Esta clase "adapta" la base de datos a nuestro puerto.
    Para este ejemplo inicial y que sea fácil de probar sin instalar nada,
    usaremos un diccionario en memoria.
    Luego podemos cambiar esto a `SqliteUserRepository` para leer `db.sqlite3`
    sin tocar ni una línea de la lógica de negocio.
    """
    def __init__(self):
        # Simulamos una base de datos con un usuario de prueba
        self.db = {
            "profesor": User(
                id=1,
                username="profesor",
                email="profe@escuela.com",
                password_hash="secreta123" # En la vida real esto estaría encriptado
            )
        }
        
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.get(username)
        
    def save_user(self, user: User) -> None:
        self.db[user.username] = user
