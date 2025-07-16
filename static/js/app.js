// app.js - Sistema de Facturación Electrónica UBL 2.1

// Configuración
const API_BASE = 'http://localhost:8000/api';
const EMPRESA_ID = 'c11dba61-2837-4bcc-b197-301e78168582'; // ID fijo de la empresa

let itemCounter = 0;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    checkSystemStatus();
    setDefaultDate();
    addItem(); // Agregar primer item por defecto
    
    // Event listener para el formulario
    document.getElementById('documentForm').addEventListener('submit', handleFormSubmit);
});

// =============================
// FUNCIONES DE NAVEGACIÓN
// =============================

function showSection(sectionName) {
    // Ocultar todas las secciones
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.add('d-none');
    });
    
    // Mostrar sección seleccionada
    document.getElementById(`section-${sectionName}`).classList.remove('d-none');
    
    // Actualizar botones del sidebar
    document.querySelectorAll('.list-group-item').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Cargar datos específicos de la sección
    if (sectionName === 'documentos') {
        loadDocuments();
    }
}

// =============================
// ESTADO DEL SISTEMA
// =============================

async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/test/`);
        const data = await response.json();
        
        if (data.success) {
            updateConnectionStatus('online', 'Conectado');
            updateSystemStatus(data.data);
        } else {
            updateConnectionStatus('offline', 'Error');
        }
    } catch (error) {
        updateConnectionStatus('offline', 'Sin conexión');
        console.error('Error checking status:', error);
    }
}

function updateConnectionStatus(status, text) {
    const badge = document.getElementById('connectionStatus');
    badge.textContent = text;
    badge.className = `badge bg-${status === 'online' ? 'success' : 'danger'}`;
}

function updateSystemStatus(data) {
    const container = document.getElementById('systemStatus');
    const systemStatus = data.system_status;
    
    container.innerHTML = `
        <div class="row g-2">
            <div class="col-12">
                <span class="badge ${systemStatus.firma_digital_disponible ? 'bg-success' : 'bg-warning'}">
                    <i class="bi bi-shield-check"></i> 
                    ${systemStatus.firma_digital_disponible ? 'Firma Real' : 'Simulada'}
                </span>
            </div>
            <div class="col-12">
                <small class="text-muted">
                    Documentos: ${systemStatus.total_documentos}<br>
                    Empresas: ${systemStatus.total_empresas}<br>
                    Cert: ${systemStatus.certificado_tipo}
                </small>
            </div>
        </div>
    `;
}

// =============================
// FORMULARIO DE DOCUMENTO
// =============================

function setDefaultDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('fechaEmision').value = today;
}

function updateFormByDocType() {
    const tipo = document.getElementById('tipoDocumento').value;
    const serie = document.getElementById('serie');
    const receptorTipo = document.getElementById('receptorTipoDoc');
    const receptorNumero = document.getElementById('receptorNumero');
    const receptorRazon = document.getElementById('receptorRazon');
    
    // Actualizar serie según tipo
    if (tipo === '01') {
        serie.value = 'F001';
        receptorTipo.value = '6'; // RUC para facturas
        receptorNumero.placeholder = '20123456789';
        receptorRazon.placeholder = 'EMPRESA CLIENTE SAC';
        
        // Limpiar campos si estaban con datos de boleta
        if (receptorNumero.value.length === 8) {
            receptorNumero.value = '';
            receptorRazon.value = '';
        }
    } else if (tipo === '03') {
        serie.value = 'B001';
        receptorTipo.value = '1'; // DNI para boletas
        receptorNumero.placeholder = '12345678';
        receptorRazon.placeholder = 'CLIENTE DE PRUEBA';
        
        // Limpiar campos si estaban con datos de factura
        if (receptorNumero.value.length === 11) {
            receptorNumero.value = '';
            receptorRazon.value = '';
        }
    } else if (tipo === '07') {
        serie.value = 'FC01';
    } else if (tipo === '08') {
        serie.value = 'FD01';
    }
}

function addItem() {
    itemCounter++;
    const container = document.getElementById('itemsContainer');
    
    const itemHtml = `
        <div class="card mb-2" id="item-${itemCounter}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">Item ${itemCounter}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeItem(${itemCounter})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
                <div class="row">
                    <div class="col-md-3">
                        <div class="mb-2">
                            <label class="form-label">Código</label>
                            <input type="text" class="form-control form-control-sm" name="codigo_producto_${itemCounter}" placeholder="PROD001">
                        </div>
                    </div>
                    <div class="col-md-5">
                        <div class="mb-2">
                            <label class="form-label">Descripción</label>
                            <input type="text" class="form-control form-control-sm" name="descripcion_${itemCounter}" placeholder="PRODUCTO DE PRUEBA" required>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="mb-2">
                            <label class="form-label">Unidad</label>
                            <select class="form-select form-select-sm" name="unidad_medida_${itemCounter}">
                                <option value="NIU">NIU</option>
                                <option value="ZZ">ZZ</option>
                                <option value="KGM">KGM</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-md-2">
                        <div class="mb-2">
                            <label class="form-label">Cantidad</label>
                            <input type="number" class="form-control form-control-sm" name="cantidad_${itemCounter}" value="1" step="0.001" required>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-4">
                        <div class="mb-2">
                            <label class="form-label">Valor Unitario</label>
                            <input type="number" class="form-control form-control-sm" name="valor_unitario_${itemCounter}" value="10.00" step="0.01" required>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="mb-2">
                            <label class="form-label">Afectación IGV</label>
                            <select class="form-select form-select-sm" name="afectacion_igv_${itemCounter}">
                                <option value="10">10 - Gravado</option>
                                <option value="20">20 - Exonerado</option>
                                <option value="30">30 - Inafecto</option>
                                <option value="40">40 - Exportación</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', itemHtml);
}

