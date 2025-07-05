import logging
from typing import Dict, List, Optional

class LabelManager:
    """Gestor de etiquetas inteligente para Gmail"""
    
    def __init__(self, gmail_client):
        """
        Inicializa el gestor de etiquetas
        
        Args:
            gmail_client: Cliente Gmail API
        """
        self.gmail_client = gmail_client
        self.logger = logging.getLogger(__name__)
        self.existing_labels = {}
        self._load_existing_labels()
    
    def _load_existing_labels(self):
        """Carga etiquetas existentes desde Gmail"""
        try:
            self.existing_labels = self.gmail_client.get_labels()
            self.logger.info(f"Cargadas {len(self.existing_labels)} etiquetas existentes")
        except Exception as e:
            self.logger.error(f"Error cargando etiquetas existentes: {e}")
            self.existing_labels = {}
    
    def create_label_if_not_exists(self, label_name: str, color_bg: str = '#4285f4', color_text: str = '#ffffff') -> Optional[str]:
        """
        Crea una etiqueta si no existe
        
        Args:
            label_name (str): Nombre de la etiqueta
            color_bg (str): Color de fondo (hex)
            color_text (str): Color del texto (hex)
            
        Returns:
            str: ID de la etiqueta (nueva o existente)
        """
        try:
            # Verificar si la etiqueta ya existe
            if label_name in self.existing_labels:
                return self.existing_labels[label_name]
            
            # Crear nueva etiqueta
            result = self.gmail_client.create_label(label_name, color_bg, color_text)
            
            if result:
                label_id = result['id']
                self.existing_labels[label_name] = label_id
                self.logger.info(f"Etiqueta '{label_name}' creada con ID: {label_id}")
                return label_id
            else:
                self.logger.error(f"No se pudo crear la etiqueta '{label_name}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando etiqueta '{label_name}': {e}")
            return None
    
    def apply_smart_labels(self, message_id: str, classification: str, sender_group: str) -> bool:
        """
        Aplica etiquetas inteligentes basadas en clasificación IA y grupo de remitente
        
        Args:
            message_id (str): ID del mensaje
            classification (str): Clasificación IA (Urgente, Importante, Otros)
            sender_group (str): Grupo del remitente
            
        Returns:
            bool: True si las etiquetas se aplicaron correctamente
        """
        try:
            labels_to_apply = []
            
            # Etiqueta por clasificación IA
            if classification and classification != "Otros":
                label_name = f"IA/{classification}"
                label_id = self.create_label_if_not_exists(
                    label_name, 
                    self._get_classification_color(classification)
                )
                if label_id:
                    labels_to_apply.append(label_id)
            
            # Etiqueta por grupo de remitente
            if sender_group and sender_group != "Otros":
                label_name = f"Grupos/{sender_group}"
                label_id = self.create_label_if_not_exists(
                    label_name,
                    self._get_group_color(sender_group)
                )
                if label_id:
                    labels_to_apply.append(label_id)
            
            # Aplicar etiquetas si hay alguna
            if labels_to_apply:
                success = self.gmail_client.add_labels(message_id, labels_to_apply)
                if success:
                    self.logger.info(f"Etiquetas aplicadas al mensaje {message_id}: {len(labels_to_apply)}")
                    return True
                else:
                    self.logger.error(f"Error aplicando etiquetas al mensaje {message_id}")
                    return False
            else:
                self.logger.debug(f"No se aplicaron etiquetas al mensaje {message_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error aplicando etiquetas inteligentes: {e}")
            return False
    
    def organize_by_priority(self, message_id: str, priority_level: str) -> bool:
        """
        Organiza mensaje por nivel de prioridad
        
        Args:
            message_id (str): ID del mensaje
            priority_level (str): Nivel de prioridad (Alta, Media, Baja)
            
        Returns:
            bool: True si la etiqueta se aplicó correctamente
        """
        try:
            if priority_level == "Baja":
                # No etiquetar prioridad baja
                return True
            
            label_name = f"Prioridad/{priority_level}"
            color = self._get_priority_color(priority_level)
            
            label_id = self.create_label_if_not_exists(label_name, color)
            
            if label_id:
                success = self.gmail_client.add_labels(message_id, [label_id])
                if success:
                    self.logger.info(f"Etiqueta de prioridad '{priority_level}' aplicada al mensaje {message_id}")
                    return True
                else:
                    self.logger.error(f"Error aplicando etiqueta de prioridad al mensaje {message_id}")
                    return False
            else:
                self.logger.error(f"No se pudo crear etiqueta de prioridad '{priority_level}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error organizando por prioridad: {e}")
            return False
    
    def organize_by_date(self, message_id: str, date_info: str) -> bool:
        """
        Organiza mensaje por fecha (año-mes)
        
        Args:
            message_id (str): ID del mensaje
            date_info (str): Información de fecha (formato: YYYY-MM)
            
        Returns:
            bool: True si la etiqueta se aplicó correctamente
        """
        try:
            label_name = f"Fecha/{date_info}"
            label_id = self.create_label_if_not_exists(label_name, '#607d8b')
            
            if label_id:
                success = self.gmail_client.add_labels(message_id, [label_id])
                if success:
                    self.logger.debug(f"Etiqueta de fecha '{date_info}' aplicada al mensaje {message_id}")
                    return True
                else:
                    self.logger.error(f"Error aplicando etiqueta de fecha al mensaje {message_id}")
                    return False
            else:
                self.logger.error(f"No se pudo crear etiqueta de fecha '{date_info}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error organizando por fecha: {e}")
            return False
    
    def organize_by_domain(self, message_id: str, domain: str) -> bool:
        """
        Organiza mensaje por dominio del remitente
        
        Args:
            message_id (str): ID del mensaje
            domain (str): Dominio del remitente
            
        Returns:
            bool: True si la etiqueta se aplicó correctamente
        """
        try:
            # Solo etiquetar dominios importantes
            important_domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com']
            
            if domain.lower() not in important_domains:
                label_name = f"Dominios/{domain}"
                label_id = self.create_label_if_not_exists(label_name, '#795548')
                
                if label_id:
                    success = self.gmail_client.add_labels(message_id, [label_id])
                    if success:
                        self.logger.debug(f"Etiqueta de dominio '{domain}' aplicada al mensaje {message_id}")
                        return True
                    else:
                        self.logger.error(f"Error aplicando etiqueta de dominio al mensaje {message_id}")
                        return False
                else:
                    self.logger.error(f"No se pudo crear etiqueta de dominio '{domain}'")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error organizando por dominio: {e}")
            return False
    
    def apply_comprehensive_labeling(self, message_id: str, message_info: Dict) -> bool:
        """
        Aplica etiquetado comprehensivo a un mensaje
        
        Args:
            message_id (str): ID del mensaje
            message_info (dict): Información del mensaje
            
        Returns:
            bool: True si todas las etiquetas se aplicaron correctamente
        """
        try:
            success_count = 0
            total_operations = 0
            
            # Clasificación IA y grupos
            if 'classification' in message_info and 'sender_group' in message_info:
                total_operations += 1
                if self.apply_smart_labels(
                    message_id, 
                    message_info['classification'], 
                    message_info['sender_group']
                ):
                    success_count += 1
            
            # Prioridad
            if 'priority' in message_info:
                total_operations += 1
                if self.organize_by_priority(message_id, message_info['priority']):
                    success_count += 1
            
            # Fecha
            if 'date' in message_info:
                total_operations += 1
                try:
                    # Extraer año-mes de la fecha
                    date_parts = message_info['date'].split('-')
                    if len(date_parts) >= 2:
                        year_month = f"{date_parts[0]}-{date_parts[1]}"
                        if self.organize_by_date(message_id, year_month):
                            success_count += 1
                except:
                    pass
            
            # Dominio
            if 'domain' in message_info:
                total_operations += 1
                if self.organize_by_domain(message_id, message_info['domain']):
                    success_count += 1
            
            # Verificar éxito general
            if total_operations > 0:
                success_rate = success_count / total_operations
                self.logger.info(f"Etiquetado completado para mensaje {message_id}: {success_count}/{total_operations} ({success_rate:.1%})")
                return success_rate >= 0.7  # 70% de éxito mínimo
            else:
                self.logger.warning(f"No se realizaron operaciones de etiquetado para mensaje {message_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error en etiquetado comprehensivo: {e}")
            return False
    
    def _get_classification_color(self, classification: str) -> str:
        """Obtiene color para etiquetas de clasificación IA"""
        colors = {
            'Urgente': '#f44336',      # Rojo
            'Importante': '#ff9800',   # Naranja
            'Otros': '#9e9e9e'         # Gris
        }
        return colors.get(classification, '#4285f4')
    
    def _get_group_color(self, group: str) -> str:
        """Obtiene color para etiquetas de grupos"""
        colors = {
            'Trabajo': '#2196f3',      # Azul
            'Personal': '#4caf50',     # Verde
            'Bancos': '#673ab7',       # Morado
            'Servicios': '#ff5722',    # Naranja rojizo
            'Familia': '#e91e63',      # Rosa
            'Clientes': '#00bcd4',     # Cian
            'Soporte': '#ffc107',      # Amarillo
            'Otros': '#9e9e9e'         # Gris
        }
        return colors.get(group, '#607d8b')
    
    def _get_priority_color(self, priority: str) -> str:
        """Obtiene color para etiquetas de prioridad"""
        colors = {
            'Alta': '#f44336',         # Rojo
            'Media': '#ffaa00',        # Naranja
            'Baja': '#4caf50'          # Verde
        }
        return colors.get(priority, '#9e9e9e')
    
    def get_label_stats(self) -> Dict:
        """
        Obtiene estadísticas de etiquetas
        
        Returns:
            dict: Estadísticas de etiquetas
        """
        try:
            stats = {
                'total_labels': len(self.existing_labels),
                'ia_labels': len([l for l in self.existing_labels.keys() if l.startswith('IA/')]),
                'group_labels': len([l for l in self.existing_labels.keys() if l.startswith('Grupos/')]),
                'priority_labels': len([l for l in self.existing_labels.keys() if l.startswith('Prioridad/')]),
                'date_labels': len([l for l in self.existing_labels.keys() if l.startswith('Fecha/')]),
                'domain_labels': len([l for l in self.existing_labels.keys() if l.startswith('Dominios/')])
            }
            
            self.logger.info(f"Estadísticas de etiquetas: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de etiquetas: {e}")
            return {}
    
    def cleanup_unused_labels(self, dry_run: bool = True) -> List[str]:
        """
        Limpia etiquetas no utilizadas (solo aquellas creadas automáticamente)
        
        Args:
            dry_run (bool): Si es True, solo muestra qué se eliminaría
            
        Returns:
            list: Lista de etiquetas que se eliminaron o eliminarían
        """
        try:
            # Prefijos de etiquetas creadas automáticamente
            auto_prefixes = ['IA/', 'Grupos/', 'Prioridad/', 'Fecha/', 'Dominios/']
            
            cleanup_candidates = []
            
            for label_name in self.existing_labels.keys():
                if any(label_name.startswith(prefix) for prefix in auto_prefixes):
                    cleanup_candidates.append(label_name)
            
            if dry_run:
                self.logger.info(f"Se encontraron {len(cleanup_candidates)} etiquetas automáticas para posible limpieza")
                return cleanup_candidates
            else:
                # Aquí implementaríamos la lógica real de limpieza
                # Por seguridad, no implementamos eliminación automática
                self.logger.warning("Limpieza automática de etiquetas no implementada por seguridad")
                return []
                
        except Exception as e:
            self.logger.error(f"Error en limpieza de etiquetas: {e}")
            return []