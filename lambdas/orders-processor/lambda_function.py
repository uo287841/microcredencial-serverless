import json
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table = dynamodb.Table('Orders-UO287841')
sns_client = boto3.client('sns', region_name='eu-north-1')

SNS_TOPIC_ARN = 'arn:aws:sns:eu-north-1:430165813080:orders-notification-UO287841'

def lambda_handler(event, context):
    for record in event['Records']:
        body = json.loads(record['body'])
        order_id = body.get('id') or body.get('Id') or body.get('orderId')

        if not order_id:
            print(f"No id en el mensaje: {body}")
            continue

        # Actualizar estado en DynamoDB
        table.update_item(
            Key={'Id': order_id},
            UpdateExpression='SET #s = :status',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':status': 'COMPLETED'}
        )

        # Enviar email de confirmación
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f'Pedido {order_id} procesado',
            Message=f'Tu pedido {order_id} ha sido procesado y su estado es COMPLETED.'
        )

        print(f"Pedido {order_id} procesado correctamente.")

    return {'statusCode': 200}