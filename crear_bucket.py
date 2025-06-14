import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Handler para el endpoint POST /s3/crear-bucket.
    Acepta un JSON en el body con la forma:
      { "bucket": "nombre-del-bucket" }
    Maneja los casos en que API Gateway entregue event["body"] como string JSON
    o como un dict Python ya parseado.
    """

    # --- DEBUG: imprimir el evento completo para inspeccionar en CloudWatch Logs ---
    print("DEBUG ── event completo:")
    print(json.dumps(event))

    # Extraer raw_body: puede venir como dict (si API Gateway ya lo parseó)
    # o como string JSON. Si no existe, raw_body = None.
    raw_body = event.get("body", None)

    # Determinar si ya está parseado (dict) o es string
    if isinstance(raw_body, dict):
        body = raw_body
    else:
        # raw_body es un string (JSON) o None
        try:
            body = json.loads(raw_body or "{}")
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"JSON inválido en el body: {str(e)}"
                })
            }

    # Verificar que tengamos el parámetro "bucket" en el body
    bucket_name = body.get("bucket")
    if not bucket_name:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Falta parámetro 'bucket' en el body"
            })
        }

    # Intentar crear el bucket en S3
    try:
        s3.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        # Si el bucket ya existe o lo posee este mismo usuario
        if error_code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            return {
                "statusCode": 409,
                "body": json.dumps({
                    "error": f"El bucket '{bucket_name}' ya existe"
                })
            }
        # Otro error de AWS S3
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": str(e)
            })
        }

    # Si llegamos aquí, el bucket se creó correctamente
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Bucket '{bucket_name}' creado correctamente"
        })
    }
