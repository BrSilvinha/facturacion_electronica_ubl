from django.urls import path
from . import views, views_sunat

app_name = 'api_rest'

urlpatterns = [
    # === ENDPOINTS PRINCIPALES ===
    # Endpoint principal del reto
    path('generar-xml/', views.GenerarXMLView.as_view(), name='generar-xml'),
    
    # === ENDPOINTS DE APOYO ===
    path('tipos-documento/', views.TiposDocumentoView.as_view(), name='tipos-documento'),
    path('empresas/', views.EmpresasView.as_view(), name='empresas'),
    path('validar-ruc/', views.ValidarRUCView.as_view(), name='validar-ruc'),
    
    # === ENDPOINTS SUNAT - NIVEL 3 ===
    # Pruebas y estado
    path('sunat/test-connection/', views_sunat.TestSUNATConnectionView.as_view(), name='sunat-test-connection'),
    path('sunat/status/', views_sunat.SUNATStatusView.as_view(), name='sunat-status'),
    
    # Envío de documentos
    path('sunat/send-bill/', views_sunat.SendBillToSUNATView.as_view(), name='sunat-send-bill'),
    path('sunat/send-summary/', views_sunat.SendSummaryToSUNATView.as_view(), name='sunat-send-summary'),
    
    # Consultas
    path('sunat/get-status/', views_sunat.GetStatusSUNATView.as_view(), name='sunat-get-status'),
    path('sunat/get-status-cdr/', views_sunat.GetStatusCDRView.as_view(), name='sunat-get-status-cdr'),
    
    # === ENDPOINT DE PRUEBA ===
    path('test/', views.TestAPIView.as_view(), name='test'),
]