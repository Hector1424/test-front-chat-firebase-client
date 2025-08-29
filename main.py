# main.py — AUTOCONTENIDO (sin Firebase)
# Usuarios locales + referencias a chat_ids remotos (API Firebase)
# Sirve /test con tu HTML de prueba desacoplado

import json
import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field



import os
from dotenv import load_dotenv

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


class UserLogin(BaseModel):
    name: str
    password: str


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


@app.post("/login", response_class=JSONResponse, tags=["auth"])
def login_user(payload: UserLogin):
    """
    Autentica a un usuario por nombre y contraseña (en texto plano).
    """
    for u in USERS_STORE.values():
        # Búsqueda insensible a mayúsculas/minúsculas para el nombre
        if u["name"].lower() == payload.name.lower():
            # Comparación de contraseña sensible a mayúsculas/minúsculas
            if u.get("password") == payload.password:
                return norm_user(u)  # Devuelve el usuario normalizado sin la contraseña
    
    raise HTTPException(status_code=401, detail="Nombre de usuario o contraseña incorrectos")

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

# # =========================
# # HTML de prueba /test
# # =========================
# TEST_HTML = r"""<!DOCTYPE html>
# <html lang="es">
# <head>
#   <meta charset="UTF-8">
#   <title>Chat de Prueba</title>
#   <meta name="viewport" content="width=device-width, initial-scale=1.0">
#   <style>
#     body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background-color: #f0f2f5; }
#     #app-container { display: flex; height: 100vh; width: 100vw; }
#     #login-container { width: 300px; margin: auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
#     #login-container h2 { margin-top: 0; }
#     #login-container select, #login-container button { width: 100%; padding: 10px; margin-top: 10px; box-sizing: border-box; border-radius: 5px; border: 1px solid #ccc;}
#     #login-container button { background-color: #0084ff; color: white; border: none; cursor: pointer; }
#     #chat-container { display: none; flex-grow: 1; display: flex; }
#     #left-panel { width: 30%; max-width: 350px; border-right: 1px solid #ddd; display: flex; flex-direction: column; background-color: white; }
#     #left-panel-header { padding: 15px; border-bottom: 1px solid #ddd; }
#     #left-panel-header h3 { margin: 0; font-size: 1.2em; }
#     #contacts-list { overflow-y: auto; flex-grow: 1; }
#     .contact-item { padding: 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0; font-size: 1.1em; }
#     .contact-item:hover { background-color: #f5f5f5; }
#     .contact-item.active { background-color: #e0e0e0; font-weight: bold; }
#     #right-panel { flex-grow: 1; display: flex; flex-direction: column; }
#     #chat-header { padding: 15px; border-bottom: 1px solid #ddd; background-color: #f5f5f5; font-weight: bold; font-size: 1.1em; }
#     #messages-container { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; }
#     .message { max-width: 70%; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
#     .message.sent { background-color: #0084ff; color: white; align-self: flex-end; }
#     .message.received { background-color: #e4e6eb; color: #050505; align-self: flex-start; }
#     #message-input-container { display: flex; padding: 10px; border-top: 1px solid #ddd; background-color: white; }
#     #message-input { flex-grow: 1; border: 1px solid #ccc; border-radius: 18px; padding: 10px 15px; font-size: 1em; }
#     #message-input:focus { outline: none; }
#     #message-input-container button { margin-left: 10px; border: none; background-color: #0084ff; color: white; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-size: 18px; flex-shrink: 0; }
#     #placeholder-right-panel { flex-grow: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #65676b; text-align: center; background-color: #f0f2f5; }
#   </style>
# </head>
# <body>

# <div id="app-container">
#   <div id="login-container">
#     <h2>Iniciar Sesión</h2>
#     <input type="text" id="username-input" placeholder="Nombre de usuario">
#     <input type="password" id="password-input" placeholder="Contraseña">
#     <button onclick="login()">Entrar</button>
#   </div>
  
