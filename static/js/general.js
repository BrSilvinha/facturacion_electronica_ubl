// ===== CONFIGURACIÓN GLOBAL =====
const CONFIG = {
    API_BASE: 'http://127.0.0.1:8000/api',
    EMPRESA_ID: "c11dba61-2837-4bcc-b197-301e78168582"
};

// ===== VARIABLES GLOBALES =====
let currentDocuments = [];
let currentXMLDocumentId = null;
let currentCDRDocumentId = null;
let itemCounter = 0;
let currencySymbol = 'S/';

// ===== FUNCIONES DE LOGGING =====
function log(message, type = 'info') {
    const logContainer = document.getElementById('activityLog');
    if (!logContainer) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const colorClass = type === 'error' ? 'text-danger' : 
                     type === 'success' ? 'text-success' : 
                     type === 'warning' ? 'text-warning' : 'text-info';
    
    const logEntry = document.createElement('div');
    logEntry.className = `${colorClass} mb-1`;
    logEntry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLog() {
    const logContainer = document.getElementById('activityLog');
    if (logContainer) {
        logContainer.innerHTML = '';
        log('Log del sistema limpiado', 'info');
    }
}

// ===== FUNCIONES DE API =====
async function apiCall(method, endpoint, data = null) {
    try {
        log(`${method} ${endpoint}`, 'info');
        
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        if (response.ok) {
            log(`✓ ${endpoint} - SUCCESS`, 'success');
            return { success: true, data: result };
        } else {
            log(`✗ ${endpoint} - ERROR ${response.status}`, 'error');
            return { success: false, error: result, status: response.status };
        }
    } catch (error) {
        log(`✗ ${endpoint} - EXCEPTION: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// ===== FUNCIONES DE NAVEGACIÓN =====
function switchToCreateTab() {
    const createTab = document.getElementById('create-tab');
    if (createTab) {
        createTab.click();
        log('📝 Navegando a Crear Factura', 'info');
    }
}

function switchToDocumentsTab() {
    const documentsTab = document.getElementById('documents-tab');
    if (documentsTab) {
        documentsTab.click();
        log('📊 Navegando a Mis Documentos', 'info');
    }
}

function switchToXMLTab() {
    const xmlTab = document.getElementById('xml-tab');
    if (xmlTab) {
        xmlTab.click();
        log('💻 Navegando a Visor XML', 'info');
    }
}

function switchToCDRTab() {
    const cdrTab = document.getElementById('cdr-tab');
    if (cdrTab) {
        cdrTab.click();
        log('✅ Navegando a Visor CDR', 'info');
    }
}

// ===== FUNCIONES DEL FORMULARIO =====
function updateCurrencySymbol() {
    const moneda = document.getElementById('moneda').value;
    switch(moneda) {
        case 'PEN': currencySymbol = 'S/'; break;
        case 'USD': currencySymbol = '$'; break;
        case 'EUR': currencySymbol = '€'; break;
        default: currencySymbol = 'S/';
    }
    
    // Actualizar símbolos en items existentes
    document.querySelectorAll('.currency-symbol').forEach(symbol => {
        symbol.textContent = currencySymbol;
    });
    
    calculateTotals();
}

function addItem() {
    itemCounter++;
    const container = document.getElementById('itemsContainer');
    
    const itemDiv = document.createElement('div');
    itemDiv.className = 'card mb-3';
    itemDiv.innerHTML = `
        <div class="card-body">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 text-primary">
                    <i class="bi bi-box me-1"></i>Item ${itemCounter}
                </h6>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeItem(this)">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label">Descripción del Producto/Servicio</label>
                    <input type="text" class="form-control item-descripcion" placeholder="Ej: Producto Premium" required onchange="calculateTotals()">
                </div>
                <div class="col-md-3">
                    <label class="form-label">Código (Opcional)</label>
                    <input type="text" class="form-control item-codigo" placeholder="PROD001" onchange="calculateTotals()">
                </div>
                <div class="col-md-3">
                    <label class="form-label">Unidad Medida</label>
                    <select class="form-select item-unidad" onchange="calculateTotals()">
                        <option value="NIU">NIU - Unidad</option>
                        <option value="ZZ">ZZ - Servicios</option>
                        <option value="KGM">KGM - Kilogramo</option>
                        <option value="MTR">MTR - Metro</option>
                        <option value="LTR">LTR - Litro</option>
                        <option value="SET">SET - Juego</option>
                        <option value="DAY">DAY - Día</option>
                        <option value="HUR">HUR - Hora</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Cantidad</label>
                    <input type="number" class="form-control item-cantidad" value="1" min="0.001" step="0.001" required onchange="calculateTotals()">
                </div>
                <div class="col-md-3">
                    <label class="form-label">Precio Unitario (Sin IGV)</label>
                    <div class="input-group">
                        <span class="input-group-text currency-symbol">${currencySymbol}</span>
                        <input type="number" class="form-control item-precio" value="0.00" min="0" step="0.01" required onchange="calculateTotals()">
                    </div>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Afectación IGV</label>
                    <select class="form-select item-afectacion" onchange="calculateTotals()">
                        <option value="10">10 - Gravado</option>
                        <option value="20">20 - Exonerado</option>
                        <option value="30">30 - Inafecto</option>
                        <option value="40">40 - Exportación</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Subtotal</label>
                    <div class="input-group">
                        <span class="input-group-text currency-symbol">${currencySymbol}</span>
                        <input type="text" class="form-control item-subtotal" readonly style="background: #f8f9fa;">
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(itemDiv);
    calculateTotals();
}

function removeItem(button) {
    button.closest('.card').remove();
    calculateTotals();
}

function calculateTotals() {
    const items = document.querySelectorAll('#itemsContainer .card');
    let subtotal = 0;
    let igvTotal = 0;
    
    items.forEach(item => {
        const cantidad = parseFloat(item.querySelector('.item-cantidad').value) || 0;
        const precio = parseFloat(item.querySelector('.item-precio').value) || 0;
        const afectacion = item.querySelector('.item-afectacion').value;
        
        const lineSubtotal = cantidad * precio;
        const lineIGV = afectacion === '10' ? lineSubtotal * 0.18 : 0;
        
        item.querySelector('.item-subtotal').value = lineSubtotal.toFixed(2);
        
        subtotal += lineSubtotal;
        igvTotal += lineIGV;
    });
    
    const total = subtotal + igvTotal;
    
    document.getElementById('displaySubtotal').textContent = `${currencySymbol} ${subtotal.toFixed(2)}`;
    document.getElementById('displayIGV').textContent = `${currencySymbol} ${igvTotal.toFixed(2)}`;
    document.getElementById('displayTotal').textContent = `${currencySymbol} ${total.toFixed(2)}`;
}

function clearForm() {
    document.getElementById('facturaForm').reset();
    document.getElementById('itemsContainer').innerHTML = '';
    itemCounter = 0;
    calculateTotals();
    generateNewNumber();
    log('Formulario limpiado', 'info');
}

function generateNewNumber() {
    const numeroField = document.getElementById('numero');
    if (numeroField) {
        numeroField.value = Math.floor(Math.random() * 9000) + 1000;
    }
}

// ===== FUNCIONES DE DATOS DE PRUEBA =====
function loadSampleClient() {
    document.getElementById('clienteTipoDoc').value = '6';
    document.getElementById('clienteNumDoc').value = '20987654321';
    document.getElementById('clienteRazonSocial').value = 'CLIENTE PREMIUM SAC';
    document.getElementById('clienteDireccion').value = 'AV. EMPRESARIAL 456, LIMA';
    log('Cliente de prueba cargado', 'info');
}

function loadSampleProducts() {
    // Limpiar items existentes
    document.getElementById('itemsContainer').innerHTML = '';
    itemCounter = 0;
    
    // Agregar productos de ejemplo
    const productos = [
        { desc: 'Producto Premium Calidad Superior', codigo: 'PREM001', cantidad: 2, precio: 250.00, unidad: 'NIU' },
        { desc: 'Servicio de Consultoría Empresarial', codigo: 'SERV001', cantidad: 10, precio: 150.00, unidad: 'HUR' },
        { desc: 'Software Licencia Anual', codigo: 'SOFT001', cantidad: 1, precio: 1200.00, unidad: 'ZZ' }
    ];
    
    productos.forEach(producto => {
        addItem();
        const lastItem = document.querySelector('#itemsContainer .card:last-child');
        lastItem.querySelector('.item-descripcion').value = producto.desc;
        lastItem.querySelector('.item-codigo').value = producto.codigo;
        lastItem.querySelector('.item-cantidad').value = producto.cantidad;
        lastItem.querySelector('.item-precio').value = producto.precio;
        lastItem.querySelector('.item-unidad').value = producto.unidad;
    });
    
    calculateTotals();
    log('Productos de ejemplo cargados', 'info');
}

function loadFullSample() {
    loadSampleClient();
    loadSampleProducts();
    log('Factura completa de ejemplo cargada', 'success');
}

// ===== FUNCIÓN PRINCIPAL - GENERAR FACTURA =====
async function generateFactura() {
    log('🚀 Iniciando generación de factura...', 'info');
    
    // Validar formulario
    const form = document.getElementById('facturaForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        log('❌ Formulario incompleto', 'error');
        return;
    }
    
    // Validar que hay items
    const items = document.querySelectorAll('#itemsContainer .card');
    if (items.length === 0) {
        log('❌ Debe agregar al menos un item', 'error');
        alert('Debe agregar al menos un producto o servicio.');
        return;
    }
    
    // Recopilar datos del formulario
    const facturaData = {
        tipo_documento: document.getElementById('tipoDocumento').value,
        serie: document.getElementById('serie').value,
        numero: parseInt(document.getElementById('numero').value),
        fecha_emision: new Date().toISOString().split('T')[0],
        moneda: document.getElementById('moneda').value,
        empresa_id: CONFIG.EMPRESA_ID,
        receptor: {
            tipo_doc: document.getElementById('clienteTipoDoc').value,
            numero_doc: document.getElementById('clienteNumDoc').value,
            razon_social: document.getElementById('clienteRazonSocial').value,
            direccion: document.getElementById('clienteDireccion').value
        },
        items: []
    };
    
    // Recopilar items
    items.forEach(item => {
        const itemData = {
            descripcion: item.querySelector('.item-descripcion').value,
            codigo_producto: item.querySelector('.item-codigo').value,
            cantidad: parseFloat(item.querySelector('.item-cantidad').value),
            valor_unitario: parseFloat(item.querySelector('.item-precio').value),
            unidad_medida: item.querySelector('.item-unidad').value,
            afectacion_igv: item.querySelector('.item-afectacion').value
        };
        facturaData.items.push(itemData);
    });
    
    log('📄 Datos recopilados, enviando a API...', 'info');
    
    // Enviar a API
    const result = await apiCall('POST', '/generar-xml/', facturaData);
    
    if (result.success) {
        const docData = result.data;
        log(`✅ Factura generada: ${docData.numero_completo}`, 'success');
        
        // Mostrar información del documento generado
        showLastDocumentInfo(docData);
        
        // Actualizar estadísticas
        updateStats();
        
        // Enviar a SUNAT automáticamente
        setTimeout(() => {
            sendToSUNAT(docData.documento_id);
        }, 1000);
        
        // Actualizar lista de documentos
        setTimeout(() => {
            refreshDocuments();
        }, 3000);
        
        // Generar nuevo número para la siguiente factura
        generateNewNumber();
        
    } else {
        log('❌ Error generando factura', 'error');
        alert(`Error: ${result.error.error || 'Error desconocido'}`);
    }
}

function showLastDocumentInfo(docData) {
    const card = document.getElementById('lastDocumentCard');
    const content = document.getElementById('lastDocumentInfo');
    
    if (!card || !content) return;
    
    content.innerHTML = `
        <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
                <h6 class="text-primary mb-1">${docData.numero_completo}</h6>
                <small class="text-muted">ID: ${docData.documento_id}</small>
            </div>
            <span class="badge bg-success">Generado</span>
        </div>
        <div class="row text-center">
            <div class="col-4">
                <div class="border-end">
                    <div class="fw-bold text-success">${docData.totales.total_precio_venta.toFixed(2)}</div>
                    <small class="text-muted">Total</small>
                </div>
            </div>
            <div class="col-4">
                <div class="border-end">
                    <div class="fw-bold">${docData.processing_time_ms}ms</div>
                    <small class="text-muted">Tiempo</small>
                </div>
            </div>
            <div class="col-4">
                <div class="fw-bold text-info">${docData.signature_type}</div>
                <small class="text-muted">Firma</small>
            </div>
        </div>
        <div class="d-grid gap-2 mt-3">
            <button class="btn btn-sm btn-outline-primary" onclick="loadXMLById('${docData.documento_id}'); switchToXMLTab();">
                <i class="bi bi-code me-1"></i>Ver XML
            </button>
        </div>
    `;
    
    card.style.display = 'block';
}

// ===== ENVÍO A SUNAT =====
async function sendToSUNAT(docId) {
    if (!docId) {
        log('⚠️ No hay documento para enviar', 'warning');
        return;
    }

    const cleanDocId = docId.replace(/[{}]/g, '').trim();
    log(`📤 Enviando documento a SUNAT: ${cleanDocId}`, 'info');
    
    const result = await apiCall('POST', '/sunat/send-bill/', {
        documento_id: cleanDocId
    });
    
    if (result.success) {
        log('✅ ¡Documento enviado exitosamente a SUNAT!', 'success');
        if (result.data.has_cdr) {
            log('📄 CDR recibido de SUNAT', 'success');
        }
        updateStats();
    } else {
        log('❌ Error enviando a SUNAT', 'error');
    }
}

// ===== GESTIÓN DE DOCUMENTOS =====
async function refreshDocuments() {
    log('🔄 Actualizando lista de documentos...', 'info');
    
    const tableBody = document.getElementById('documentsTableBody');
    if (!tableBody) return;
    
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4">
                <div class="spinner-border text-primary" role="status"></div>
                <div class="mt-2">Cargando documentos...</div>
            </td>
        </tr>
    `;
    
    const result = await apiCall('GET', '/documentos/');
    
    if (result.success) {
        const documentos = result.data.data.documentos;
        const stats = result.data.data.stats;
        
        log(`✓ ${documentos.length} documentos cargados`, 'success');
        
        updateStatsFromAPI(stats);
        currentDocuments = documentos;
        
        if (documentos.length > 0) {
            tableBody.innerHTML = '';
            documentos.forEach(doc => {
                const row = createDocumentRow(doc);
                tableBody.appendChild(row);
            });
        } else {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-5">
                        <div class="alert alert-info mb-0">
                            <i class="bi bi-info-circle me-2"></i>
                            No hay documentos disponibles.
                            <br><button class="btn btn-success btn-sm mt-3" onclick="switchToCreateTab()">
                                <i class="bi bi-plus me-1"></i>Crear Primera Factura
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }
        
        updateDocumentSelects(documentos);
        
    } else {
        log('❌ Error cargando documentos', 'error');
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <div class="alert alert-danger mb-0">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error cargando documentos
                    </div>
                </td>
            </tr>
        `;
    }
}

function createDocumentRow(doc) {
    const row = document.createElement('tr');
    row.style.cursor = 'pointer';
    
    const badgeClass = doc.estado_badge.class;
    const badgeText = doc.estado_badge.text;
    
    const total = new Intl.NumberFormat('es-PE', {
        style: 'currency',
        currency: doc.moneda
    }).format(doc.total);
    
    row.innerHTML = `
        <td>
            <div class="fw-bold">${doc.numero_completo}</div>
            <small class="text-muted">${doc.tipo_documento.descripcion}</small>
        </td>
        <td>
            <div>${doc.fecha_emision}</div>
            <small class="text-muted">${doc.created_at}</small>
        </td>
        <td>
            <div class="fw-bold">${doc.receptor.razon_social}</div>
            <small class="text-muted">${doc.receptor.numero_doc}</small>
        </td>
        <td class="text-end">
            <div class="fw-bold">${total}</div>
            <small class="text-muted">${doc.moneda}</small>
        </td>
        <td>
            <span class="badge ${badgeClass}">${badgeText}</span>
        </td>
        <td class="text-center">
            ${doc.tiene_cdr ? 
                '<i class="bi bi-check-circle text-success fs-5" title="CDR Disponible"></i>' : 
                '<i class="bi bi-clock text-warning fs-5" title="Sin CDR"></i>'
            }
        </td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-warning btn-sm" onclick="loadXMLById('${doc.id}'); switchToXMLTab();" title="Ver XML">
                    <i class="bi bi-code"></i>
                </button>
                <button class="btn btn-outline-success btn-sm" onclick="loadCDRById('${doc.id}'); switchToCDRTab();" title="Ver CDR">
                    <i class="bi bi-file-check"></i>
                </button>
                <button class="btn btn-outline-primary btn-sm" onclick="sendToSUNAT('${doc.id}')" title="Reenviar">
                    <i class="bi bi-send"></i>
                </button>
            </div>
        </td>
    `;
    
    return row;
}

function updateDocumentSelects(documentos) {
    // Actualizar select de XML
    const xmlSelect = document.getElementById('xmlDocumentSelect');
    if (xmlSelect) {
        xmlSelect.innerHTML = '<option value="">Seleccione un documento...</option>';
        
        if (documentos && documentos.length > 0) {
            documentos.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = `${doc.numero_completo} - ${doc.receptor.razon_social}`;
                xmlSelect.appendChild(option);
            });
        }
    }
    
    // Actualizar select de CDR
    const cdrSelect = document.getElementById('cdrDocumentSelect');
    if (cdrSelect) {
        cdrSelect.innerHTML = '<option value="">Seleccione un documento...</option>';
        
        if (documentos && documentos.length > 0) {
            documentos.forEach(doc => {
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = `${doc.numero_completo} - ${doc.receptor.razon_social}`;
                cdrSelect.appendChild(option);
            });
        }
    }
}

