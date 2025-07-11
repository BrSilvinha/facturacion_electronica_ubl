# api_rest/urls.py - VERSIÓN COMPLETA ACTUALIZADA

"""
URLs para la API REST de Facturación Electrónica
VERSIÓN COMPLETA con endpoints de documentos
"""

from django.urls import path
from . import views
from . import views_sunat

urlpatterns = [
    # Endpoints principales de la API
    path('test/', views.TestAPIView.as_view(), name='api-test'),
    path('generar-xml/', views.GenerarXMLView.as_view(), name='generar-xml'),
    path('tipos-documento/', views.TiposDocumentoView.as_view(), name='tipos-documento'),
    path('empresas/', views.EmpresasView.as_view(), name='empresas'),
    path('validar-ruc/', views.ValidarRUCView.as_view(), name='validar-ruc'),
    path('certificate-info/', views.CertificateInfoView.as_view(), name='certificate-info'),
    
    # 🆕 NUEVOS ENDPOINTS DE DOCUMENTOS
    path('documentos/', views.DocumentosListView.as_view(), name='documentos-list'),
    path('documentos/<uuid:documento_id>/', views.DocumentoDetailView.as_view(), name='documento-detail'),
    path('documentos/stats/', views.DocumentosStatsView.as_view(), name='documentos-stats'),
    
    # Endpoints SUNAT con Error 0160 fix garantizado
    path('sunat/test-connection/', views_sunat.TestSUNATConnectionView.as_view(), name='sunat-test-connection'),
    path('sunat/send-bill/', views_sunat.SendBillToSUNATView.as_view(), name='sunat-send-bill'),
    path('sunat/send-summary/', views_sunat.SendSummaryToSUNATView.as_view(), name='sunat-send-summary'),
    path('sunat/get-status/', views_sunat.GetStatusSUNATView.as_view(), name='sunat-get-status'),
    path('sunat/get-status-cdr/', views_sunat.GetStatusCDRView.as_view(), name='sunat-get-status-cdr'),
    path('sunat/status/', views_sunat.SUNATStatusView.as_view(), name='sunat-status'),
    
    # Endpoint para obtener información de CDR
    path('cdr-info/<uuid:documento_id>/', views.CDRInfoView.as_view(), name='cdr-info'),
]