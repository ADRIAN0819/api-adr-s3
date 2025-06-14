import json
import base64
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Handler para el endpoint POST /s3/subir-archivo.
    Espera un JSON en el body con la forma:
      {
        "bucket": "nombre-del-bucket",
        "directorio": "ruta/opcional/",        # puede omitirse o estar vacío
        "nombreArchivo": "imagen.png",
        "archivoBase64": "…cadena Base64…"
      }

    - Detecta si event["body"] viene como dict (ya parseado) o como string JSON.
    - Decodifica el campo "archivoBase64" a bytes.
    - Hace put_object a S3 usando esos bytes.
    - Devuelve JSON con message de éxito o error.
    """

    print("DEBUG ── event completo:")
    print(json.dumps(event))

    raw_body = event.get("body", None)

    if isinstance(raw_body, dict):
        body = raw_body
    else:
        try:
            body = json.loads(raw_body or "{}")
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"JSON inválido en el body: {str(e)}"
                })
            }

    bucket_name    = body.get("bucket")
    directorio     = body.get("directorio", "")       
    nombre_archivo = body.get("nombreArchivo")
    archivo_b64    = body.get("archivoBase64")

    if not bucket_name or not nombre_archivo or not archivo_b64:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Faltan parámetros: 'bucket', 'nombreArchivo' o 'archivoBase64'"
            })
        }

    if directorio and not directorio.endswith("/"):
        directorio += "/"

    try:
        contenido_bytes = base64.b64decode(archivo_b64)
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"Error al decodificar Base64: {str(e)}"
            })
        }

    key_final = f"{directorio}{nombre_archivo}"
    try:
        s3.put_object(
            Bucket=bucket_name,
            Key=key_final,
            Body=contenido_bytes,
            ContentType="image/png"   
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": f"El bucket '{bucket_name}' no existe"
                })
            }
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": f"Error al subir a S3: {str(e)}"
            })
        }

    # 7) Respuesta de éxito
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Imagen '{nombre_archivo}' subida correctamente a '{bucket_name}/{directorio}'"
        })
    }