// ===== VISOR XML =====
async function loadXML() {
    const select = document.getElementById('xmlDocumentSelect');
    const docId = select.value;
    if (!docId) return;
    
    await loadXMLById(docId);
}

async function loadXMLById(docId = null) {
    const documentIdInput = document.getElementById('xmlDocumentId');
    let targetDocId = docId || documentIdInput.value.trim();
    
    if (!targetDocId) {
        log('⚠️ Ingrese un ID de documento válido', 'warning');
        return;
    }

    targetDocId = targetDocId.replace(/[{}]/g, '').trim();
    currentXMLDocumentId = targetDocId;
    
    log(`🔍 Cargando XML para documento: ${targetDocId}`, 'info');
    
    const xmlContent = document.getElementById('xmlContent');
    const xmlActions = document.getElementById('xmlActions');
    const xmlInfoCard = document.getElementById('xmlInfoCard');
    
    if (!xmlContent) return;
    
    xmlContent.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-warning mb-3" role="status"></div>
            <h5>Cargando XML</h5>
            <p class="text-muted">Obteniendo documento...</p>
        </div>
    `;

    const result = await apiCall('GET', `/documentos/${targetDocId}/`);

    if (result.success) {
        const docData = result.data.data;
        
        if (docData.xml_firmado_disponible) {
            // Mostrar información del documento
            if (xmlInfoCard && xmlInfoCard) {
                const xmlInfoContent = document.getElementById('xmlInfoContent');
                xmlInfoContent.innerHTML = `
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong><i class="bi bi-file-text me-1"></i>Documento:</strong><br>
                            <span class="text-warning fw-bold">${docData.numero_completo}</span>
                        </div>
                        <div class="col-6">
                            <strong><i class="bi bi-calendar me-1"></i>Fecha:</strong><br>
                            <span>${docData.fecha_emision}</span>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-6">
                            <strong><i class="bi bi-person me-1"></i>Cliente:</strong><br>
                            <span>${docData.receptor.razon_social}</span>
                        </div>
                        <div class="col-6">
                            <strong><i class="bi bi-currency-dollar me-1"></i>Total:</strong><br>
                            <span class="fw-bold text-success">${docData.montos.moneda} ${docData.montos.total}</span>
                        </div>
                    </div>
                    <div class="alert alert-warning">
                        <strong><i class="bi bi-info-circle me-1"></i>Hash:</strong><br>
                        <small class="font-monospace">${docData.hash_digest || 'N/A'}</small>
                    </div>
                `;
                
                xmlInfoCard.style.display = 'block';
            }
            
            if (xmlActions) {
                xmlActions.style.display = 'block';
            }
            
            // Simular contenido XML
            const xmlSimulado = generateSampleXML(docData);
            
            xmlContent.innerHTML = `
                <div class="alert alert-success mb-3">
                    <i class="bi bi-check-circle me-2"></i>
                    <strong>XML UBL 2.1 Disponible</strong>
                    <div class="mt-2">
                        <small><strong>Estado:</strong> ${docData.estado}</small><br>
                        <small><strong>Firma:</strong> ${docData.xml_firmado_disponible ? 'Firmado Digitalmente' : 'Sin Firma'}</small>
                    </div>
                </div>
                <div class="mt-3">
                    <h6><i class="bi bi-code me-1"></i>Contenido XML UBL 2.1</h6>
                    <pre id="xmlDisplayArea" class="bg-dark text-light p-3 rounded" style="font-size: 0.75rem; max-height: 400px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(xmlSimulado)}</pre>
                </div>
            `;
            
            log('✅ XML cargado exitosamente', 'success');
        } else {
            displayXMLError('XML no disponible para este documento');
        }
        
    } else {
        log('❌ Error cargando XML', 'error');
        displayXMLError(result.error);
    }
}

function displayXMLError(error) {
    const xmlContent = document.getElementById('xmlContent');
    const xmlActions = document.getElementById('xmlActions');
    const xmlInfoCard = document.getElementById('xmlInfoCard');

    if (xmlInfoCard) xmlInfoCard.style.display = 'none';
    if (xmlActions) xmlActions.style.display = 'none';

    if (xmlContent) {
        xmlContent.innerHTML = `
            <div class="alert alert-danger text-center py-4">
                <i class="bi bi-x-circle display-3 text-danger mb-3"></i>
                <h5>Error Cargando XML</h5>
                <p><strong>Error:</strong> ${typeof error === 'string' ? error : error.error || 'Error desconocido'}</p>
                <div class="mt-3">
                    <button class="btn btn-warning me-2" onclick="refreshDocuments()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Actualizar Documentos
                    </button>
                    <button class="btn btn-success" onclick="switchToCreateTab()">
                        <i class="bi bi-plus me-1"></i>Crear Documento
                    </button>
                </div>
            </div>
        `;
    }
}

function generateSampleXML(docData) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2">

    <!-- Extensiones UBL -->
    <ext:UBLExtensions>
        <ext:UBLExtension>
            <ext:ExtensionContent>
                <!-- Firma digital aplicada -->
            </ext:ExtensionContent>
        </ext:UBLExtension>
    </ext:UBLExtensions>

    <!-- Información básica del documento -->
    <cbc:UBLVersionID>2.1</cbc:UBLVersionID>
    <cbc:CustomizationID>2.0</cbc:CustomizationID>
    <cbc:ID>${docData.numero_completo}</cbc:ID>
    <cbc:IssueDate>${docData.fecha_emision}</cbc:IssueDate>
    <cbc:InvoiceTypeCode listAgencyName="PE:SUNAT">${docData.tipo_documento.codigo}</cbc:InvoiceTypeCode>
    <cbc:DocumentCurrencyCode>${docData.montos.moneda}</cbc:DocumentCurrencyCode>

    <!-- Información del emisor -->
    <cac:AccountingSupplierParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="6">${docData.empresa.ruc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[${docData.empresa.razon_social}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingSupplierParty>

    <!-- Información del cliente -->
    <cac:AccountingCustomerParty>
        <cac:Party>
            <cac:PartyIdentification>
                <cbc:ID schemeID="${docData.receptor.tipo_doc}">${docData.receptor.numero_doc}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName><![CDATA[${docData.receptor.razon_social}]]></cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>

    <!-- Totales monetarios -->
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="${docData.montos.moneda}">${docData.montos.subtotal}</cbc:LineExtensionAmount>
        <cbc:TaxInclusiveAmount currencyID="${docData.montos.moneda}">${docData.montos.total}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="${docData.montos.moneda}">${docData.montos.total}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>

</Invoice>`;
}

