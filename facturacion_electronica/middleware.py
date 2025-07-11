# facturacion_electronica/middleware.py
"""
Middleware personalizado para deshabilitar CSRF en endpoints API
Solo para ambiente de desarrollo
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Middleware para deshabilitar CSRF en endpoints API
    Permite que las peticiones POST/PUT/PATCH/DELETE funcionen sin token CSRF
    """
    
    def process_request(self, request):
        """
        Procesa la petición antes de que llegue a las views
        """
        
        # Solo aplicar en modo DEBUG (desarrollo)
        if not settings.DEBUG:
            return None
        
        # Rutas que deben estar exentas de CSRF
        exempt_paths = [
            '/api/',
            '/admin/api/',  # Si tienes API de admin
        ]
        
        # Verificar si la ruta actual debe estar exenta
        for path in exempt_paths:
            if request.path.startswith(path):
                # Deshabilitar verificación CSRF para esta petición
                setattr(request, '_dont_enforce_csrf_checks', True)
                
                # Log para debugging
                logger.info(f"CSRF deshabilitado para: {request.method} {request.path}")
                
                break
        
        return None
    
    def process_response(self, request, response):
        """
        Procesa la respuesta antes de enviarla al cliente
        Agrega headers CORS adicionales si es necesario
        """
        
        # Solo en desarrollo
        if not settings.DEBUG:
            return response
        
        # Si es una petición API, agregar headers CORS adicionales
        if request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response