function removeItem(itemId) {
    const item = document.getElementById(`item-${itemId}`);
    if (item) {
        item.remove();
    }
}

function resetForm() {
    document.getElementById('documentForm').reset();
    document.getElementById('itemsContainer').innerHTML = '';
    itemCounter = 0;
    setDefaultDate();
    addItem();
}

// =============================
// AUTO-COMPLETADO DE DATOS DE PRUEBA
// =============================

function fillTestData() {
    // Limpiar formulario primero
    resetForm();
    
    // Datos de prueba para Boleta
    const testData = {
        boleta: {
            tipo_documento: '03',
            serie: 'B001',
            numero: Math.floor(Math.random() * 1000) + 1,
            receptor: {
                tipo_doc: '1',
                numero_doc: '12345678',
                razon_social: 'CLIENTE DE PRUEBA',
                direccion: 'AV. LIMA 123, LIMA'
            },
            items: [
                {
                    codigo_producto: 'PROD001',
                    descripcion: 'PRODUCTO DE PRUEBA 1',
                    unidad_medida: 'NIU',
                    cantidad: 2,
                    valor_unitario: 10.00,
                    afectacion_igv: '10'
                },
                {
                    codigo_producto: 'SERV001',
                    descripcion: 'SERVICIO DE PRUEBA',
                    unidad_medida: 'ZZ',
                    cantidad: 1,
                    valor_unitario: 25.00,
                    afectacion_igv: '10'
                }
            ]
        },
        factura: {
            tipo_documento: '01',
            serie: 'F001',
            numero: Math.floor(Math.random() * 1000) + 1,
            receptor: {
                tipo_doc: '6',
                numero_doc: '20123456789',
                razon_social: 'EMPRESA CLIENTE SAC',
                direccion: 'AV. COMERCIAL 456, LIMA'
            },
            items: [
                {
                    codigo_producto: 'CONS001',
                    descripcion: 'SERVICIO DE CONSULTORIA',
                    unidad_medida: 'ZZ',
                    cantidad: 1,
                    valor_unitario: 1000.00,
                    afectacion_igv: '10'
                }
            ]
        }
    };
    
    // Preguntar al usuario qué tipo de documento quiere
    const tipoDoc = prompt('¿Qué tipo de documento deseas generar?\n\n1 = Factura\n2 = Boleta\n\nEscribe 1 o 2:', '2');
    
    let selectedData;
    if (tipoDoc === '1') {
        selectedData = testData.factura;
        showAlert('info', 'Datos de Factura cargados', 'Se han cargado los datos de prueba para una factura.');
    } else {
        selectedData = testData.boleta;
        showAlert('info', 'Datos de Boleta cargados', 'Se han cargado los datos de prueba para una boleta.');
    }
    
    // Llenar formulario
    document.getElementById('tipoDocumento').value = selectedData.tipo_documento;
    document.getElementById('serie').value = selectedData.serie;
    document.getElementById('numero').value = selectedData.numero;
    
    // Actualizar campos según tipo de documento
    updateFormByDocType();
    
    // Llenar datos del receptor
    document.getElementById('receptorTipoDoc').value = selectedData.receptor.tipo_doc;
    document.getElementById('receptorNumero').value = selectedData.receptor.numero_doc;
    document.getElementById('receptorRazon').value = selectedData.receptor.razon_social;
    document.getElementById('receptorDireccion').value = selectedData.receptor.direccion;
    
    // Limpiar items existentes
    document.getElementById('itemsContainer').innerHTML = '';
    itemCounter = 0;
    
    // Agregar items de prueba
    selectedData.items.forEach(item => {
        addItem();
        const currentItemId = itemCounter;
        
        document.querySelector(`[name="codigo_producto_${currentItemId}"]`).value = item.codigo_producto;
        document.querySelector(`[name="descripcion_${currentItemId}"]`).value = item.descripcion;
        document.querySelector(`[name="unidad_medida_${currentItemId}"]`).value = item.unidad_medida;
        document.querySelector(`[name="cantidad_${currentItemId}"]`).value = item.cantidad;
        document.querySelector(`[name="valor_unitario_${currentItemId}"]`).value = item.valor_unitario;
        document.querySelector(`[name="afectacion_igv_${currentItemId}"]`).value = item.afectacion_igv;
    });
    
    // Agregar fecha de vencimiento para facturas
    if (selectedData.tipo_documento === '01') {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 30);
        document.getElementById('fechaVencimiento').value = tomorrow.toISOString().split('T')[0];
    }
    
    showAlert('success', '¡Datos cargados!', 'Formulario completado con datos de prueba. Presiona "Generar XML" para crear el documento.');
}

