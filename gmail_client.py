import os
import pickle
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

class GmailClient:
    """Cliente para interactuar con Gmail API de manera completa"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.labels',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Inicializa el cliente Gmail API
        
        Args:
            credentials_file (str): Ruta al archivo de credenciales OAuth2
        """
        self.credentials_file = credentials_file
        self.service = None
        self.logger = logging.getLogger(__name__)
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Gmail API usando OAuth2"""
        creds = None
        
        # Cargar credenciales existentes
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas, obtener nuevas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Credenciales OAuth2 renovadas exitosamente")
                except Exception as e:
                    self.logger.error(f"Error renovando credenciales: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Archivo de credenciales no encontrado: {self.credentials_file}\n"
                        "Por favor, descarga las credenciales OAuth2 desde Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
                self.logger.info("Nuevas credenciales OAuth2 obtenidas")
            
            # Guardar credenciales para futuros usos
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        # Construir el servicio Gmail API
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info("Cliente Gmail API inicializado exitosamente")
    
    def get_unread_messages(self, max_results=100):
        """
        Obtiene mensajes no leídos
        
        Args:
            max_results (int): Número máximo de mensajes a obtener
            
        Returns:
            list: Lista de mensajes no leídos
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            self.logger.info(f"Obtenidos {len(messages)} mensajes no leídos")
            return messages
            
        except HttpError as e:
            self.logger.error(f"Error obteniendo mensajes no leídos: {e}")
            return []
    
    def get_message_details(self, message_id):
        """
        Obtiene detalles completos de un mensaje
        
        Args:
            message_id (str): ID del mensaje
            
        Returns:
            dict: Detalles del mensaje
        """
        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return msg
            
        except HttpError as e:
            self.logger.error(f"Error obteniendo detalles del mensaje {message_id}: {e}")
            return None
    
    def extract_message_info(self, message):
        """
        Extrae información relevante de un mensaje
        
        Args:
            message (dict): Mensaje completo de Gmail API
            
        Returns:
            dict: Información extraída del mensaje
        """
        try:
            payload = message['payload']
            headers = payload.get('headers', [])
            
            # Extraer headers importantes
            info = {
                'id': message['id'],
                'thread_id': message['threadId'],
                'sender': '',
                'subject': '',
                'date': '',
                'body': '',
                'snippet': message.get('snippet', ''),
                'labels': message.get('labelIds', [])
            }
            
            # Procesar headers
            for header in headers:
                name = header['name'].lower()
                value = header['value']
                
                if name == 'from':
                    info['sender'] = value
                elif name == 'subject':
                    info['subject'] = value
                elif name == 'date':
                    info['date'] = value
            
            # Extraer cuerpo del mensaje
            info['body'] = self._extract_body(payload)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error extrayendo información del mensaje: {e}")
            return None
    
    def _extract_body(self, payload):
        """
        Extrae el cuerpo de texto de un mensaje
        
        Args:
            payload (dict): Payload del mensaje
            
        Returns:
            str: Cuerpo del mensaje
        """
        body = ""
        
        if 'parts' in payload:
            # Mensaje multipart
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        break
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
        else:
            # Mensaje simple
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')
        
        return body
    
    def send_message(self, to, subject, body, html=False, reply_to=None):
        """
        Envía un mensaje de correo
        
        Args:
            to (str): Destinatario
            subject (str): Asunto
            body (str): Cuerpo del mensaje
            html (bool): Si el cuerpo es HTML
            reply_to (str): ID del mensaje al que responder
            
        Returns:
            dict: Resultado del envío
        """
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if reply_to:
                message['In-Reply-To'] = reply_to
                message['References'] = reply_to
            
            # Agregar cuerpo del mensaje
            if html:
                message.attach(MIMEText(body, 'html'))
            else:
                message.attach(MIMEText(body, 'plain'))
            
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Enviar mensaje
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self.logger.info(f"Mensaje enviado exitosamente: {result['id']}")
            return result
            
        except HttpError as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            return None
    
    def mark_as_read(self, message_id):
        """
        Marca un mensaje como leído
        
        Args:
            message_id (str): ID del mensaje
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            self.logger.debug(f"Mensaje {message_id} marcado como leído")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error marcando mensaje como leído: {e}")
            return False
    
    def add_labels(self, message_id, label_ids):
        """
        Agrega etiquetas a un mensaje
        
        Args:
            message_id (str): ID del mensaje
            label_ids (list): Lista de IDs de etiquetas
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': label_ids}
            ).execute()
            
            self.logger.debug(f"Etiquetas {label_ids} agregadas al mensaje {message_id}")
            return True
            
        except HttpError as e:
            self.logger.error(f"Error agregando etiquetas: {e}")
            return False
    
    def get_labels(self):
        """
        Obtiene todas las etiquetas disponibles
        
        Returns:
            dict: Diccionario con nombre y ID de etiquetas
        """
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            label_dict = {}
            for label in labels:
                label_dict[label['name']] = label['id']
            
            self.logger.debug(f"Obtenidas {len(labels)} etiquetas")
            return label_dict
            
        except HttpError as e:
            self.logger.error(f"Error obteniendo etiquetas: {e}")
            return {}
    
    def create_label(self, name, color_bg='#4285f4', color_text='#ffffff'):
        """
        Crea una nueva etiqueta
        
        Args:
            name (str): Nombre de la etiqueta
            color_bg (str): Color de fondo
            color_text (str): Color del texto
            
        Returns:
            dict: Etiqueta creada
        """
        try:
            label_object = {
                'name': name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'backgroundColor': color_bg,
                    'textColor': color_text
                }
            }
            
            result = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            self.logger.info(f"Etiqueta '{name}' creada exitosamente")
            return result
            
        except HttpError as e:
            self.logger.error(f"Error creando etiqueta '{name}': {e}")
            return None
    
    def get_profile(self):
        """
        Obtiene información del perfil del usuario
        
        Returns:
            dict: Información del perfil
        """
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            self.logger.debug(f"Perfil obtenido: {profile['emailAddress']}")
            return profile
            
        except HttpError as e:
            self.logger.error(f"Error obteniendo perfil: {e}")
            return None