"""
Rate limiter compartido por toda la aplicación.

Vivía en main.py, pero lo movemos aquí para evitar importaciones
circulares: chat.py → main.py → router → chat.py.

Cualquier endpoint que necesite rate limiting importa el limiter
desde aquí, y main.py también lo registra en la app desde aquí.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# La clave es la IP del cliente, no el user_id, para poder limitar
# incluso requests sin autenticar (ej. intentos de login masivos).
limiter = Limiter(key_func=get_remote_address)
