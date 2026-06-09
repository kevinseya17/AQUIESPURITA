import json
from application.use_cases import AuthUseCase
from adapters.in_memory_repository import InMemoryUserRepository

# 1. Configuración de dependencias (Inyección de Dependencias)
# Elegimos qué base de datos usar y se la pasamos al caso de uso.
db_adapter = InMemoryUserRepository()
auth_service = AuthUseCase(repository=db_adapter)

def lambda_handler(event, context):
    """
    ENDPOINT SERVERLESS (AWS Lambda, Azure Function, etc)
    Esta función es el único punto de entrada para la nube.
    Recibe un evento (ej. una petición HTTP desde el API Gateway).
    """
    try:
        # Simulamos que leemos el body que envía el API Gateway
        body = json.loads(event.get("body", "{}"))
        username = body.get("username")
        password = body.get("password")
        
        # Llamamos a nuestro caso de uso
        success, message_or_token = auth_service.login(username, password)
        
        if success:
            return {
                "statusCode": 200,
                "body": json.dumps({"status": "success", "token": message_or_token})
            }
        else:
            return {
                "statusCode": 401,
                "body": json.dumps({"status": "error", "message": message_or_token})
            }
            
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message": str(e)})
        }
