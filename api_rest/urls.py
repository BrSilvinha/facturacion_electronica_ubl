# api_rest/urls.py - VERSIÓN COMPLETA ACTUALIZADA CON ENDPOINTS SUNAT CORREGIDOS

"""
URLs para la API REST de Facturación Electrónica
VERSIÓN COMPLETA con endpoints de documentos, CDR y SUNAT funcionando
"""

from django.urls import path
from . import views
from . import views_sunat

# 🧪 IMPORTAR VIEWS DE ESCENARIOS DE PRUEBA (si existen)
try:
    from .views_test_scenarios import (
        TestScenariosMenuView,
        TestScenario1BoletaCompleta,
        TestScenario2FacturaGravada,
        TestScenario3FacturaExonerada,
        TestScenario4FacturaMixta,
        TestScenario5FacturaExportacion,
        TestAllScenariosView
    )
    TEST_SCENARIOS_AVAILABLE = True
except ImportError:
    TEST_SCENARIOS_AVAILABLE = False

urlpatterns = [
    # =========================================================================
    # ENDPOINTS PRINCIPALES DE LA API
    # =========================================================================
    path('test/', views.TestAPIView.as_view(), name='api-test'),
    path('generar-xml/', views.GenerarXMLView.as_view(), name='generar-xml'),
    path('tipos-documento/', views.TiposDocumentoView.as_view(), name='tipos-documento'),
    path('empresas/', views.EmpresasView.as_view(), name='empresas'),
    path('validar-ruc/', views.ValidarRUCView.as_view(), name='validar-ruc'),
    path('certificate-info/', views.CertificateInfoView.as_view(), name='certificate-info'),
    
    # =========================================================================
    # ENDPOINTS DE DOCUMENTOS
    # =========================================================================
    path('documentos/', views.DocumentosListView.as_view(), name='documentos-list'),
    path('documentos/<uuid:documento_id>/', views.DocumentoDetailView.as_view(), name='documento-detail'),
    path('documentos/stats/', views.DocumentosStatsView.as_view(), name='documentos-stats'),
    
    # =========================================================================
    # 🔧 ENDPOINTS SUNAT - CORREGIDOS Y FUNCIONANDO
    # =========================================================================
    path('sunat/test-connection/', views_sunat.TestSUNATConnectionView.as_view(), name='sunat-test-connection'),
    path('sunat/send-bill/', views_sunat.SendBillToSUNATView.as_view(), name='sunat-send-bill'),
    path('sunat/send-summary/', views_sunat.SendSummaryToSUNATView.as_view(), name='sunat-send-summary'),
    path('sunat/get-status/', views_sunat.GetStatusSUNATView.as_view(), name='sunat-get-status'),
    path('sunat/get-status-cdr/', views_sunat.GetStatusCDRView.as_view(), name='sunat-get-status-cdr'),
    path('sunat/status/', views_sunat.SUNATStatusView.as_view(), name='sunat-status'),
    
    # =========================================================================
    # ENDPOINTS CDR - PROCESAMIENTO DE CONSTANCIA DE RECEPCIÓN
    # =========================================================================
    # path('cdr/process/', views_cdr.ProcessCDRView.as_view(), name='cdr-process'),
    # path('cdr/generate/', views_cdr.GenerateCDRView.as_view(), name='cdr-generate'),
    # path('cdr/status/<uuid:documento_id>/', views_cdr.CDRStatusView.as_view(), name='cdr-status'),
    # path('cdr/simulate-sunat/', views_cdr.SimulateSUNATResponseView.as_view(), name='cdr-simulate-sunat'),
    
    # Endpoint para obtener información de CDR (compatibilidad)
    path('cdr-info/<uuid:documento_id>/', views.CDRInfoView.as_view(), name='cdr-info'),
]

# =========================================================================
# 🧪 ENDPOINTS DE PRUEBA PARA NUBEFACT - OPCIONALES
# =========================================================================
if TEST_SCENARIOS_AVAILABLE:
    urlpatterns += [
        # Menú principal de escenarios
        path('test-scenarios/', TestScenariosMenuView.as_view(), name='test-scenarios-menu'),
        
        # 5 Escenarios específicos para probar-xml.nubefact.com
        path('test-scenarios/scenario-1-boleta-completa/', 
             TestScenario1BoletaCompleta.as_view(), 
             name='test-scenario-1'),
        
        path('test-scenarios/scenario-2-factura-gravada/', 
             TestScenario2FacturaGravada.as_view(), 
             name='test-scenario-2'),
        
        path('test-scenarios/scenario-3-factura-exonerada/', 
             TestScenario3FacturaExonerada.as_view(), 
             name='test-scenario-3'),
        
        path('test-scenarios/scenario-4-factura-mixta/', 
             TestScenario4FacturaMixta.as_view(), 
             name='test-scenario-4'),
        
        path('test-scenarios/scenario-5-factura-exportacion/', 
             TestScenario5FacturaExportacion.as_view(), 
             name='test-scenario-5'),
        
        # Ejecutar todos los escenarios de una vez
        path('test-scenarios/run-all-scenarios/', 
             TestAllScenariosView.as_view(), 
             name='test-all-scenarios'),
        
        # =====================================================================
        # ALIASES CORTOS PARA FACILIDAD DE USO
        # =====================================================================
        path('test/menu/', TestScenariosMenuView.as_view(), name='test-menu-alias'),
        path('test/boleta/', TestScenario1BoletaCompleta.as_view(), name='test-boleta-alias'),
        path('test/factura/', TestScenario2FacturaGravada.as_view(), name='test-factura-alias'),
        path('test/exonerada/', TestScenario3FacturaExonerada.as_view(), name='test-exonerada-alias'),
        path('test/mixta/', TestScenario4FacturaMixta.as_view(), name='test-mixta-alias'),
        path('test/exportacion/', TestScenario5FacturaExportacion.as_view(), name='test-exportacion-alias'),
        path('test/all/', TestAllScenariosView.as_view(), name='test-all-alias'),
    ]