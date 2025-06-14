import json
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Handler para el endpoint POST /s3/crear-directorio.
    Acepta un JSON en el body con la forma:
      { "bucket": "nombre-del-bucket", "directorio": "ruta/carpeta" }
    Maneja los casos en que API Gateway entregue event["body"] como string JSON
    o como un dict Python ya parseado.
    """

    print("DEBUG ── event completo:")
    print(json.dumps(event))

    raw_body = event.get("body", None)

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

    bucket_name = body.get("bucket")
    directorio = body.get("directorio")

    if not bucket_name or not directorio:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Faltan parámetros 'bucket' o 'directorio' en el body"
            })
        }

    if not directorio.endswith("/"):
        directorio += "/"

    key_placeholder = directorio + "_placeholder"

    try:
        s3.put_object(Bucket=bucket_name, Key=key_placeholder, Body=b"")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": f"El bucket '{bucket_name}' no existe"
                })
            }
        # Otro error genérico de AWS S3
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": str(e)
            })
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Directorio '{directorio}' creado exitosamente en el bucket '{bucket_name}'"
        })
    }
