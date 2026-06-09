import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from handler import lambda_handler

class APIGatewayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Si entran desde el navegador, mostramos un formulario bonito para probar
        if 'login' in self.path:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
                <body style="font-family: Arial; padding: 50px; text-align: center;">
                    <h2>Prueba del Microservicio de Login (Version Cloud Serverless)</h2>
                    <form id="loginForm">
                        <input type="text" id="user" placeholder="Usuario" value="profesor"><br><br>
                        <input type="password" id="pass" placeholder="Contrasena" value="secreta123"><br><br>
                        <button type="button" onclick="login()">Iniciar Sesion (POST)</button>
                    </form>
                    <p id="resultado" style="color: blue;"></p>
                    <script>
                        function login() {
                            fetch('/api/ms-login', {
                                method: 'POST',
                                body: JSON.stringify({
                                    username: document.getElementById('user').value,
                                    password: document.getElementById('pass').value
                                })
                            })
                            .then(r => r.json())
                            .then(data => {
                                document.getElementById('resultado').innerText = "Respuesta del microservicio: " + JSON.stringify(data);
                            });
                        }
                    </script>
                </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

    def do_POST(self):
        # Permitir solo acceso al endpoint de login
        if 'login' in self.path:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Simulamos el evento que enviaría el API Gateway a AWS Lambda
            event = {
                "body": post_data,
                "path": self.path,
                "httpMethod": "POST"
            }
            
            # Llamamos a nuestro microservicio aislado
            respuesta_microservicio = lambda_handler(event, None)
            
            # Devolvemos la respuesta al cliente (ej. Postman o el navegador)
            self.send_response(respuesta_microservicio["statusCode"])
            self.send_header('Content-type', 'application/json')
            # Solucionar problemas de CORS si se conecta con un frontend
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(respuesta_microservicio["body"].encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Endpoint no encontrado en el API Gateway')

# Exportar handler para que Vercel lo detecte como Serverless Function
handler = APIGatewayHandler

def run(server_class=HTTPServer, handler_class=APIGatewayHandler, port=8001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"[*] API Gateway Local iniciado en el puerto {port}...")
    print(f"[*] Microservicio de Autenticacion disponible en: http://localhost:{port}/api/ms-login")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("[*] API Gateway detenido.")

if __name__ == '__main__':
    run()