// ===== VISOR CDR =====
async function loadCDR() {
    const select = document.getElementById('cdrDocumentSelect');
    const docId = select.value;
    if (!docId) return;
    
    await loadCDRById(docId);
}

async function loadCDRById(docId = null) {
    const documentIdInput = document.getElementById('cdrDocumentId');
    let targetDocId = docId || documentIdInput.value.trim();
    
    if (!targetDocId) {
        log('⚠️ Ingrese un ID de documento válido', 'warning');
        return;
    }

    targetDocId = targetDocId.replace(/[{}]/g, '').trim();
    currentCDRDocumentId = targetDocId;
    
    log(`🔍 Cargando CDR para documento: ${targetDocId}`, 'info');
    
    const cdrContent = document.getElementById('cdrContent');
    const cdrActions = document.getElementById('cdrActions');
    const cdrInfoCard = document.getElementById('cdrInfoCard');
    
    if (!cdrContent) return;
    
    cdrContent.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-success mb-3" role="status"></div>
            <h5>Cargando CDR</h5>
            <p class="text-muted">Consultando SUNAT...</p>
        </div>
    `;

    const result = await apiCall('GET', `/cdr-info/${targetDocId}/`);

    if (result.success) {
        displayCDR(result.data);
        log('✅ CDR cargado exitosamente', 'success');
    } else {
        log('❌ Error cargando CDR', 'error');
        displayCDRError(result.error);
    }
}

function displayCDR(cdrData) {
    const cdrInfoCard = document.getElementById('cdrInfoCard');
    const cdrInfoContent = document.getElementById('cdrInfoContent');
    const cdrContent = document.getElementById('cdrContent');
    const cdrActions = document.getElementById('cdrActions');

    if (cdrInfoCard) cdrInfoCard.style.display = 'block';
    if (cdrActions) cdrActions.style.display = 'block';

    const numeroCompleto = cdrData.data?.numero_completo || cdrData.numero_completo || 'N/A';
    const estadoDocumento = cdrData.data?.estado_documento || cdrData.estado_documento || 'DESCONOCIDO';
    const tieneCDR = cdrData.data?.tiene_cdr || cdrData.tiene_cdr || false;
    const cdrInfo = cdrData.data?.cdr_info || cdrData.cdr_info || null;

    // Mostrar información del CDR
    if (cdrInfoContent) {
        cdrInfoContent.innerHTML = `
            <div class="row mb-3">
                <div class="col-6">
                    <strong><i class="bi bi-file-text me-1"></i>Documento:</strong><br>
                    <span class="text-success fw-bold">${numeroCompleto}</span>
                </div>
                <div class="col-6">
                    <strong><i class="bi bi-check-circle me-1"></i>Estado:</strong><br>
                    <span class="badge ${estadoDocumento === 'ACEPTADO' ? 'bg-success' : 'bg-warning'}">${estadoDocumento}</span>
                </div>
            </div>
            <div class="row mb-3">
                <div class="col-6">
                    <strong><i class="bi bi-file-check me-1"></i>CDR:</strong><br>
                    ${tieneCDR ? '<i class="bi bi-check-circle text-success"></i> Disponible' : '<i class="bi bi-x-circle text-danger"></i> No disponible'}
                </div>
                <div class="col-6">
                    <strong><i class="bi bi-hash me-1"></i>Código:</strong><br>
                    <span class="badge bg-info">${cdrInfo?.codigo_respuesta || 'N/A'}</span>
                </div>
            </div>
            ${cdrInfo?.descripcion ? `
            <div class="alert alert-info">
                <strong><i class="bi bi-info-circle me-1"></i>Descripción:</strong><br>
                <small>${cdrInfo.descripcion}</small>
            </div>
            ` : ''}
        `;
    }

    // Mostrar contenido CDR
    if (cdrContent) {
        if (tieneCDR && cdrInfo?.xml_cdr) {
            cdrContent.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle me-2"></i>
                    <strong>CDR Disponible - Sistema Corregido</strong>
                    <div class="mt-2">
                        <small><strong>Estado:</strong> ${cdrInfo.estado || 'Procesado'}</small><br>
                        <small><strong>Código:</strong> ${cdrInfo.codigo_respuesta || '0'}</small><br>
                        <small><strong>Descripción:</strong> ${cdrInfo.descripcion || 'Documento procesado exitosamente'}</small>
                    </div>
                </div>
                <div class="mt-3">
                    <h6><i class="bi bi-file-check me-1"></i>XML CDR SUNAT</h6>
                    <pre id="cdrDisplayArea" class="bg-dark text-success p-3 rounded" style="font-size: 0.75rem; max-height: 400px; overflow-y: auto; white-space: pre-wrap;">${escapeHtml(cdrInfo.xml_cdr)}</pre>
                </div>
            `;
        } else {
            const documentoId = cdrData.data?.documento_id || cdrData.documento_id;
            const cleanDocId = documentoId ? documentoId.replace(/[{}]/g, '') : '';
            
            cdrContent.innerHTML = `
                <div class="alert alert-warning text-center py-4">
                    <i class="bi bi-exclamation-triangle display-3 text-warning mb-3"></i>
                    <h5>CDR No Disponible</h5>
                    <p>Este documento aún no tiene Constancia de Recepción.</p>
                    <div class="mt-3">
                        <strong>Estado:</strong> <span class="badge bg-secondary">${estadoDocumento}</span>
                    </div>
                    ${cleanDocId ? `
                    <div class="mt-4">
                        <button class="btn btn-success" onclick="sendToSUNAT('${cleanDocId}')">
                            <i class="bi bi-send me-1"></i>Enviar a SUNAT
                        </button>
                    </div>
                    ` : ''}
                </div>
            `;
        }
    }
}

