from auth_microservice.handler import lambda_handler
import json

def run_test():
    print("--- PRUEBA DEL MICROSERVICIO SERVERLESS ---")
    
    # Simulamos lo que enviaría el API Gateway para un login exitoso
    evento_exito = {
        "body": json.dumps({
            "username": "profesor",
            "password": "secreta123"
        })
    }
    
    print("\nIntento 1 (Credenciales correctas):")
    respuesta = lambda_handler(evento_exito, None)
    print("Código HTTP:", respuesta["statusCode"])
    print("Respuesta:", respuesta["body"])

    # Simulamos un login fallido
    evento_fallo = {
        "body": json.dumps({
            "username": "profesor",
            "password": "password_incorrecta"
        })
    }
    
    print("\nIntento 2 (Contraseña incorrecta):")
    respuesta2 = lambda_handler(evento_fallo, None)
    print("Código HTTP:", respuesta2["statusCode"])
    print("Respuesta:", respuesta2["body"])

if __name__ == "__main__":
    run_test()
