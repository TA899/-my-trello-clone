from flask import Blueprint, request, jsonify
import jwt  
from .models import Column, db , Card
import requests
import os

routes_blueprint = Blueprint('routes', __name__)


NGROK_URL = os.getenv('NGROK_API_URL')


# Funcion para obtener el user_id del token jwt
def get_user_id_from_token():
    token = request.headers.get('Authorization')
    
    if not token:
        return {'error': 'Authorization header is missing', 'status_code': 400}

    token = token.split(' ')[1] if ' ' in token else token
    secret_key = "your_secret_key"

    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_id = decoded.get('user_id')
        if not user_id:
            return {'error': 'User ID is missing from token payload', 'status_code': 400}
        return user_id
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired', 'status_code': 401}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token', 'status_code': 403}

# Funcion para obtener el user_id de la API de usuarios
def get_user_id_from_api():
    token = request.headers.get('Authorization')

    if not token:
        return None, {'error': 'Authorization header is missing', 'status_code': 400}

    token = token.split(' ')[1] if ' ' in token else token

    # URL del endpoint /me de la API de usuarios
    user_api_url = f"{NGROK_URL}/me"

    # Verificar el token con la API de usuarios
    headers = {
        'Authorization': f'Bearer {token}',
        'ngrok-skip-browser-warning': 'true'  # Este encabezado omite la advertencia de ngrok
    }
    response = requests.get(user_api_url, headers=headers)

    if response.status_code != 200:
        return None, {'error': 'Unauthorized, invalid or expired token', 'status_code': 401}

    user_info = response.json()
    user_id = user_info.get('id')

    if not user_id:
        return None, {'error': 'User ID is missing from user API response', 'status_code': 400}

    return user_id, None  # Retorna el user_id y None si no hay errores

# CREAR COLUMNA
@routes_blueprint.route('/columns', methods=['POST'])
def create_column():
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 422

    print("Datos recibidos:", data)
    column_name = data.get('name')

    # Obtener el user_id usando la función que verifica el token contra la API
    user_id, error_response = get_user_id_from_api()
    if error_response:
        return jsonify(error_response), error_response.get('status_code', 400)

    if not column_name:
        return jsonify({'error': 'Column name is required'}), 400

    existing_column = Column.query.filter_by(name=column_name, user_id=user_id).first()
    if existing_column:
        return jsonify({'error': 'A column with this name already exists for this user'}), 409

    column_count = Column.query.filter_by(user_id=user_id).count()
    if column_count >= 10:
        return jsonify({'error': 'Cannot create more than 10 columns for this user'}), 400

    new_column = Column(name=column_name, user_id=user_id)
    db.session.add(new_column)
    db.session.commit()
    return jsonify(new_column.to_dict()), 201


# EDITAR COLUMNA
@routes_blueprint.route('/columns/<int:column_id>', methods=['PUT'])
def edit_column(column_id):
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 422

    print("Datos recibidos:", data)
    new_column_name = data.get('name')

    user_id_response = get_user_id_from_token()
    if isinstance(user_id_response, dict):  # Verifica si la respuesta es un error
        return jsonify(user_id_response), user_id_response.get('status', 400)

    user_id = user_id_response

    if not new_column_name:
        return jsonify({'error': 'New column name is required'}), 400

    # Verifica si la columna existe y pertenece al usuario
    column = Column.query.filter_by(column_id=column_id, user_id=user_id).first()
    if not column:
        return jsonify({'error': 'Column not found or you do not have permission to edit it'}), 403

    # Verifica si el nuevo nombre ya existe en otra columna del mismo usuario
    existing_column = Column.query.filter_by(name=new_column_name, user_id=user_id).first()
    if existing_column and existing_column.column_id != column_id:
        return jsonify({'error': 'A column with this name already exists for this user'}), 409

    # Actualiza el nombre de la columna
    column.name = new_column_name
    db.session.commit()
    
    return jsonify(column.to_dict()), 200

# OBTENER TODAS LAS COLUMNAS O FILTRAR POR NOMBRE DE LA COLUMNA
@routes_blueprint.route('/columns', methods=['GET'])
def get_columns():
    user_id_response = get_user_id_from_token()
    if isinstance(user_id_response, dict):  # Verifica si la respuesta es un error
        return jsonify(user_id_response), user_id_response.get('status', 400)

    user_id = user_id_response

    # Obtener el parámetro de consulta 'name' si existe
    name = request.args.get('name')

    if name:
        # Filtrar las columnas del usuario por el nombre (búsqueda parcial e insensible a mayúsculas)
        columns = Column.query.filter(
            Column.user_id == user_id,
            Column.name.ilike(f'%{name}%')
        ).all()
    else:
        # Si no se pasa ningún parámetro, devolver todas las columnas del usuario
        columns = Column.query.filter_by(user_id=user_id).all()

    # Convertir las columnas a una lista de diccionarios
    columns_list = [column.to_dict() for column in columns]
    return jsonify(columns_list), 200

