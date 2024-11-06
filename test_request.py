import jwt
import datetime

# Clave secreta que usarás para firmar el token
SECRET_KEY = "057e84ab20b3fb4ed5e055d4db4e29a4118b6ff027df41c17c36cf7ead920a024156441f0a674e13c03013b4eb7abbec70ebcd4d8f19ce5d717ff22e10865eb7"

# Función para generar un token JWT
def generar_token(user_id):
    token = jwt.encode(
        {'sub': user_id, 'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

# Función para decodificar y verificar el token
def verificar_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return "El token ha expirado"
    except jwt.InvalidTokenError:
        return "Token inválido"

if __name__ == "__main__":
    # Genera un token para el usuario con ID 123
    token_generado = generar_token(123)
    print(f'Token generado: {token_generado}')

    # Verifica el token generado
    datos_decodificados = verificar_token(token_generado)
    print(f'Datos decodificados: {datos_decodificados}')