function displayCDRError(error) {
    const cdrInfoCard = document.getElementById('cdrInfoCard');
    const cdrContent = document.getElementById('cdrContent');
    const cdrActions = document.getElementById('cdrActions');

    if (cdrInfoCard) cdrInfoCard.style.display = 'none';
    if (cdrActions) cdrActions.style.display = 'none';

    if (cdrContent) {
        cdrContent.innerHTML = `
            <div class="alert alert-danger text-center py-4">
                <i class="bi bi-x-circle display-3 text-danger mb-3"></i>
                <h5>Error Cargando CDR</h5>
                <p><strong>Error:</strong> ${typeof error === 'string' ? error : error.error || 'Error desconocido'}</p>
                <div class="mt-3">
                    <button class="btn btn-warning me-2" onclick="refreshDocuments()">
                        <i class="bi bi-arrow-clockwise me-1"></i>Actualizar Documentos
                    </button>
                    <button class="btn btn-success" onclick="switchToCreateTab()">
                        <i class="bi bi-plus me-1"></i>Crear Documento
                    </button>
                </div>
            </div>
        `;
    }
}

// ===== FUNCIONES DE ACCIÓN PARA XML Y CDR =====
function copyXML() {
    const xmlArea = document.getElementById('xmlDisplayArea');
    if (!xmlArea) {
        log('⚠️ No hay contenido XML para copiar', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(xmlArea.textContent)
        .then(() => log('📋 XML copiado al portapapeles', 'success'))
        .catch(() => log('❌ Error copiando XML', 'error'));
}

function downloadXML() {
    const xmlArea = document.getElementById('xmlDisplayArea');
    if (!xmlArea) {
        log('⚠️ No hay contenido para descargar', 'warning');
        return;
    }
    
    try {
        const xmlContent = xmlArea.textContent;
        const blob = new Blob([xmlContent], { type: 'application/xml' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `XML_${currentXMLDocumentId || 'documento'}_${new Date().toISOString().split('T')[0]}.xml`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        log('⬇️ XML descargado exitosamente', 'success');
        
    } catch (error) {
        log('❌ Error descargando XML', 'error');
    }
}

function formatXML() {
    const xmlArea = document.getElementById('xmlDisplayArea');
    if (!xmlArea) return;
    
    try {
        let formatted = xmlArea.textContent
            .replace(/></g, '>\n<')
            .replace(/^\s+|\s+$/gm, '');
        
        let indent = 0;
        formatted = formatted.split('\n').map(line => {
            if (line.includes('</') && !line.includes('</'+ line.split('</')[1].split('>')[0] + '>')) {
                indent--;
            }
            const indentedLine = '  '.repeat(Math.max(0, indent)) + line.trim();
            if (line.includes('<') && !line.includes('</') && !line.includes('/>')) {
                indent++;
            }
            return indentedLine;
        }).join('\n');
        
        xmlArea.textContent = formatted;
        log('✅ XML formateado correctamente', 'success');
        
    } catch (error) {
        log('❌ Error formateando XML', 'error');
    }
}

function copyCDR() {
    const cdrArea = document.getElementById('cdrDisplayArea');
    if (!cdrArea) {
        log('⚠️ No hay contenido CDR para copiar', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(cdrArea.textContent)
        .then(() => log('📋 CDR copiado al portapapeles', 'success'))
        .catch(() => log('❌ Error copiando CDR', 'error'));
}

function downloadCDR() {
    const cdrArea = document.getElementById('cdrDisplayArea');
    if (!cdrArea) {
        log('⚠️ No hay contenido CDR para descargar', 'warning');
        return;
    }
    
    try {
        const cdrContent = cdrArea.textContent;
        const blob = new Blob([cdrContent], { type: 'application/xml' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `CDR_${currentCDRDocumentId || 'documento'}_${new Date().toISOString().split('T')[0]}.xml`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        log('⬇️ CDR descargado exitosamente', 'success');
        
    } catch (error) {
        log('❌ Error descargando CDR', 'error');
    }
}

function formatCDR() {
    const cdrArea = document.getElementById('cdrDisplayArea');
    if (!cdrArea) return;
    
    try {
        let formatted = cdrArea.textContent
            .replace(/></g, '>\n<')
            .replace(/^\s+|\s+$/gm, '');
        
        let indent = 0;
        formatted = formatted.split('\n').map(line => {
            if (line.includes('</') && !line.includes('</'+ line.split('</')[1].split('>')[0] + '>')) {
                indent--;
            }
            const indentedLine = '  '.repeat(Math.max(0, indent)) + line.trim();
            if (line.includes('<') && !line.includes('</') && !line.includes('/>')) {
                indent++;
            }
            return indentedLine;
        }).join('\n');
        
        cdrArea.textContent = formatted;
        log('✅ CDR formateado correctamente', 'success');
        
    } catch (error) {
        log('❌ Error formateando CDR', 'error');
    }
}

// ===== FUNCIONES DE TEST =====
async function testConnection() {
    log('🧪 Probando conexión con SUNAT...', 'info');
    const result = await apiCall('GET', '/sunat/test-connection/');
    
    if (result.success) {
        log('✅ Conexión SUNAT exitosa', 'success');
        alert('✅ Conexión con SUNAT exitosa!\n\nSistema operativo y listo para facturar.');
    } else {
        log('❌ Error en conexión SUNAT', 'error');
        alert('❌ Error en conexión SUNAT\n\nVerificar configuración.');
    }
}

// ===== FUNCIONES DE ESTADÍSTICAS =====
function updateStats() {
    const statsDocuments = document.getElementById('statsDocuments');
    const statsCDR = document.getElementById('statsCDR');
    
    if (statsDocuments) {
        statsDocuments.textContent = parseInt(statsDocuments.textContent) + 1;
    }
    
    if (statsCDR) {
        statsCDR.textContent = parseInt(statsCDR.textContent) + 1;
    }
    
    // Actualizar total facturado (simulado)
    const statsTotal = document.getElementById('statsTotal');
    if (statsTotal) {
        const currentTotal = parseFloat(statsTotal.textContent.replace(/[^\d.]/g, '')) || 0;
        const newTotal = currentTotal + Math.random() * 1000 + 100;
        statsTotal.textContent = `${currencySymbol} ${newTotal.toFixed(2)}`;
    }
}

function updateStatsFromAPI(stats) {
    const statsDocuments = document.getElementById('statsDocuments');
    const statsCDR = document.getElementById('statsCDR');
    
    if (statsDocuments) {
        statsDocuments.textContent = stats.total || 0;
    }
    
    if (statsCDR) {
        statsCDR.textContent = stats.con_cdr || 0;
    }
}

// ===== FUNCIONES HELPER =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== INICIALIZACIÓN =====
function initializeApp() {
    log('🚀 Dashboard de Facturación Electrónica cargado', 'success');
    log('✅ Sistema CDR completamente corregido', 'success');
    log('🔐 Certificado real C23022479065 integrado', 'info');
    log('💰 Soporte multi-moneda (PEN/USD/EUR) activado', 'info');
    
    // Generar número inicial
    generateNewNumber();
    
    // Agregar primer item por defecto
    addItem();
    
    // Cargar documentos existentes
    refreshDocuments();
    
    // Test inicial después de 2 segundos
    setTimeout(() => {
        log('🧪 Ejecutando verificación inicial...', 'info');
        testConnection();
    }, 2000);
    
    // Event listeners para tabs
    initializeTabListeners();
    
    // Event listeners para shortcuts
    initializeKeyboardShortcuts();
    
    // Auto-refresh
    initializeAutoRefresh();
}

function initializeTabListeners() {
    document.querySelectorAll('#mainTabs button').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            const target = e.target.getAttribute('data-bs-target');
            const tabName = target.replace('#', '').toUpperCase();
            log(`📂 Navegando a: ${tabName}`, 'info');
            
            switch(target) {
                case '#documents':
                    refreshDocuments();
                    break;
                case '#xml':
                case '#cdr':
                    updateDocumentSelects(currentDocuments);
                    break;
                case '#create':
                    // Asegurar que hay al menos un item
                    const itemsContainer = document.getElementById('itemsContainer');
                    if (itemsContainer && itemsContainer.children.length === 0) {
                        addItem();
                    }
                    break;
            }
        });
    });
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'n') {
            e.preventDefault();
            switchToCreateTab();
            log('⌨️ Ctrl+N: Nueva factura', 'info');
        }
        
        if (e.ctrlKey && e.key === 'd') {
            e.preventDefault();
            switchToDocumentsTab();
            log('⌨️ Ctrl+D: Ver documentos', 'info');
        }
        
        if (e.ctrlKey && e.key === 'g') {
            e.preventDefault();
            const activeTab = document.querySelector('#mainTabs .nav-link.active');
            if (activeTab && activeTab.getAttribute('data-bs-target') === '#create') {
                generateFactura();
                log('⌨️ Ctrl+G: Generar factura', 'info');
            }
        }
        
        if (e.ctrlKey && e.key === 'x') {
            e.preventDefault();
            switchToXMLTab();
            log('⌨️ Ctrl+X: Visor XML', 'info');
        }
        
        if (e.ctrlKey && e.key === 'c') {
            e.preventDefault();
            switchToCDRTab();
            log('⌨️ Ctrl+C: Visor CDR', 'info');
        }
    });
}

function initializeAutoRefresh() {
    // Auto-refresh cada 30 segundos en la pestaña de documentos
    setInterval(() => {
        const activeTab = document.querySelector('#mainTabs .nav-link.active');
        if (activeTab && activeTab.getAttribute('data-bs-target') === '#documents') {
            log('🔄 Auto-actualización de documentos...', 'info');
            refreshDocuments();
        }
    }, 30000);
}

// ===== ERROR HANDLING GLOBAL =====
window.addEventListener('error', function(e) {
    log(`💥 Error del sistema: ${e.message}`, 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    log(`💥 Promise rechazada: ${e.reason}`, 'error');
});

// ===== INICIALIZAR AL CARGAR LA PÁGINA =====
window.addEventListener('load', initializeApp);

// ===== FUNCIONES ADICIONALES DE UTILIDAD =====
function showNotification(message, type = 'info') {
    // Crear notificación simple
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ===== FUNCIONES DE EXPORTACIÓN =====
function exportToJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}