#   <div id="chat-container">
#     <div id="left-panel">
#       <div id="left-panel-header">
#         <h3 id="current-user-name"></h3>
#       </div>
#       <div id="contacts-list"></div>
#     </div>
#     <div id="right-panel">
#       <div id="placeholder-right-panel">
#         <h2>Tu mensajero personal</h2>
#         <p>Selecciona un contacto para empezar a chatear.</p>
#       </div>
#       <div id="chat-window" style="display: none; flex-grow: 1; display: flex; flex-direction: column;">
#         <div id="chat-header"></div>
#         <div id="messages-container"></div>
#         <div id="message-input-container">
#           <input type="text" id="message-input" placeholder="Escribe un mensaje..." onkeydown="if(event.key === 'Enter') sendMessage()">
#           <button onclick="sendMessage()">➤</button>
#         </div>
#       </div>
#     </div>
#   </div>
# </div>

# <script>
#   const API_BASE = "{api_base}";
#   const PROJECT_ID = "{project_id}";
#   const API_KEY = "{api_key}";
#   const USERS = {users_json};

#   let loggedInUser = null;
#   let projectChats = [];
#   let activeChat = null;
#   let messagePollingInterval = null;

#   const loginContainer = document.getElementById('login-container');
#   const chatContainer = document.getElementById('chat-container');
#   const usernameInput = document.getElementById('username-input');
#   const passwordInput = document.getElementById('password-input');
#   const contactsList = document.getElementById('contacts-list');
#   const chatWindow = document.getElementById('chat-window');
#   const placeholderRightPanel = document.getElementById('placeholder-right-panel');
#   const chatHeader = document.getElementById('chat-header');
#   const messagesContainer = document.getElementById('messages-container');
#   const messageInput = document.getElementById('message-input');
#   const currentUserNameEl = document.getElementById('current-user-name');

#   function init() {
#     chatContainer.style.display = 'none';
#     loginContainer.style.display = 'flex';
#     usernameInput.focus();
#   }

#   async function login() {
#     const name = usernameInput.value.trim();
#     const password = passwordInput.value;

#     if (!name || !password) {
#       alert("Por favor, introduce nombre de usuario y contraseña.");
#       return;
#     }

#     try {
#       const response = await fetch('/login', {
#         method: 'POST',
#         headers: { 'Content-Type': 'application/json' },
#         body: JSON.stringify({ name, password })
#       });

#       if (!response.ok) throw new Error('Credenciales incorrectas');

#       loggedInUser = await response.json();
#       loginContainer.style.display = 'none';
#       chatContainer.style.display = 'flex';
#       currentUserNameEl.textContent = `Hola, ${loggedInUser.name}`;
#       await loadProjectChats();
#       populateContacts();
#     } catch (error) {
#       console.error("Error de login:", error);
#       alert("Login fallido. Revisa tu usuario y contraseña.");
#     }
#   }

#   function populateContacts() {
#     contactsList.innerHTML = '';
#     const otherUsers = USERS.filter(u => u.uuid !== loggedInUser.uuid);
#     otherUsers.forEach(user => {
#       const contactDiv = document.createElement('div');
#       contactDiv.className = 'contact-item';
#       contactDiv.textContent = user.name;
#       contactDiv.dataset.userId = user.uuid;
#       contactDiv.onclick = () => openChatWithUser(user);
#       contactsList.appendChild(contactDiv);
#     });
#   }

#   async function loadProjectChats() {
#     try {
#       const response = await fetch(`${API_BASE}/chats`, {
#         headers: { 'X-Project-Id': PROJECT_ID, 'X-Api-Key': API_KEY }
#       });
#       if (!response.ok) throw new Error('Fallo al cargar los chats');
#       projectChats = await response.json();
#     } catch (error) {
#       console.error("Error cargando los chats del proyecto:", error);
#       alert("No se pudieron cargar los chats remotos.");
#     }
#   }

#   async function openChatWithUser(contactUser) {
#     if (messagePollingInterval) clearInterval(messagePollingInterval);

#     document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
#     const sel = document.querySelector(`.contact-item[data-user-id='${contactUser.uuid}']`);
#     if (sel) sel.classList.add('active');

