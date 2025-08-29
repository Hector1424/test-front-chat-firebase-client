# main.py — AUTOCONTENIDO (sin Firebase)
# Usuarios locales + referencias a chat_ids remotos (API Firebase)
# Sirve /test con tu HTML de prueba desacoplado
 
import json
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
 
 
 
import os
from dotenv import load_dotenv
# Instancia para la seguridad de Bearer Token
security = HTTPBearer()
# Carga las variables del archivo .env
load_dotenv()
# =================================
# Obtiene los valores del .env
# =================================
PROJECT_ID = os.getenv("PROJECT_ID")
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")  # Si quieres usar una variable para la URL base

app = FastAPI(title="Test Chat UI (autocontenido sin Firebase)")
# =========================
# "DB" en fichero JSON
# =========================
USERS_FILE = "users.json"


def load_users_from_disk() -> dict[str, dict]:
    """Carga los usuarios desde users.json. Si no existe, devuelve un dict vacío."""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users_to_disk():
    """Guarda el estado actual de USERS_STORE en users.json."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(USERS_STORE, f, indent=2, ensure_ascii=False)


USERS_STORE: dict[str, dict] = load_users_from_disk()


def norm_user(u: dict) -> dict:
    return {
        "uuid": u.get("uuid"),
        "name": u.get("name"),
        "chat_ids": list(u.get("chat_ids", [])),
    }

# =========================
# Schemas
# =========================
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    name: Optional[str] = None


# Modelo para la petición de login
class UserLogin(BaseModel):
    name: str
    password: str


# Modelo para la respuesta del usuario (sin datos sensibles)
class User(BaseModel):
    uuid: str
    name: str
    chat_ids: List[str]

# Modelo para la respuesta del login, incluyendo el token
class LoginResponse(BaseModel):
    token: str
    user: User


class AddChatRef(BaseModel):
    chat_id: str = Field(..., min_length=1)

# =========================
# Endpoints: Usuarios locales
# =========================
@app.get("/users", response_class=JSONResponse, tags=["users"])
def list_users():
    return [norm_user(u) for u in USERS_STORE.values()]


@app.post("/users", response_class=JSONResponse, tags=["users"])
def create_user(payload: UserCreate):
    user_id = str(uuid.uuid4())
    USERS_STORE[user_id] = {
        "uuid": user_id,
        "name": payload.name,
        "password": payload.password,
        "chat_ids": [],
    }
    save_users_to_disk()
    return {"ok": True, "user": norm_user(USERS_STORE[user_id])}


@app.get("/users/{user_uuid}", response_class=JSONResponse, tags=["users"])
def get_user(user_uuid: str):
    u = USERS_STORE.get(user_uuid)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    return norm_user(u)


@app.patch("/users/{user_uuid}", response_class=JSONResponse, tags=["users"])
def update_user(user_uuid: str, payload: UserUpdate):
    u = USERS_STORE.get(user_uuid)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    if payload.name is not None:
        u["name"] = payload.name
    save_users_to_disk()
    return {"ok": True, "user": norm_user(u)}


@app.delete("/users/{user_uuid}", response_class=JSONResponse, tags=["users"])
def delete_user(user_uuid: str):
    if user_uuid not in USERS_STORE:
        raise HTTPException(404, "Usuario no encontrado")
    del USERS_STORE[user_uuid]
    save_users_to_disk()
    return {"ok": True}


@app.post("/login", response_model=LoginResponse, tags=["auth"])
def login(payload: UserLogin):
    """
    Autentica a un usuario por nombre y contraseña (en texto plano).
    Si es exitoso, devuelve un token y los datos del usuario.
    """
    for u in USERS_STORE.values():
        # Búsqueda insensible a mayúsculas/minúsculas para el nombre
        if u["name"].lower() == payload.name.lower():
            # Comparación de contraseña sensible a mayúsculas/minúsculas
            if u.get("password") == payload.password:
                # En este sistema simple, el token es el UUID del usuario.
                return {"token": u["uuid"], "user": norm_user(u)}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nombre de usuario o contraseña incorrectos",
    )


@app.get("/me", response_model=User, tags=["auth"])
def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Valida un token (Bearer) y devuelve los datos del usuario correspondiente.
    """
    token = credentials.credentials
    # El token es el UUID del usuario.
    user = USERS_STORE.get(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return norm_user(user)
# =========================
# Endpoints: Referencias de chats por usuario
# =========================
@app.get("/users/{user_uuid}/chatRefs", response_class=JSONResponse, tags=["users"])
def list_user_chat_refs(user_uuid: str):
    u = USERS_STORE.get(user_uuid)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    return {"user_uuid": user_uuid, "chat_ids": list(u.get("chat_ids", []))}


@app.post("/users/{user_uuid}/chatRefs", response_class=JSONResponse, tags=["users"])
def add_user_chat_ref(user_uuid: str, payload: AddChatRef):
    u = USERS_STORE.get(user_uuid)
    if not u:
        raise HTTPException(404, "Usuario no encontrado")
    if payload.chat_id not in u["chat_ids"]:
        u["chat_ids"].append(payload.chat_id)
    save_users_to_disk()
    return {"ok": True, "user": norm_user(u)}

# Listado de todos los chat_ids locales (deduplicado)
@app.get("/local/chats", response_class=JSONResponse, tags=["users"])
def list_all_local_chat_refs():
    ids = set()
    for u in USERS_STORE.values():
        ids.update(u.get("chat_ids", []))
    return {"chat_ids": sorted(ids)}


# =========================
# HTML de prueba
# =========================
@app.get("/", response_class=HTMLResponse, tags=["frontend"])
def serve_test_html():
    """
    Sirve el HTML de prueba desde un fichero, inyectando:
      - API_BASE: URL del main Firebase
      - PROJECT_ID / API_KEY globales (para todos los usuarios)
      - USERS: los usuarios locales con name/uuid + chat_refs
    """
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            template_content = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="index.html no encontrado.")

    users_payload = [norm_user(u) for u in USERS_STORE.values()]

    # Inyecta las variables en el template
    # El `or ""` es para evitar errores si una variable de entorno no está definida
    html_content = (
        template_content.replace("{api_base}", json.dumps(API_BASE or "")[1:-1])
        .replace("{project_id}", json.dumps(PROJECT_ID or "")[1:-1])
        .replace("{api_key}", json.dumps(API_KEY or "")[1:-1])
        .replace("{users_json}", json.dumps(users_payload))
    )
    return HTMLResponse(content=html_content)
