# documentos/utils/presign.py
# Presigned tokens locales (simple, seguro suficiente para dev)
# token = base64(payload_json) + "." + hexdigest(secret + payload)
import time
import json
import hashlib
import hmac
import base64
from django.conf import settings

# usa secret configurable: si no está, usa settings.SECRET_KEY
SECRET = getattr(settings, "PRESIGN_SECRET", settings.SECRET_KEY).encode()
PRESIGN_TTL = getattr(settings, "PRESIGN_TTL", 300)  # segundos

def _sign(payload_bytes):
    return hmac.new(SECRET, payload_bytes, hashlib.sha256).hexdigest()

def generate_presigned_token(file_path, mode):
    """
    file_path: ruta absoluta en disco donde se guardará/leerá el archivo.
    mode: 'upload' o 'download'
    devuelve token string
    """
    payload = {
        "file_path": str(file_path),
        "mode": mode,
        "exp": int(time.time()) + PRESIGN_TTL
    }
    raw = json.dumps(payload).encode()
    sig = _sign(raw)
    token = base64.urlsafe_b64encode(raw).decode() + "." + sig
    return token

def get_presign_meta(token):
    """
    devuelve dict {'file_path':..., 'mode':...} o None si inválido/expirado
    """
    try:
        raw_b64, sig = token.rsplit(".", 1)
        raw = base64.urlsafe_b64decode(raw_b64.encode())
        if not hmac.compare_digest(_sign(raw), sig):
            return None
        payload = json.loads(raw)
        if int(time.time()) > int(payload.get("exp", 0)):
            return None
        return payload
    except Exception:
        return None
