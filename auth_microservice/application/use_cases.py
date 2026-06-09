from typing import Dict, Any, Tuple
from domain.ports import UserRepositoryPort

class AuthUseCase:
    """
    CASO DE USO (Lógica del Negocio): Aquí es donde ocurre la magia.
    Solo se comunica con los 'puertos', no sabe qué base de datos se usa.
    Esto cumple el requisito de "Aislado" y "Una sola función" (Autenticar).
    """
    def __init__(self, repository: UserRepositoryPort):
        self.repository = repository
        
    def login(self, username: str, password_input: str) -> Tuple[bool, str]:
        """
        Intenta iniciar sesión.
        Retorna (Éxito, Mensaje_o_Token)
        """
        if not username or not password_input:
            return False, "Faltan credenciales"
            
        user = self.repository.get_user_by_username(username)
        if not user:
            return False, "Usuario no encontrado"
            
        if not user.verify_password(password_input):
            return False, "Contraseña incorrecta"
            
        # Si todo es correcto, en un entorno real generaríamos un JWT token.
        fake_token = f"jwt_token_for_{user.username}"
        return True, fake_token
