# facturacion_electronica/urls.py
"""
URL configuration for facturacion_electronica project.
Versión con CSRF deshabilitado para API REST
"""
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api_rest.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Agregar archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)