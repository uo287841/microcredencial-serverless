import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('Orders-UO287841')
events_client = boto3.client('events', region_name='eu-north-1')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'content-type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
}

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj)
    raise TypeError

def lambda_handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', '')
    path = event.get('rawPath', '')

    # Responder a preflight OPTIONS
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': CORS_HEADERS, 'body': ''}

    # POST /orders — crear pedido
    if method == 'POST' and path == '/orders':
        body = json.loads(event.get('body', '{}'))
        order_id = str(uuid.uuid4())

        order = {
            'Id': order_id,
            'status': 'PENDING',
            'createdAt': datetime.utcnow().isoformat(),
            'product': body.get('product', 'unknown'),
            'quantity': body.get('quantity', 1)
        }

        table.put_item(Item=order)

        events_client.put_events(
            Entries=[{
                'Source': 'tienda-online',
                'DetailType': 'order-created',
                'Detail': json.dumps({'id': order_id}),
                'EventBusName': 'default'
            }]
        )

        return {
            'statusCode': 201,
            'headers': CORS_HEADERS,
            'body': json.dumps({'id': order_id, 'status': 'PENDING'})
        }

    # GET /orders/{id} — consultar estado
    if method == 'GET':
        # Usar pathParameters (robusto) con fallback a rawPath
        path_params = event.get('pathParameters') or {}
        order_id = path_params.get('id') or path.split('/orders/')[-1]

        print(f"Buscando pedido con Id: {order_id}")

        response = table.get_item(Key={'Id': order_id})
        item = response.get('Item')

        if not item:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Pedido no encontrado'})
            }

        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps(item, default=decimal_default)
        }

    return {
        'statusCode': 400,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Bad request'})
    }