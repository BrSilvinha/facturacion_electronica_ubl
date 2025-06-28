from django.urls import path
from . import views

app_name = 'api_rest'

urlpatterns = [
    # Endpoint principal del reto
    path('generar-xml/', views.GenerarXMLView.as_view(), name='generar-xml'),
    
    # Endpoints de apoyo
    path('tipos-documento/', views.TiposDocumentoView.as_view(), name='tipos-documento'),
    path('empresas/', views.EmpresasView.as_view(), name='empresas'),
    path('validar-ruc/', views.ValidarRUCView.as_view(), name='validar-ruc'),
    
    # Endpoint de prueba
    path('test/', views.TestAPIView.as_view(), name='test'),
]