#     let chat = projectChats.find(c =>
#       c.type === 'direct' &&
#       c.users.length === 2 &&
#       c.users.includes(loggedInUser.uuid) &&
#       c.users.includes(contactUser.uuid)
#     );

#     if (!chat) {
#       try {
#         const response = await fetch(`${API_BASE}/chats/direct`, {
#           method: 'POST',
#           headers: {
#             'Content-Type': 'application/json',
#             'X-Project-Id': PROJECT_ID,
#             'X-Api-Key': API_KEY
#           },
#           body: JSON.stringify({ users: [loggedInUser.uuid, contactUser.uuid] })
#         });
#         if (!response.ok) throw new Error('Fallo al crear el chat remoto');
#         chat = await response.json();
#         projectChats.push(chat);

#         try {
#           await fetch(`/users/${loggedInUser.uuid}/chatRefs`, {
#             method: 'POST',
#             headers: { 'Content-Type': 'application/json' },
#             body: JSON.stringify({ chat_id: chat.id })
#           });
#           await fetch(`/users/${contactUser.uuid}/chatRefs`, {
#             method: 'POST',
#             headers: { 'Content-Type': 'application/json' },
#             body: JSON.stringify({ chat_id: chat.id })
#           });
#         } catch (e) { console.warn("No se pudo actualizar chat_ids locales:", e); }
#       } catch (error) {
#         console.error("Error creando el chat remoto:", error);
#         alert("No se pudo crear un nuevo chat remoto.");
#         return;
#       }
#     }

#     activeChat = chat;
#     placeholderRightPanel.style.display = 'none';
#     chatWindow.style.display = 'flex';
#     chatHeader.textContent = `Chat con ${contactUser.name}`;
#     messageInput.focus();

#     await loadMessages();
#     messagePollingInterval = setInterval(loadMessages, 3000);
#   }

#   async function loadMessages() {
#     if (!activeChat) return;
#     try {
#       const response = await fetch(`${API_BASE}/chats/${activeChat.id}/messages`, {
#         headers: { 'X-Project-Id': PROJECT_ID, 'X-Api-Key': API_KEY }
#       });
#       if (!response.ok) throw new Error('Fallo al cargar los mensajes');
#       const messages = await response.json();
#       renderMessages(messages);
#     } catch (error) {
#       console.error(`Error cargando mensajes para el chat ${activeChat.id}:`, error);
#     }
#   }

#   function renderMessages(messages) {
#     messagesContainer.innerHTML = '';
#     messages.forEach(msg => {
#       const messageDiv = document.createElement('div');
#       messageDiv.className = 'message';
#       messageDiv.classList.add(msg.sender_id === loggedInUser.uuid ? 'sent' : 'received');

#       const messageText = document.createElement('div');
#       messageText.textContent = msg.text;

#       const messageTimestamp = document.createElement('span');
#       const date = new Date(msg.timestamp);
#       messageTimestamp.textContent = date.toLocaleString();
#       messageTimestamp.style.fontSize = '0.7em';
#       messageTimestamp.style.display = 'block';
#       messageTimestamp.style.color = msg.sender_id === loggedInUser.uuid
#         ? 'rgba(255, 255, 255, 0.7)'
#         : 'rgba(0, 0, 0, 0.5)';

#       messageDiv.appendChild(messageText);
#       messageDiv.appendChild(messageTimestamp);
#       messagesContainer.appendChild(messageDiv);
#     });
#     messagesContainer.scrollTop = messagesContainer.scrollHeight;
#   }

#   async function sendMessage() {
#     const text = messageInput.value.trim();
#     if (!text || !activeChat) return;

#     try {
#       await fetch(`${API_BASE}/chats/${activeChat.id}/messages`, {
#         method: 'POST',
#         headers: {
#           'Content-Type': 'application/json',
#           'X-Project-Id': PROJECT_ID,
#           'X-Api-Key': API_KEY
#         },
#         body: JSON.stringify({ sender_id: loggedInUser.uuid, text })
#       });
#       messageInput.value = '';
#       await loadMessages();
#     } catch (error) {
#       console.error("Error enviando el mensaje:", error);
#       alert("No se pudo enviar el mensaje al servidor remoto.");
#     }
#   }