// =============================
// ENVÍO DEL FORMULARIO CON CSRF
// =============================

// Función para obtener token CSRF
function getCSRFToken() {
    // Intentar obtener desde meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    // Fallback: obtener desde cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return null;
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = collectFormData();
    if (!formData) return;
    
    showAlert('info', 'Generando XML...', 'Por favor espere mientras se procesa el documento.');
    
    try {
        // Headers con CSRF
        const headers = {
            'Content-Type': 'application/json',
        };
        
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(`${API_BASE}/generar-xml/`, {
            method: 'POST',
            headers: headers,
            credentials: 'include', // Incluir cookies
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            const tipoDoc = formData.tipo_documento;
            const esBoleta = tipoDoc === '03';
            const esFactura = tipoDoc === '01';
            
            let mensaje = `Documento ${result.data.document.numero_completo} creado con estado: ${result.data.document.estado}`;
            
            if (esBoleta) {
                mensaje += ' - ✅ BOLETA con firma digital aplicada';
            } else if (esFactura) {
                mensaje += ' - ✅ FACTURA con firma digital aplicada';
            }
            
            showAlert('success', '¡Documento generado exitosamente!', mensaje);
            showResultModal(result.data, `${esBoleta ? 'Boleta' : esFactura ? 'Factura' : 'Documento'} Generado`);
            resetForm();
        } else {
            showAlert('danger', 'Error al generar documento', JSON.stringify(result.error || result, null, 2));
        }
    } catch (error) {
        showAlert('danger', 'Error de conexión', error.message);
    }
}

function collectFormData() {
    // Validaciones básicas
    const tipoDocumento = document.getElementById('tipoDocumento').value;
    const serie = document.getElementById('serie').value;
    const numero = document.getElementById('numero').value;
    
    if (!tipoDocumento || !serie || !numero) {
        showAlert('warning', 'Campos requeridos', 'Por favor complete todos los campos obligatorios.');
        return null;
    }

    // Recopilar items
    const items = [];
    const itemElements = document.querySelectorAll('[id^="item-"]');
    
    itemElements.forEach((item, index) => {
        const itemNumber = item.id.split('-')[1];
        const descripcion = item.querySelector(`[name="descripcion_${itemNumber}"]`).value;
        
        if (descripcion.trim()) {
            items.push({
                codigo_producto: item.querySelector(`[name="codigo_producto_${itemNumber}"]`).value || '',
                descripcion: descripcion,
                unidad_medida: item.querySelector(`[name="unidad_medida_${itemNumber}"]`).value,
                cantidad: parseFloat(item.querySelector(`[name="cantidad_${itemNumber}"]`).value),
                valor_unitario: parseFloat(item.querySelector(`[name="valor_unitario_${itemNumber}"]`).value),
                afectacion_igv: item.querySelector(`[name="afectacion_igv_${itemNumber}"]`).value
            });
        }
    });

    if (items.length === 0) {
        showAlert('warning', 'Items requeridos', 'Debe agregar al menos un item al documento.');
        return null;
    }

    // Preparar datos para envío
    return {
        tipo_documento: tipoDocumento,
        serie: serie,
        numero: parseInt(numero),
        fecha_emision: document.getElementById('fechaEmision').value,
        fecha_vencimiento: document.getElementById('fechaVencimiento').value || null,
        moneda: 'PEN',
        empresa_id: EMPRESA_ID,
        receptor: {
            tipo_doc: document.getElementById('receptorTipoDoc').value,
            numero_doc: document.getElementById('receptorNumero').value,
            razon_social: document.getElementById('receptorRazon').value,
            direccion: document.getElementById('receptorDireccion').value || ''
        },
        items: items
    };
}

// =============================
// ESCENARIOS DE PRUEBA
// =============================

async function runScenario(scenarioName) {
    showAlert('info', 'Ejecutando escenario...', `Procesando ${scenarioName}`);
    
    try {
        const response = await fetch(`${API_BASE}/test-scenarios/${scenarioName}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success || result.scenario) {
            showAlert('success', 'Escenario ejecutado', 'Datos de prueba preparados. Revisa el modal para más detalles.');
            showResultModal(result, `Escenario: ${scenarioName}`);
        } else {
            showAlert('warning', 'Escenario en desarrollo', result.message || 'Este escenario aún no está implementado.');
        }
    } catch (error) {
        showAlert('danger', 'Error ejecutando escenario', error.message);
    }
}

async function runAllScenarios() {
    showAlert('info', 'Ejecutando todos los escenarios...', 'Esto puede tomar unos minutos.');
    
    const scenarios = [
        'scenario-1-boleta-completa',
        'scenario-2-factura-gravada',
        'scenario-3-factura-exonerada',
        'scenario-4-factura-mixta',
        'scenario-5-factura-exportacion'
    ];
    
    const results = [];
    
    for (const scenario of scenarios) {
        try {
            const response = await fetch(`${API_BASE}/test-scenarios/${scenario}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            results.push({
                scenario: scenario,
                success: result.success || result.scenario,
                data: result
            });
        } catch (error) {
            results.push({
                scenario: scenario,
                success: false,
                error: error.message
            });
        }
    }
    
    showAlert('info', 'Escenarios completados', `Ejecutados ${results.length} escenarios. Ver detalles en el modal.`);
    showResultModal({ results: results }, 'Todos los Escenarios');
}

// =============================
// GESTIÓN DE DOCUMENTOS
// =============================

async function loadDocuments() {
    const container = document.getElementById('documentsContainer');
    
    container.innerHTML = `
        <div class="text-center">
            <div class="spinner-border" role="status"></div>
            <p class="mt-2">Cargando documentos...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/documentos/`);
        const result = await response.json();
        
        if (result.success) {
            displayDocuments(result.data.documentos);
        } else {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    Error cargando documentos: ${result.error || 'Error desconocido'}
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i>
                Error de conexión: ${error.message}
            </div>
        `;
    }
}

function displayDocuments(documentos) {
    const container = document.getElementById('documentsContainer');
    
    if (documentos.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-file-earmark-text display-4"></i>
                <p class="mt-2">No hay documentos generados aún.</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="row">';
    
    documentos.forEach((doc, index) => {
        const estadoBadge = getEstadoBadge(doc.estado.codigo);
        const tipoIcon = getTipoIcon(doc.tipo_documento.codigo);
        const hasSignature = doc.quality_indicators?.signature_type === 'REAL';
        
        html += `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="card-title">
                                    <i class="bi ${tipoIcon}"></i>
                                    ${doc.numero_completo}
                                </h6>
                                <p class="card-text mb-1">
                                    <strong>Cliente:</strong> ${doc.receptor.razon_social}<br>
                                    <strong>Fecha:</strong> ${doc.fecha_emision}<br>
                                    <strong>Total:</strong> ${doc.moneda} ${doc.totales.total}
                                </p>
                                ${hasSignature ? '<span class="badge bg-success"><i class="bi bi-shield-check"></i> Firmado Digitalmente</span>' : ''}
                            </div>
                            <div class="text-end">
                                ${estadoBadge}
                                <div class="btn-group-vertical btn-group-sm mt-2" role="group">
                                    <button class="btn btn-outline-primary btn-sm" onclick="viewDocument('${doc.id}')">
                                        <i class="bi bi-eye"></i>
                                    </button>
                                    <button class="btn btn-outline-success btn-sm" onclick="sendDocumentToSunat('${doc.id}')">
                                        <i class="bi bi-cloud-upload"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function getEstadoBadge(estado) {
    const badges = {
        'BORRADOR': 'bg-secondary',
        'PENDIENTE': 'bg-warning',
        'FIRMADO': 'bg-success',
        'FIRMADO_SIMULADO': 'bg-info',
        'ENVIADO': 'bg-primary',
        'ACEPTADO': 'bg-success',
        'RECHAZADO': 'bg-danger',
        'ERROR': 'bg-danger'
    };
    
    return `<span class="badge ${badges[estado] || 'bg-secondary'}">${estado}</span>`;
}

function getTipoIcon(tipo) {
    const icons = {
        '01': 'bi-file-earmark-text',
        '03': 'bi-receipt',
        '07': 'bi-file-earmark-minus',
        '08': 'bi-file-earmark-plus'
    };
    
    return icons[tipo] || 'bi-file-earmark';
}

async function viewDocument(documentId) {
    try {
        const response = await fetch(`${API_BASE}/documentos/${documentId}/`);
        const result = await response.json();
        
        if (result.success) {
            showResultModal(result.data, 'Detalle del Documento');
        } else {
            showAlert('danger', 'Error', 'No se pudo cargar el documento');
        }
    } catch (error) {
        showAlert('danger', 'Error', error.message);
    }
}

async function sendDocumentToSunat(documentId) {
    showAlert('info', 'Enviando a SUNAT...', 'Por favor espere.');
    
    try {
        const response = await fetch(`${API_BASE}/sunat/send-bill/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                documento_id: documentId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', '¡Enviado a SUNAT!', 'Documento procesado exitosamente.');
            showResultModal(result.data, 'Resultado SUNAT');
            loadDocuments(); // Recargar lista
        } else {
            showAlert('warning', 'Respuesta SUNAT', result.error || 'Error en el envío');
        }
    } catch (error) {
        showAlert('danger', 'Error', error.message);
    }
}

// =============================
// FUNCIONES SUNAT
// =============================

async function testSunatConnection() {
    const container = document.getElementById('sunatTestResult');
    
    container.innerHTML = `
        <div class="text-center">
            <div class="spinner-border spinner-border-sm" role="status"></div>
            <span class="ms-2">Probando conexión...</span>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE}/sunat/test-connection/`);
        const result = await response.json();
        
        if (result.success) {
            container.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i>
                    <strong>Conexión exitosa</strong><br>
                    Método: ${result.data.connection_test.method}<br>
                    Duración: ${result.data.connection_test.duration_ms}ms
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    <strong>Conexión limitada</strong><br>
                    ${result.error || 'Modo simulación activo'}
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-x-circle"></i>
                <strong>Error de conexión</strong><br>
                ${error.message}
            </div>
        `;
    }
}

async function sendToSunat() {
    const documentId = document.getElementById('documentIdToSend').value;
    
    if (!documentId) {
        showAlert('warning', 'ID requerido', 'Por favor ingrese el ID del documento.');
        return;
    }
    
    await sendDocumentToSunat(documentId);
}

// =============================
// UTILIDADES UI
// =============================

function showAlert(type, title, message) {
    const container = document.getElementById('alertsContainer');
    const alertId = `alert-${Date.now()}`;
    
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" id="${alertId}">
            <i class="bi bi-${getAlertIcon(type)}"></i>
            <strong>${title}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle-fill',
        'danger': 'exclamation-triangle-fill',
        'warning': 'exclamation-triangle-fill',
        'info': 'info-circle-fill'
    };
    
    return icons[type] || 'info-circle-fill';
}

function showResultModal(data, title) {
    const modal = new bootstrap.Modal(document.getElementById('resultsModal'));
    const modalTitle = document.querySelector('#resultsModal .modal-title');
    const modalContent = document.getElementById('modalContent');
    
    modalTitle.textContent = title;
    
    // Formatear contenido según el tipo de datos
    let content = '';
    
    if (data.document) {
        // Resultado de generación de documento
        content = formatDocumentResult(data);
    } else if (data.results) {
        // Resultados de múltiples escenarios
        content = formatMultipleResults(data.results);
    } else if (data.scenario) {
        // Resultado de escenario individual
        content = formatScenarioResult(data);
    } else {
        // Datos genéricos
        content = `<pre class="bg-light p-3 rounded">${JSON.stringify(data, null, 2)}</pre>`;
    }
    
    modalContent.innerHTML = content;
    modal.show();
}

function formatDocumentResult(data) {
    const doc = data.document;
    const xmlInfo = data.xml_info;
    const totales = data.totales;
    
    return `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="bi bi-file-earmark-text"></i> Información del Documento</h6>
                <table class="table table-sm">
                    <tr><td><strong>Número:</strong></td><td>${doc.numero_completo}</td></tr>
                    <tr><td><strong>Estado:</strong></td><td><span class="badge bg-success">${doc.estado}</span></td></tr>
                    <tr><td><strong>Hash:</strong></td><td><code>${doc.hash}</code></td></tr>
                </table>
                
                <h6><i class="bi bi-shield-check"></i> Firma Digital</h6>
                <table class="table table-sm">
                    <tr><td><strong>Tipo:</strong></td><td><span class="badge bg-success">${xmlInfo.signature_type}</span></td></tr>
                    <tr><td><strong>RUC Fix:</strong></td><td><span class="badge bg-success">✅ Aplicado</span></td></tr>
                    <tr><td><strong>XML Limpio:</strong></td><td><span class="badge bg-success">✅ Sí</span></td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="bi bi-calculator"></i> Totales</h6>
                <table class="table table-sm">
                    <tr><td><strong>Subtotal:</strong></td><td>S/ ${totales.total_valor_venta.toFixed(2)}</td></tr>
                    <tr><td><strong>IGV:</strong></td><td>S/ ${totales.total_igv.toFixed(2)}</td></tr>
                    <tr><td><strong>Total:</strong></td><td><strong>S/ ${totales.total_precio_venta.toFixed(2)}</strong></td></tr>
                </table>
                
                <h6><i class="bi bi-gear"></i> Procesamiento</h6>
                <table class="table table-sm">
                    <tr><td><strong>Tiempo:</strong></td><td>${data.processing.processing_time_ms} ms</td></tr>
                    <tr><td><strong>Versión:</strong></td><td>${data.processing.generator_version}</td></tr>
                </table>
            </div>
        </div>
        
        <div class="mt-3">
            <h6><i class="bi bi-code-square"></i> XML Generado</h6>
            <div class="bg-light p-2 rounded" style="max-height: 300px; overflow-y: auto;">
                <pre><code>${escapeHtml(xmlInfo.xml_firmado.substring(0, 2000))}${xmlInfo.xml_firmado.length > 2000 ? '...' : ''}</code></pre>
            </div>
        </div>
    `;
}

function formatScenarioResult(data) {
    return `
        <div class="row">
            <div class="col-12">
                <h6><i class="bi bi-play-circle"></i> ${data.scenario.name}</h6>
                <p>${data.result.note}</p>
                
                <h6><i class="bi bi-list-task"></i> Datos de Prueba</h6>
                <pre class="bg-light p-3 rounded">${JSON.stringify(data.test_data, null, 2)}</pre>
                
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i>
                    <strong>Siguiente paso:</strong> ${data.instructions.next_step}
                </div>
            </div>
        </div>
    `;
}

function formatMultipleResults(results) {
    let html = '<h6><i class="bi bi-lightning"></i> Resultados de Todos los Escenarios</h6>';
    
    results.forEach((result, index) => {
        const icon = result.success ? 'check-circle-fill text-success' : 'x-circle-fill text-danger';
        html += `
            <div class="d-flex align-items-center mb-2">
                <i class="bi bi-${icon} me-2"></i>
                <strong>${result.scenario}</strong>
                <span class="badge ${result.success ? 'bg-success' : 'bg-danger'} ms-2">
                    ${result.success ? 'OK' : 'Error'}
                </span>
            </div>
        `;
    });
    
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}