# OBTENER UNA COLUMNA ESPECIFICA
@routes_blueprint.route('/columns/<int:column_id>', methods=['GET'])
def get_column(column_id):
    user_id_response = get_user_id_from_token()
    if isinstance(user_id_response, dict):  # Verifica si la respuesta es un error
        return jsonify(user_id_response), user_id_response.get('status', 400)

    user_id = user_id_response

    # Obtener la columna específica del usuario
    column = Column.query.filter_by(column_id=column_id, user_id=user_id).first()

    if not column:
        return jsonify({'error': 'Column not found or access is forbidden'}), 403

    # Convertir la columna a un diccionario y devolverla como JSON
    return jsonify(column.to_dict()), 200

# ELIMINAR COLUMNA
@routes_blueprint.route('/columns/<int:column_id>', methods=['DELETE'])
def delete_column(column_id):
    user_id_response = get_user_id_from_token()
    if isinstance(user_id_response, dict):  # Verifica si la respuesta es un error
        return jsonify(user_id_response), user_id_response.get('status', 400)

    user_id = user_id_response

    # Buscar la columna y verificar que pertenece al usuario autenticado
    column = Column.query.filter_by(column_id=column_id, user_id=user_id).first()

    if not column:
        return jsonify({'error': 'Column not found or you do not have permission to delete it'}), 403

    # Eliminar la columna
    db.session.delete(column)
    db.session.commit()
    return jsonify({'message': 'Column deleted successfully'}), 200



# TARJETAS


# CREAR UNA TARJETA
@routes_blueprint.route('/columns/<int:column_id>/cards', methods=['POST'])
def create_card(column_id):
    data = request.get_json(silent=True)
    
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 422

    # Verificar que se proporcione el ID de la columna
    if not column_id:
        return jsonify({'error': 'Column ID is required'}), 404

    # Obtener el user_id usando la función que verifica el token contra la API
    user_id, error_response = get_user_id_from_api()
    if error_response:
        return jsonify(error_response), error_response.get('status_code', 400)

    # Verificar que la columna existe y que pertenece al usuario
    column = Column.query.filter_by(column_id=column_id, user_id=user_id).first()
    if not column:
        return jsonify({'error': 'Column not found or you do not have permission to add a card to it'}), 403

    # Validar título de la tarjeta
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Title is required'}), 400

    description = data.get('description', '')

    # Verificar si ya existe una tarjeta con el mismo título en la misma columna
    existing_card = Card.query.filter_by(title=title, column_id=column_id).first()
    if existing_card:
        return jsonify({'error': 'A card with this title already exists in this column'}), 409

    # Verificar que no haya más de 10 tarjetas en la columna
    card_count = Card.query.filter_by(column_id=column_id).count()
    if card_count >= 10:
        return jsonify({'error': 'Cannot create more than 10 cards in this column'}), 400

    # Crear la tarjeta
    new_card = Card(title=title, description=description, column_id=column_id, user_id=user_id)
    db.session.add(new_card)
    db.session.commit()
    return jsonify(new_card.to_dict()), 201


# OBTENER TODAS LAS TARJETAS O FILTRAR POR TÍTULO
@routes_blueprint.route('/columns/<int:column_id>/cards', methods=['GET'])
def get_cards(column_id):
    user_id = get_user_id_from_token()
    if isinstance(user_id, tuple):  # Verificar si se devolvió un error
        return user_id

    # Obtener el parámetro de búsqueda 'title' si existe
    title = request.args.get('title')

    # Si se proporciona un título, buscar todas las tarjetas en la columna que coincidan y que sean del usuario
    if title:
        cards = Card.query.filter(
            Card.title.ilike(f"%{title}%"),
            Card.user_id == user_id,
            Card.column_id == column_id  # Filtrar por column_id
        ).all()
        if not cards:
            return jsonify({'error': 'No cards found in this column matching the title'}), 404
        return jsonify([card.to_dict() for card in cards]), 200

    # Si no se proporciona título, devolver todas las tarjetas de la columna para el usuario
    cards = Card.query.filter_by(user_id=user_id, column_id=column_id).all()  # Filtrar por column_id
    if not cards:
        return jsonify({'error': 'No cards found in this column'}), 404

    return jsonify([card.to_dict() for card in cards]), 200


