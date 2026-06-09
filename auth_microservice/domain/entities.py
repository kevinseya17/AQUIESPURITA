from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    is_active: bool = True

    def verify_password(self, password_input: str) -> bool:
        """
        En un entorno real, aquí usaríamos una librería como passlib o bcrypt.
        Para mantener el microservicio sin dependencias complejas por ahora,
        simularemos la validación.
        """
        # TODO: Implementar hash real
        return self.password_hash == password_input