#   window.onload = init;
# </script>

# </body>
# </html>
# """



# =========================
# HTML de prueba /test
# =========================
TEST_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Chat de Prueba</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    /* --- Styles for Login and General Layout (Improved) --- */
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
        margin: 0; 
        /* A nice gradient for the background when login is visible */
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    #app-container { 
        display: flex; /* This allows margin:auto on children to work for centering */
        height: 100vh; 
        width: 100vw; 
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }

    #login-container { 
        width: 380px; 
        margin: auto; /* This centers the box in the flex container */
        padding: 40px; 
        background-color: white;
        border-radius: 12px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.15); 
        text-align: center; 
        animation: fadeIn 0.5s ease-in-out;
    }

    #login-container h2 { 
        margin-top: 0; 
        margin-bottom: 30px;
        color: #333;
        font-size: 2em;
        font-weight: 600;
    }

    #login-container input[type="text"], 
    #login-container input[type="password"] {
        width: 100%;
        padding: 15px;
        margin-bottom: 20px;
        box-sizing: border-box; 
        border-radius: 8px; 
        border: 1px solid #ccc;
        font-size: 1em;
        transition: all 0.3s ease;
    }

    #login-container input[type="text"]:focus, 
    #login-container input[type="password"]:focus {
        outline: none;
        border-color: #764ba2;
        box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.2);
    }

    #login-container button { 
        width: 100%; 
        padding: 15px; 
        margin-top: 10px; 
        box-sizing: border-box; 
        border-radius: 8px; 
        background-color: #764ba2;
        color: white; 
        border: none; 
        cursor: pointer; 
        font-size: 1.1em;
        font-weight: bold;
        letter-spacing: 0.5px;
        transition: background-color 0.3s ease, transform 0.1s ease;
    }

    #login-container button:hover {
        background-color: #623c85;
    }

    #login-container button:active {
        transform: scale(0.98);
    }

    /* --- CHAT STYLES (UNCHANGED from original) --- */
    #chat-container { display: none; flex-grow: 1; display: flex; }
    #left-panel { width: 30%; max-width: 350px; border-right: 1px solid #ddd; display: flex; flex-direction: column; background-color: white; }
    #left-panel-header { padding: 15px; border-bottom: 1px solid #ddd; }
    #left-panel-header h3 { margin: 0; font-size: 1.2em; }
    #contacts-list { overflow-y: auto; flex-grow: 1; }
    .contact-item { padding: 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0; font-size: 1.1em; }
    .contact-item:hover { background-color: #f5f5f5; }
    .contact-item.active { background-color: #e0e0e0; font-weight: bold; }
    #right-panel { flex-grow: 1; display: flex; flex-direction: column; }
    #chat-header { padding: 15px; border-bottom: 1px solid #ddd; background-color: #f5f5f5; font-weight: bold; font-size: 1.1em; }
    #messages-container { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; }
    .message { max-width: 70%; padding: 10px 15px; border-radius: 18px; margin-bottom: 10px; line-height: 1.4; word-wrap: break-word; }
    .message.sent { background-color: #0084ff; color: white; align-self: flex-end; }
    .message.received { background-color: #e4e6eb; color: #050505; align-self: flex-start; }
    #message-input-container { display: flex; padding: 10px; border-top: 1px solid #ddd; background-color: white; }
    #message-input { flex-grow: 1; border: 1px solid #ccc; border-radius: 18px; padding: 10px 15px; font-size: 1em; }
    #message-input:focus { outline: none; }
    #message-input-container button { margin-left: 10px; border: none; background-color: #0084ff; color: white; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-size: 18px; flex-shrink: 0; }
    #placeholder-right-panel { flex-grow: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #65676b; text-align: center; background-color: #f0f2f5; }
  </style>
</head>
<body>

<div id="app-container">
  <div id="login-container">
    <h2>Iniciar Sesión</h2>
    <input type="text" id="username-input" placeholder="Nombre de usuario">
    <input type="password" id="password-input" placeholder="Contraseña">
    <button onclick="login()">Entrar</button>
  </div>
  
  <div id="chat-container">
    <div id="left-panel">
      <div id="left-panel-header">
        <h3 id="current-user-name"></h3>
      </div>
      <div id="contacts-list"></div>
    </div>
    <div id="right-panel">
      <div id="placeholder-right-panel">
        <h2>Tu mensajero personal</h2>
        <p>Selecciona un contacto para empezar a chatear.</p>
      </div>
      <div id="chat-window" style="display: none; flex-grow: 1; display: flex; flex-direction: column;">
        <div id="chat-header"></div>
        <div id="messages-container"></div>
        <div id="message-input-container">
          <input type="text" id="message-input" placeholder="Escribe un mensaje..." onkeydown="if(event.key === 'Enter') sendMessage()">
          <button onclick="sendMessage()">➤</button>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
  const API_BASE = "{api_base}";
  const PROJECT_ID = "{project_id}";
  const API_KEY = "{api_key}";
  const USERS = {users_json};

  let loggedInUser = null;
  let projectChats = [];
  let activeChat = null;
  let messagePollingInterval = null;

  const loginContainer = document.getElementById('login-container');
  const chatContainer = document.getElementById('chat-container');
  const usernameInput = document.getElementById('username-input');
  const passwordInput = document.getElementById('password-input');
  const contactsList = document.getElementById('contacts-list');
  const chatWindow = document.getElementById('chat-window');
  const placeholderRightPanel = document.getElementById('placeholder-right-panel');
  const chatHeader = document.getElementById('chat-header');
  const messagesContainer = document.getElementById('messages-container');
  const messageInput = document.getElementById('message-input');
  const currentUserNameEl = document.getElementById('current-user-name');

  function init() {
    chatContainer.style.display = 'none';
    loginContainer.style.display = 'block'; // Changed from 'flex' to 'block' for better compatibility
    usernameInput.focus();
  }

  async function login() {
    const name = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!name || !password) {
      alert("Por favor, introduce nombre de usuario y contraseña.");
      return;
    }

    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, password })
      });

      if (!response.ok) throw new Error('Credenciales incorrectas');

      loggedInUser = await response.json();
      loginContainer.style.display = 'none';
      chatContainer.style.display = 'flex';
      currentUserNameEl.textContent = `Hola, ${loggedInUser.name}`;
      await loadProjectChats();
      populateContacts();
    } catch (error) {
      console.error("Error de login:", error);
      alert("Login fallido. Revisa tu usuario y contraseña.");
    }
  }

  function populateContacts() {
    contactsList.innerHTML = '';
    const otherUsers = USERS.filter(u => u.uuid !== loggedInUser.uuid);
    otherUsers.forEach(user => {
      const contactDiv = document.createElement('div');
      contactDiv.className = 'contact-item';
      contactDiv.textContent = user.name;
      contactDiv.dataset.userId = user.uuid;
      contactDiv.onclick = () => openChatWithUser(user);
      contactsList.appendChild(contactDiv);
    });
  }

  async function loadProjectChats() {
    try {
      const response = await fetch(`${API_BASE}/chats`, {
        headers: { 'X-Project-Id': PROJECT_ID, 'X-Api-Key': API_KEY }
      });
      if (!response.ok) throw new Error('Fallo al cargar los chats');
      projectChats = await response.json();
    } catch (error) {
      console.error("Error cargando los chats del proyecto:", error);
      alert("No se pudieron cargar los chats remotos.");
    }
  }

  async function openChatWithUser(contactUser) {
    if (messagePollingInterval) clearInterval(messagePollingInterval);

    document.querySelectorAll('.contact-item').forEach(el => el.classList.remove('active'));
    const sel = document.querySelector(`.contact-item[data-user-id='${contactUser.uuid}']`);
    if (sel) sel.classList.add('active');

    let chat = projectChats.find(c =>
      c.type === 'direct' &&
      c.users.length === 2 &&
      c.users.includes(loggedInUser.uuid) &&
      c.users.includes(contactUser.uuid)
    );

    if (!chat) {
      try {
        const response = await fetch(`${API_BASE}/chats/direct`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Project-Id': PROJECT_ID,
            'X-Api-Key': API_KEY
          },
          body: JSON.stringify({ users: [loggedInUser.uuid, contactUser.uuid] })
        });
        if (!response.ok) throw new Error('Fallo al crear el chat remoto');
        chat = await response.json();
        projectChats.push(chat);

        try {
          await fetch(`/users/${loggedInUser.uuid}/chatRefs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chat.id })
          });
          await fetch(`/users/${contactUser.uuid}/chatRefs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chat_id: chat.id })
          });
        } catch (e) { console.warn("No se pudo actualizar chat_ids locales:", e); }
      } catch (error) {
        console.error("Error creando el chat remoto:", error);
        alert("No se pudo crear un nuevo chat remoto.");
        return;
      }
    }

    activeChat = chat;
    placeholderRightPanel.style.display = 'none';
    chatWindow.style.display = 'flex';
    chatHeader.textContent = `Chat con ${contactUser.name}`;
    messageInput.focus();

    await loadMessages();
    messagePollingInterval = setInterval(loadMessages, 3000);
  }

  async function loadMessages() {
    if (!activeChat) return;
    try {
      const response = await fetch(`${API_BASE}/chats/${activeChat.id}/messages`, {
        headers: { 'X-Project-Id': PROJECT_ID, 'X-Api-Key': API_KEY }
      });
      if (!response.ok) throw new Error('Fallo al cargar los mensajes');
      const messages = await response.json();
      renderMessages(messages);
    } catch (error) {
      console.error(`Error cargando mensajes para el chat ${activeChat.id}:`, error);
    }
  }

  function renderMessages(messages) {
    messagesContainer.innerHTML = '';
    messages.forEach(msg => {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'message';
      messageDiv.classList.add(msg.sender_id === loggedInUser.uuid ? 'sent' : 'received');

      const messageText = document.createElement('div');
      messageText.textContent = msg.text;

      const messageTimestamp = document.createElement('span');
      const date = new Date(msg.timestamp);
      messageTimestamp.textContent = date.toLocaleString();
      messageTimestamp.style.fontSize = '0.7em';
      messageTimestamp.style.display = 'block';
      messageTimestamp.style.color = msg.sender_id === loggedInUser.uuid
        ? 'rgba(255, 255, 255, 0.7)'
        : 'rgba(0, 0, 0, 0.5)';

      messageDiv.appendChild(messageText);
      messageDiv.appendChild(messageTimestamp);
      messagesContainer.appendChild(messageDiv);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !activeChat) return;

    try {
      await fetch(`${API_BASE}/chats/${activeChat.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Project-Id': PROJECT_ID,
          'X-Api-Key': API_KEY
        },
        body: JSON.stringify({ sender_id: loggedInUser.uuid, text })
      });
      messageInput.value = '';
      await loadMessages();
    } catch (error) {
      console.error("Error enviando el mensaje:", error);
      alert("No se pudo enviar el mensaje al servidor remoto.");
    }
  }

  window.onload = init;
</script>

</body>
</html>
"""




# El resto de tu código...
# ...

# =========================
# HTML de prueba /test
# =========================
@app.get("/", response_class=HTMLResponse, tags=["frontend"])
def serve_test_html(
    # Elimina los parámetros de query, ya no son necesarios
    # Los valores se toman del .env
):
    """
    Sirve el HTML de prueba, inyectando:
      - API_BASE: URL del main Firebase
      - PROJECT_ID / API_KEY globales (para todos los usuarios)
      - USERS: los usuarios locales con name/uuid + chat_refs
    """
    users_payload = [norm_user(u) for u in USERS_STORE.values()]
    html = (TEST_HTML
            .replace("{api_base}", json.dumps(API_BASE)[1:-1])
            .replace("{project_id}", json.dumps(PROJECT_ID)[1:-1])
            .replace("{api_key}", json.dumps(API_KEY)[1:-1])
            .replace("{users_json}", json.dumps(users_payload)))
    return HTMLResponse(content=html)