# TRAER CARTA ESPECIFICA DE UNA COLUMNA
@routes_blueprint.route('/columns/<int:column_id>/cards/<int:card_id>', methods=['GET'])
def get_specific_card(column_id, card_id):
    user_id = get_user_id_from_token()
    if isinstance(user_id, tuple):  # Verificar si se devolvió un error
        return user_id

    # Buscar la columna
    column = Column.query.filter_by(column_id=column_id).first()
    if not column:
        return jsonify({'error': 'Column not found'}), 404

    # Buscar la carta específica que pertenezca a la columna
    card = Card.query.filter_by(card_id=card_id, column_id=column_id).first()

    if not card:
        return jsonify({'error': 'Card not found in this column'}), 404  # Error si la tarjeta no existe en la columna

    if card.user_id != user_id:
        return jsonify({'error': 'You do not have permission to view this card'}), 403  # Error si no pertenece al usuario

    # Devolver la carta en formato JSON
    return jsonify(card.to_dict()), 200


# ACTUALIZAR UNA TARJETA
@routes_blueprint.route('/columns/<int:column_id>/cards/<int:card_id>', methods=['PUT'])
def update_card(column_id, card_id):
    # Obtener los datos de la solicitud
    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    # Obtener el user_id usando la función que verifica el token
    user_id = get_user_id_from_token()
    if isinstance(user_id, dict):  # Verifica si la respuesta es un error
        return jsonify(user_id), user_id.get('status', 400)

    # Buscar la tarjeta para asegurarse de que pertenece al usuario
    card = Card.query.filter_by(card_id=card_id, column_id=column_id).first()
    if not card:
        return jsonify({'error': 'Card not found in this column'}), 404
    if card.user_id != user_id:
        return jsonify({'error': 'You do not have permission to edit this card'}), 403

    # Actualizar título y descripción de la tarjeta
    new_title = data.get('title')
    new_description = data.get('description')

    if new_title:
        # Validar que no haya duplicados de título en la nueva columna
        existing_card = Card.query.filter_by(title=new_title, column_id=column_id).first()
        if existing_card and existing_card.card_id != card_id:
            return jsonify({'error': 'A card with this title already exists in this column'}), 409
        card.title = new_title

    if new_description is not None:
        card.description = new_description

    # Cambiar la columna de la tarjeta (si está en los datos)
    new_column_id = data.get('column_id')
    if new_column_id and new_column_id != card.column_id:
        # Verificar que la columna nueva existe y pertenece al mismo usuario
        new_column = Column.query.filter_by(column_id=new_column_id, user_id=user_id).first()
        if not new_column:
            return jsonify({'error': 'The specified column does not exist or you do not have permission to access it'}), 403
        # Cambiar el column_id de la tarjeta
        card.column_id = new_column_id

    # Guardar los cambios en la base de datos
    db.session.commit()

    # Devolver la tarjeta actualizada como respuesta JSON
    return jsonify(card.to_dict()), 200



# ELIMINAR TARJETA DE UNA COLUMNA
@routes_blueprint.route('/columns/<int:column_id>/cards/<int:card_id>', methods=['DELETE'])
def delete_card(card_id,column_id):
    # Obtener y decodificar el token JWT del encabezado de autorización
    user_id = get_user_id_from_token()
    if isinstance(user_id, tuple):  # Verificar si se devolvió un error
        return user_id

    # Obtener la tarjeta por ID
    card = Card.query.get(card_id)
    if card is None:
        return jsonify({'error': 'Card not found'}), 404

    # Verificar que el user_id del token coincide con el user_id de la tarjeta
    if card.user_id != user_id:
        return jsonify({'error': 'You do not have permission to delete this card'}), 403

    # Eliminar la tarjeta
    db.session.delete(card)
    db.session.commit()

    return jsonify({'message': 'Card deleted successfully'}), 200














# ENDPOINT ADICIONAL PARA CHISTE


@routes_blueprint.route('/chiste', methods=['GET'])
def obtener_chiste():
    try:
        # Hacer una solicitud a la API de Chuck Norris
        response = requests.get('https://api.chucknorris.io/jokes/random')
        response.raise_for_status()  # Verificar si la solicitud fue exitosa
        response_data = response.json()  # Convertir la respuesta a JSON

        # Retornar el chiste en formato JSON
        return jsonify({
            'chiste': response_data['value']
        }), 200

    except requests.exceptions.RequestException as req_err:
        return jsonify({'error': f'Error en la solicitud externa: {str(req_err)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
