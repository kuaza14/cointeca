/**
 * COINTECA S.A.S. - Módulo de Ingeniería
 * detalle_proyecto.js - Matriz poste a poste, modales de apoyos, mano de obra y cálculos de liquidación.
 */

function cambiarPestana(tabName) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    const target = document.getElementById('panel-tab-' + tabName);
    if (target) target.classList.remove('hidden');

    ['materiales', 'mano_obra', 'resumen'].forEach(t => {
        const btn = document.getElementById('btn-tab-' + t);
        if (!btn) return;
        const badge = btn.querySelector('.badge-pestana');
        if (t === tabName) {
            btn.className = 'pestana-btn flex items-center gap-2 px-5 py-2.5 text-xs sm:text-sm font-bold rounded-lg transition cursor-pointer bg-primary text-white shadow-sm';
            if (badge) {
                badge.className = (t === 'resumen')
? 'badge-pestana px-2 py-0.5 rounded-full text-[10px] bg-amber-300 text-amber-900 font-extrabold'
: 'badge-pestana px-2 py-0.5 rounded-full text-[10px] bg-white/20 text-white';
            }
        } else {
            btn.className = 'pestana-btn flex items-center gap-2 px-5 py-2.5 text-xs sm:text-sm font-bold rounded-lg transition cursor-pointer text-muted-foreground hover:bg-muted hover:text-foreground';
            if (badge) {
                badge.className = (t === 'resumen')
? 'badge-pestana px-2 py-0.5 rounded-full text-[10px] bg-amber-100 text-amber-800 font-bold'
: 'badge-pestana px-2 py-0.5 rounded-full text-[10px] bg-muted text-foreground';
            }
        }
    });

    try {
        const url = new URL(window.location);
        url.searchParams.set('tab', tabName);
        window.history.replaceState(null, '', url);
    } catch (e) {}
}

// Configuración desacoplada leída desde ingenieria-config
const ingCfgEl = document.getElementById("ingenieria-config");
const ingCfg = ingCfgEl? JSON.parse(ingCfgEl.textContent): {};
const MAT_CABLE_ID = ingCfg.matCableId || "";
const URL_CREAR_APOYO = ingCfg.urlCrearApoyo || "";
const FECHA_HOY = ingCfg.fechaHoy || new Date().toISOString().split("T")[0];

const apoyosData = JSON.parse(document.getElementById('datos-apoyos-json')?.textContent || '{}');
const apoyosMOData = JSON.parse(document.getElementById('datos-apoyos-mo-json')?.textContent || '{}');

function crearFilaMO(itemId = '', cantidad = '1', observacion = '') {
    const tr = document.createElement('tr');
    tr.className = 'fila-mo-item';

    const templateSelect = document.querySelector('#templateSelectMO select');
    let optionsHtml = '';
    if (templateSelect) {
        Array.from(templateSelect.options).forEach(opt => {
            const selected = (itemId && String(opt.value) === String(itemId))? 'selected': '';
            optionsHtml += `<option value="${opt.value}" ${selected}>${opt.text}</option>`;
        });
    }

    tr.innerHTML = `
        <td class="px-3 py-2">
            <select name="item_mano_obra_id[]" required
                    class="w-full border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground bg-background font-medium focus:ring-2 focus:ring-primary focus:outline-none">
                ${optionsHtml}
            </select>
        </td>
        <td class="px-2 py-2">
            <input type="number" step="any" min="0.01" name="cantidad[]" value="${cantidad}" required placeholder="1.00"
                   class="w-full border border-emerald-400 rounded-lg px-2 py-1.5 text-xs font-black text-emerald-950 focus:ring-2 focus:ring-emerald-500 bg-emerald-50/40 text-center">
        </td>
        <td class="px-3 py-2">
            <textarea name="observacion[]" rows="2" placeholder="Escribe aquí la observación o justificación técnica detallada..."
                      class="w-full border border-border rounded-lg px-3 py-1.5 text-xs font-medium text-foreground bg-background focus:ring-2 focus:ring-primary focus:outline-none resize-y min-h-[42px] leading-relaxed shadow-2xs">${observacion}</textarea>
        </td>
        <td class="px-2 py-2 text-center">
            <button type="button" class="btnEliminarFilaMO text-destructive hover:text-red-800 font-bold text-lg p-1 rounded cursor-pointer">
                &times;
            </button>
        </td>
    `;
    return tr;
}

function crearSubFilaLuminaria(potencia = '', codigo = '') {
    const div = document.createElement('div');
    div.className = 'fila-sub-lum flex flex-wrap sm:flex-nowrap items-center gap-2 bg-white/80 p-1.5 rounded border border-amber-200';
    div.innerHTML = `
        <div class="flex items-center gap-1 flex-1 min-w-[120px]">
            <span class="text-[10px] font-extrabold text-amber-900 uppercase whitespace-nowrap"> Potencia:</span>
            <input type="text" value="${potencia}" placeholder="Ej: 70W, 190W..."
                   class="input-sub-potencia w-full bg-white border border-amber-300 rounded px-2 py-1 text-xs font-bold text-amber-900 focus:ring-1 focus:ring-amber-500 focus:outline-none"
                   title="Potencia en vatios de la luminaria (W)">
        </div>
        <div class="flex items-center gap-1 flex-1 min-w-[130px]">
            <span class="text-[10px] font-extrabold text-amber-900 uppercase whitespace-nowrap"> Código:</span>
            <input type="text" value="${codigo}" placeholder="Ej: 6T0698, 9U7940..."
                   class="input-sub-codigo w-full bg-white border border-blue-300 rounded px-2 py-1 text-xs font-bold font-mono text-blue-900 focus:ring-1 focus:ring-blue-500 focus:outline-none"
                   title="Código serial o placa de la luminaria">
        </div>
        <button type="button" class="btnQuitarSubLum text-destructive hover:text-red-800 text-lg font-bold px-2 py-0.5 rounded cursor-pointer leading-none" title="Quitar este código">&times;</button>
    `;
    return div;
}

function actualizarSerializacionLuminarias(td) {
    if (!td) return;
    const subFilas = td.querySelectorAll('.fila-sub-lum');
    const btnQuitarList = td.querySelectorAll('.btnQuitarSubLum');

    btnQuitarList.forEach(btn => {
        btn.style.display = (subFilas.length > 1)? '': 'none';
    });

    const lista = [];
    const potencias = [];
    const codigos = [];

    subFilas.forEach(f => {
        const inPot = f.querySelector('.input-sub-potencia');
        const inCod = f.querySelector('.input-sub-codigo');
        const pot = inPot? inPot.value.trim(): '';
        const cod = inCod? inCod.value.trim(): '';
        if (pot || cod) {
            lista.push({ potencia: pot, codigo: cod });
            if (pot) potencias.push(pot);
            if (cod) codigos.push(cod);
        }
    });

    const inputJson = td.querySelector('.input-json-luminarias');
    const inputPot = td.querySelector('.input-potencia-serializada');
    const inputCod = td.querySelector('.input-codigo-serializado');

    if (inputJson) inputJson.value = lista.length > 0? JSON.stringify(lista): '';
    if (inputPot) inputPot.value = potencias.join(', ');
    if (inputCod) inputCod.value = codigos.join(', ');

    const tr = td.closest('tr');
    if (tr && lista.length > 1) {
        const inInst = tr.querySelector('input[name="cantidad_instalada[]"]');
        if (inInst && (!inInst.value || parseFloat(inInst.value) < lista.length)) {
            inInst.value = lista.length;
        }
    }
}

function extraerPotenciaDeTexto(texto) {
    if (!texto) return '';
    const m = String(texto).match(/(?:DE\s+)?(\d+\s*W|6OW|\d+-\d+\s*W)/i);
    if (m) {
        return m[1].toUpperCase().replace(/\s+/g, '').replace('6OW', '60W');
    }
    return '';
}

function esLuminariaTexto(texto) {
    if (!texto) return false;
    const t = String(texto).toUpperCase();
    return (t.includes('LUM') || t.includes('SODIO') || t.includes('NA ') || t.includes('LED') || t.includes('PROY') || t.includes('FAROL')) && Boolean(extraerPotenciaDeTexto(t));
}

function onSelectMaterialNodo(selectEl) {
    const td = selectEl.closest('td');
    if (!td) return;
    const opt = selectEl.options[selectEl.selectedIndex];
    const contenedor = td.querySelector('.contenedor-potencia-mat');
    if (!contenedor) return;

    const esLuminaria = opt && (opt.dataset.esLuminaria === '1' || esLuminariaTexto(opt.text));
    const potenciaSugerida = opt? (opt.dataset.potencia || extraerPotenciaDeTexto(opt.text)): '';

    if (esLuminaria) {
        contenedor.classList.remove('hidden');
        const contSub = td.querySelector('.contenedor-sub-lums');
        if (contSub) {
            let subFilas = contSub.querySelectorAll('.fila-sub-lum');
            if (subFilas.length === 0) {
                contSub.appendChild(crearSubFilaLuminaria(potenciaSugerida, ''));
            } else if (subFilas.length === 1) {
                const inPot = subFilas[0].querySelector('.input-sub-potencia');
                if (inPot &&!inPot.value && potenciaSugerida) {
                    inPot.value = potenciaSugerida;
                }
            }
        }
        actualizarSerializacionLuminarias(td);
    } else {
        contenedor.classList.add('hidden');
        const inputJson = td.querySelector('.input-json-luminarias');
        const inputPot = td.querySelector('.input-potencia-serializada');
        const inputCod = td.querySelector('.input-codigo-serializado');
        if (inputJson) inputJson.value = '';
        if (inputPot) inputPot.value = '';
        if (inputCod) inputCod.value = '';
    }
}

function crearFilaMaterial(materialId = '', cantInst = '', cantRet = '', potencia = '', codigo = '', subLuminariasList = null) {
    const tr = document.createElement('tr');
    tr.className = 'fila-material-nodo';

    const templateSelect = document.querySelector('#templateSelectMaterial select');
    let optionsHtml = '';
    let selectedPotencia = potencia || '';
    let selectedCodigo = codigo || '';
    let selectedEsLuminaria = false;

    if (templateSelect) {
        Array.from(templateSelect.options).forEach(opt => {
            const isSel = (materialId && String(opt.value) === String(materialId));
            const selected = isSel? 'selected': '';
            const esLumOpt = opt.dataset.esLuminaria === '1' || esLuminariaTexto(opt.text);
            const potOpt = opt.dataset.potencia || extraerPotenciaDeTexto(opt.text);
            if (isSel) {
                selectedEsLuminaria = esLumOpt;
                if (!selectedPotencia && potOpt) {
                    selectedPotencia = potOpt;
                }
            }
            optionsHtml += `<option value="${opt.value}" data-es-luminaria="${esLumOpt? '1': '0'}" data-potencia="${potOpt}" ${selected}>${opt.text}</option>`;
        });
    }

    const esLuminariaReal = selectedEsLuminaria || Boolean(selectedPotencia) || Boolean(selectedCodigo);
    const mostrarPotencia = esLuminariaReal;

    tr.innerHTML = `
        <td class="px-3 py-2">
            <select name="material_id[]" onchange="onSelectMaterialNodo(this)"
                    class="w-full border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground bg-background font-medium focus:ring-2 focus:ring-primary focus:outline-none select-material-nodo">
                ${optionsHtml}
            </select>
            <div class="contenedor-potencia-mat mt-1.5 ${mostrarPotencia? '': 'hidden'}">
                <div class="bg-amber-50/90 border border-amber-300 rounded-lg p-2.5 shadow-2xs space-y-2">
                    <div class="flex items-center justify-between border-b border-amber-200/80 pb-1.5">
                        <span class="text-[10px] font-black text-amber-900 uppercase flex items-center gap-1">
                            <span></span> Potencia y Código de Luminaria
                        </span>
                        <button type="button" class="btnAgregarSubLum inline-flex items-center gap-1 px-2 py-0.5 bg-amber-600 hover:bg-amber-700 text-white text-[10px] font-bold rounded shadow-2xs cursor-pointer" title="Agregar otra potencia y código a este poste">
                            <span></span> Agregar otra potencia / código
                        </button>
                    </div>

                    <!-- Contenedor dinámico de potencias y códigos -->
                    <div class="contenedor-sub-lums space-y-1.5"></div>

                    <!-- Inputs serializados para el POST -->
                    <input type="hidden" name="potencia_material[]" class="input-potencia-serializada" value="">
                    <input type="hidden" name="codigo_luminaria_material[]" class="input-codigo-serializado" value="">
                    <input type="hidden" name="luminarias_json_material[]" class="input-json-luminarias" value="">
                </div>
            </div>
        </td>
        <td class="px-3 py-2">
            <input type="number" step="any" min="0" name="cantidad_instalada[]" value="${cantInst}" placeholder="0.00"
                   class="w-full border border-blue-400 rounded-lg px-2.5 py-1.5 text-xs font-black text-blue-900 focus:ring-2 focus:ring-blue-500 bg-blue-50/40">
        </td>
        <td class="px-3 py-2">
            <input type="number" step="any" min="0" name="cantidad_retirada[]" value="${cantRet}" placeholder="0.00"
                   class="w-full border border-amber-400 rounded-lg px-2.5 py-1.5 text-xs font-black text-amber-900 focus:ring-2 focus:ring-amber-500 bg-amber-50/40">
        </td>
        <td class="px-2 py-2 text-center">
            <button type="button" class="btnEliminarMaterialNodo text-destructive hover:text-red-800 font-bold text-lg p-1 rounded">
                &times;
            </button>
        </td>
    `;

    // Población de las sub-filas de luminaria
    const contSub = tr.querySelector('.contenedor-sub-lums');
    const td = tr.querySelector('td');
    if (contSub && esLuminariaReal) {
        let items = [];
        if (selectedCodigo || selectedPotencia) {
            const cods = selectedCodigo? selectedCodigo.split(',').map(s => s.trim()): [];
            const pots = selectedPotencia? selectedPotencia.split(',').map(s => s.trim()): [];
            const maxLen = Math.max(cods.length, pots.length, 1);
            for (let i = 0; i < maxLen; i++) {
                const p = pots[i] || (pots[0] || '');
                const c = cods[i] || '';
                items.push({ potencia: p, codigo: c });
            }
        } else if (subLuminariasList && Array.isArray(subLuminariasList) && subLuminariasList.length > 0) {
            items = subLuminariasList;
        } else {
            items.push({ potencia: selectedPotencia, codigo: '' });
        }

        items.forEach(it => {
            contSub.appendChild(crearSubFilaLuminaria(it.potencia || '', it.codigo || ''));
        });

        actualizarSerializacionLuminarias(td);
    }

    return tr;
}

let currentEditingApoyoId = null;
let huboDespachoEnModal = false;

function actualizarStockEnTodosLosSelects(materialId, stockRestante, item, descripcion, unidad) {
    let stockLabel = '';
    const numStock = parseFloat(stockRestante);
    const stockLimpio = Number.isInteger(numStock)? numStock: parseFloat(numStock.toFixed(2));
    if (numStock > 0) {
        stockLabel = `[Stock: ${stockLimpio} ${unidad}]`;
    } else if (numStock < 0) {
        stockLabel = `[ Déficit: ${stockLimpio} ${unidad}]`;
    } else {
        stockLabel = `[ Sin stock: 0 ${unidad}]`;
    }
    const nuevoTexto = `[${item}] ${descripcion} ${stockLabel}`;

    // 1. Actualizar en el selector de despacho de bodega
    const optDespacho = document.querySelector(`#despacho_material_id option[value="${materialId}"]`);
    if (optDespacho) {
        optDespacho.textContent = nuevoTexto;
    }

    // 2. Actualizar en el template base oculto
    const optTemplate = document.querySelector(`#templateSelectMaterial select option[value="${materialId}"]`);
    if (optTemplate) {
        optTemplate.textContent = nuevoTexto;
    }

    // 3. Actualizar en todos los selects existentes en la tabla de materiales
    document.querySelectorAll(`#filasMaterialesNodo select[name="material_id[]"] option[value="${materialId}"]`).forEach(opt => {
        opt.textContent = nuevoTexto;
    });
}

function abrirModalNuevoApoyo() {
    currentEditingApoyoId = null;
    huboDespachoEnModal = false;
    const modal = document.getElementById('modalNuevoApoyo');
    const form = document.getElementById('formModalApoyo');
    if (!modal ||!form) return;

    form.action = URL_CREAR_APOYO || form.action;
    document.getElementById('modalApoyoIcono').textContent = '';
    document.getElementById('modalApoyoTitulo').textContent = 'Nuevo Nodo / Apoyo — Formato Poste a Poste';
    delete form.dataset.submitting;
    const btnSubmit = document.getElementById('btnSubmitModalApoyo');
    if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.style.pointerEvents = '';
        btnSubmit.classList.remove('opacity-70', 'cursor-not-allowed');
        btnSubmit.textContent = 'Guardar Poste';
        const sp = btnSubmit.querySelector('.spinner-anti-double');
        if (sp) sp.remove();
    }

    const seccionBodega = document.getElementById('seccionDespachoBodega');
    if (seccionBodega) seccionBodega.classList.add('hidden');

    const alertaDespacho = document.getElementById('alertaDespachoBodega');
    if (alertaDespacho) alertaDespacho.classList.add('hidden');

    document.getElementById('modalApoyo_quien_ejecuta').value = '';
    document.getElementById('modalApoyo_nodo').value = '';
    document.getElementById('modalApoyo_numero_apoyo').value = '';
    document.getElementById('modalApoyo_fecha').value = FECHA_HOY;
    document.getElementById('modalApoyo_tipo_instalacion').value = '';
    document.getElementById('modalApoyo_direccion').value = '';
    const elTipoEst = document.getElementById('modalApoyo_tipo_estructura');
    if (elTipoEst) elTipoEst.value = '';
    document.getElementById('modalApoyo_brazo').value = '2';
    document.getElementById('modalApoyo_estado').value = 'Pendiente';
    const elCantRet = document.getElementById('modalApoyo_cantidad_retenida');
    if (elCantRet) elCantRet.value = '';
    const elAltRet = document.getElementById('modalApoyo_altura_retenida');
    if (elAltRet) elAltRet.value = '';
    const elMetRet = document.getElementById('modalApoyo_metros_retenido');
    if (elMetRet) elMetRet.value = '';
    document.getElementById('modalApoyo_observacion').value = '';
    const infoRetNew = document.getElementById('modalApoyo_retenida_info');
    if (infoRetNew) infoRetNew.innerHTML = 'Cable EAR 3/8" (Ítem 43)';

    const tbodyMat = document.getElementById('filasMaterialesNodo');
    tbodyMat.innerHTML = '';
    tbodyMat.appendChild(crearFilaMaterial());

    modal.classList.remove('hidden');
}

function recalcularMetrosRetenidaModal() {
    const inputCant = document.getElementById('modalApoyo_cantidad_retenida');
    const selectAlt = document.getElementById('modalApoyo_altura_retenida');
    const inputMet = document.getElementById('modalApoyo_metros_retenido');
    const info = document.getElementById('modalApoyo_retenida_info');
    if (!inputCant ||!selectAlt ||!inputMet) return;

    const cant = parseFloat(inputCant.value) || 0;
    const tipo = selectAlt.value;

    if (tipo === '12') {
        const total = cant > 0? (cant * 14): 0;
        inputMet.value = total > 0? parseFloat(total.toFixed(2)): (cant === 0? '0': '');
        if (info) {
            info.innerHTML = cant > 0
? `<span class="text-blue-600 font-bold"> ${cant} × 14m = ${parseFloat(total.toFixed(2))}m Cable EAR 3/8" a descontar</span>`
: `<span class="text-blue-600 font-semibold">Poste 12: 14 mts por retenida (Cable EAR 3/8")</span>`;
        }
    } else if (tipo === '14') {
        const total = cant > 0? (cant * 16): 0;
        inputMet.value = total > 0? parseFloat(total.toFixed(2)): (cant === 0? '0': '');
        if (info) {
            info.innerHTML = cant > 0
? `<span class="text-blue-600 font-bold"> ${cant} × 16m = ${parseFloat(total.toFixed(2))}m Cable EAR 3/8" a descontar</span>`
: `<span class="text-blue-600 font-semibold">Poste 14: 16 mts por retenida (Cable EAR 3/8")</span>`;
        }
    } else if (tipo === 'manual') {
        if (info) {
            info.innerHTML = `<span class="text-amber-600 font-semibold">Ingreso manual (Cable EAR 3/8" Ítem 43)</span>`;
        }
    } else {
        if (info) {
            info.innerHTML = 'Cable EAR 3/8" (Ítem 43)';
        }
    }
}

function verificarMetrosManualModal() {
    const selectAlt = document.getElementById('modalApoyo_altura_retenida');
    if (selectAlt && selectAlt.value!== '12' && selectAlt.value!== '14') {
        selectAlt.value = 'manual';
    }
}

function abrirModalEditarApoyo(apoyoId) {
    currentEditingApoyoId = apoyoId;
    huboDespachoEnModal = false;
    const data = apoyosData[apoyoId];
    if (!data) return;

    const modal = document.getElementById('modalNuevoApoyo');
    const form = document.getElementById('formModalApoyo');
    if (!modal ||!form) return;

    form.action = '/ingenieria/apoyo/' + apoyoId + '/editar/';
    document.getElementById('modalApoyoIcono').textContent = '';
    document.getElementById('modalApoyoTitulo').textContent = 'Editar Nodo / Apoyo — ' + (data.nodo? 'Nodo ' + data.nodo: 'Apoyo #' + (data.numero_apoyo || apoyoId));
    delete form.dataset.submitting;
    const btnSubmit = document.getElementById('btnSubmitModalApoyo');
    if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.style.pointerEvents = '';
        btnSubmit.classList.remove('opacity-70', 'cursor-not-allowed');
        btnSubmit.textContent = 'Guardar Cambios';
        const sp = btnSubmit.querySelector('.spinner-anti-double');
        if (sp) sp.remove();
    }

    const seccionBodega = document.getElementById('seccionDespachoBodega');
    if (seccionBodega) {
        seccionBodega.classList.remove('hidden');
        document.getElementById('despacho_material_id').selectedIndex = 0;
        document.getElementById('despacho_cantidad').value = '';
    }

    const alertaDespacho = document.getElementById('alertaDespachoBodega');
    if (alertaDespacho) alertaDespacho.classList.add('hidden');

    document.getElementById('modalApoyo_quien_ejecuta').value = data.quien_ejecuta_id || '';
    document.getElementById('modalApoyo_nodo').value = data.nodo || '';
    document.getElementById('modalApoyo_numero_apoyo').value = data.numero_apoyo || '';
    document.getElementById('modalApoyo_fecha').value = data.fecha || '';
    document.getElementById('modalApoyo_tipo_instalacion').value = data.tipo_instalacion || '';
    document.getElementById('modalApoyo_direccion').value = data.direccion || '';
    const elEditTipoEst = document.getElementById('modalApoyo_tipo_estructura');
    if (elEditTipoEst) elEditTipoEst.value = data.tipo_estructura || '';
    document.getElementById('modalApoyo_brazo').value = data.brazo || '2';
    document.getElementById('modalApoyo_estado').value = data.estado || 'Pendiente';
    const elEditCantRet = document.getElementById('modalApoyo_cantidad_retenida');
    if (elEditCantRet) elEditCantRet.value = data.cantidad_retenida || '';
    const elEditMetRet = document.getElementById('modalApoyo_metros_retenido');
    if (elEditMetRet) elEditMetRet.value = data.metros_retenido || '';
    document.getElementById('modalApoyo_observacion').value = data.observacion || '';

    // Auto-detectar altura de retenida según cantidad y metros
    const cantRet = parseFloat(data.cantidad_retenida) || 0;
    const metRet = parseFloat(data.metros_retenido) || 0;
    const selectAlt = document.getElementById('modalApoyo_altura_retenida');
    if (selectAlt) {
        if (cantRet > 0 && metRet > 0) {
            const porRet = metRet / cantRet;
            if (Math.abs(porRet - 14) < 0.05) {
                selectAlt.value = '12';
            } else if (Math.abs(porRet - 16) < 0.05) {
                selectAlt.value = '14';
            } else {
                selectAlt.value = 'manual';
            }
        } else {
            selectAlt.value = '';
        }
    }
    recalcularMetrosRetenidaModal();

    const tbodyMat = document.getElementById('filasMaterialesNodo');
    tbodyMat.innerHTML = '';
    if (data.materiales && data.materiales.length > 0) {
        let matsAgregados = 0;
        data.materiales.forEach(m => {
            // El cable de retenida se gestiona automáticamente por la sección de Retenidas
            if (MAT_CABLE_ID && String(m.material_id) === String(MAT_CABLE_ID)) {
                return;
            }
            let subLums = null;
            if (data.luminarias && data.luminarias.length > 0 && parseFloat(m.cant_inst) > 0) {
                subLums = data.luminarias;
            }
            tbodyMat.appendChild(crearFilaMaterial(m.material_id, m.cant_inst, m.cant_ret, m.potencia, m.codigo, subLums));
            matsAgregados++;
        });
        if (matsAgregados === 0) {
            tbodyMat.appendChild(crearFilaMaterial());
        }
    } else {
        tbodyMat.appendChild(crearFilaMaterial());
    }

    modal.classList.remove('hidden');
}

function cerrarModalApoyo() {
    const modal = document.getElementById('modalNuevoApoyo');
    if (modal) modal.classList.add('hidden');
    const form = document.getElementById('formModalApoyo');
    if (form) delete form.dataset.submitting;
    const btnSubmit = document.getElementById('btnSubmitModalApoyo');
    if (btnSubmit) {
        btnSubmit.disabled = false;
        btnSubmit.style.pointerEvents = '';
        btnSubmit.classList.remove('opacity-70', 'cursor-not-allowed');
        const sp = btnSubmit.querySelector('.spinner-anti-double');
        if (sp) sp.remove();
    }
    if (huboDespachoEnModal) {
        // Refrescar la página para actualizar todas las tablas de balance y logística
        const url = new URL(window.location);
        url.searchParams.set('tab', 'materiales');
        window.location.href = url.toString();
    }
}

function actualizarActionMO(apoyoId) {
    const form = document.getElementById('formAsignarMO');
    if (apoyoId && form) {
        form.action = '/ingenieria/apoyos/' + apoyoId + '/mano-obra-manual/';
    }
}

function onSelectApoyoMOChange(apoyoId) {
    actualizarActionMO(apoyoId);
    const select = document.getElementById('selectApoyoMO');
    const titulo = document.getElementById('modalAsignarMOTitulo');
    const tbody = document.getElementById('filasMOMultiple');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (apoyoId && select) {
        const nodoTexto = select.options[select.selectedIndex]? select.options[select.selectedIndex].text: '';
        if (titulo) titulo.textContent = 'Editar Servicios de Mano de Obra — ' + nodoTexto;
        if (typeof apoyosMOData!== 'undefined' && apoyosMOData[apoyoId] && apoyosMOData[apoyoId].length > 0) {
            apoyosMOData[apoyoId].forEach(mo => {
                tbody.appendChild(crearFilaMO(mo.item_id, mo.cantidad, mo.observacion));
            });
        } else {
            tbody.appendChild(crearFilaMO());
        }
    } else {
        if (titulo) titulo.textContent = 'Asignar Servicios Manuales a un Poste';
        tbody.appendChild(crearFilaMO());
    }
}

function abrirModalAsignarMO(apoyoId = null) {
    const modal = document.getElementById('modalAsignarMO');
    const select = document.getElementById('selectApoyoMO');
    const titulo = document.getElementById('modalAsignarMOTitulo');
    const tbody = document.getElementById('filasMOMultiple');
    if (!modal ||!tbody) return;

    tbody.innerHTML = '';

    if (apoyoId && select) {
        select.value = apoyoId;
        actualizarActionMO(apoyoId);
        const nodoTexto = select.options[select.selectedIndex]? select.options[select.selectedIndex].text: '';
        if (titulo) titulo.textContent = 'Editar Servicios de Mano de Obra — ' + nodoTexto;
        if (typeof apoyosMOData!== 'undefined' && apoyosMOData[apoyoId] && apoyosMOData[apoyoId].length > 0) {
            apoyosMOData[apoyoId].forEach(mo => {
                tbody.appendChild(crearFilaMO(mo.item_id, mo.cantidad, mo.observacion));
            });
        } else {
            tbody.appendChild(crearFilaMO());
        }
    } else {
        if (select) {
            select.selectedIndex = 0;
        }
        if (titulo) titulo.textContent = 'Asignar Servicios Manuales a un Poste';
        tbody.appendChild(crearFilaMO());
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function cerrarModalAsignarMO() {
    const modal = document.getElementById('modalAsignarMO');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const btnNuevoApoyo = document.getElementById("btnNuevoApoyo");
    if (btnNuevoApoyo) {
        btnNuevoApoyo.addEventListener("click", abrirModalNuevoApoyo);
    }

    // Despacho Asíncrono desde Bodega Central (Sin cerrar modal)
    const btnEjecutarDespacho = document.getElementById('btnEjecutarDespachoBodega');
    const inputDespachoCantidad = document.getElementById('despacho_cantidad');

    async function ejecutarDespachoBodegaAsync() {
        if (!currentEditingApoyoId) {
            alert('Debes estar editando un nodo para despachar desde bodega.');
            return;
        }
        const selectMat = document.getElementById('despacho_material_id');
        const matId = selectMat? selectMat.value: '';
        const cant = inputDespachoCantidad? inputDespachoCantidad.value: '';

        if (!matId ||!cant || parseFloat(cant) <= 0) {
            alert('Por favor selecciona un material de bodega e ingresa una cantidad válida.');
            return;
        }

        const csrfTokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfTokenEl? csrfTokenEl.value: '';

        const iconoBtn = document.getElementById('iconoBtnDespacho');
        const textoBtn = document.getElementById('textoBtnDespacho');
        const alertaDespacho = document.getElementById('alertaDespachoBodega');
        const textoAlerta = document.getElementById('alertaDespachoTexto');

        // Estado cargando
        btnEjecutarDespacho.disabled = true;
        if (iconoBtn) iconoBtn.textContent = '';
        if (textoBtn) textoBtn.textContent = 'Despachando...';

        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('material_id', matId);
        formData.append('cantidad', cant);
        formData.append('ajax', '1');

        try {
            const resp = await fetch('/ingenieria/apoyo/' + currentEditingApoyoId + '/despachar-bodega/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            const data = await resp.json();

            if (resp.ok && data.success) {
                huboDespachoEnModal = true;

                // 1. Actualizar textos de stock en todos los selects
                actualizarStockEnTodosLosSelects(
                    data.material_id,
                    data.stock_restante,
                    data.material_item,
                    data.material_descripcion,
                    data.unidad
);

                // 2. Actualizar o insertar fila en la tabla de materiales del nodo
                const tbodyMat = document.getElementById('filasMaterialesNodo');
                let filaEncontrada = null;

                if (tbodyMat) {
                    const filas = tbodyMat.querySelectorAll('.fila-material-nodo');
                    filas.forEach(f => {
                        const sel = f.querySelector('select[name="material_id[]"]');
                        if (sel && String(sel.value) === String(data.material_id)) {
                            filaEncontrada = f;
                        }
                    });

                    if (filaEncontrada) {
                        const inpInst = filaEncontrada.querySelector('input[name="cantidad_instalada[]"]');
                        if (inpInst) {
                            inpInst.value = data.cantidad_total_instalada;
                        }
                        filaEncontrada.classList.add('bg-emerald-100');
                        setTimeout(() => filaEncontrada.classList.remove('bg-emerald-100'), 2500);
                    } else {
                        // Verificar si hay una fila vacía para reutilizar
                        let filaVacia = null;
                        if (filas.length === 1) {
                            const sel = filas[0].querySelector('select[name="material_id[]"]');
                            const inpInst = filas[0].querySelector('input[name="cantidad_instalada[]"]');
                            const inpRet = filas[0].querySelector('input[name="cantidad_retirada[]"]');
                            if (sel && (!sel.value || sel.value === '') && (!inpInst ||!inpInst.value) && (!inpRet ||!inpRet.value)) {
                                filaVacia = filas[0];
                            }
                        }

                        if (filaVacia) {
                            const sel = filaVacia.querySelector('select[name="material_id[]"]');
                            const inpInst = filaVacia.querySelector('input[name="cantidad_instalada[]"]');
                            if (sel) sel.value = data.material_id;
                            if (inpInst) inpInst.value = data.cantidad_despachada;
                            filaVacia.classList.add('bg-emerald-100');
                            setTimeout(() => filaVacia.classList.remove('bg-emerald-100'), 2500);
                        } else {
                            const nuevaFila = crearFilaMaterial(data.material_id, data.cantidad_despachada, 0);
                            tbodyMat.appendChild(nuevaFila);
                            nuevaFila.classList.add('bg-emerald-100');
                            setTimeout(() => nuevaFila.classList.remove('bg-emerald-100'), 2500);
                        }
                    }
                }

                // 3. Actualizar datos en memoria apoyosData
                if (apoyosData[currentEditingApoyoId]) {
                    const mats = apoyosData[currentEditingApoyoId].materiales || [];
                    const matObj = mats.find(m => String(m.material_id) === String(data.material_id));
                    if (matObj) {
                        matObj.cant_inst = String(data.cantidad_total_instalada);
                    } else {
                        mats.push({
                            material_id: String(data.material_id),
                            cant_inst: String(data.cantidad_despachada),
                            cant_ret: "0"
                        });
                    }
                    apoyosData[currentEditingApoyoId].materiales = mats;
                }

                // 4. Mostrar feedback en el banner
                if (alertaDespacho && textoAlerta) {
                    if (data.warning) {
                        alertaDespacho.className = 'p-3 rounded-lg text-xs font-semibold flex items-center justify-between bg-amber-100 text-amber-900 border border-amber-300 transition-all';
                        textoAlerta.innerHTML = data.warning;
                    } else {
                        alertaDespacho.className = 'p-3 rounded-lg text-xs font-semibold flex items-center justify-between bg-emerald-100 text-emerald-900 border border-emerald-300 transition-all';
                        const cantDespFmt = Number.isInteger(data.cantidad_despachada)? data.cantidad_despachada: parseFloat(data.cantidad_despachada.toFixed(2));
                        const stockRestFmt = Number.isInteger(data.stock_restante)? data.stock_restante: parseFloat(data.stock_restante.toFixed(2));
                        textoAlerta.innerHTML = ` <strong>¡Despacho Exitoso!</strong> Se despacharon <strong>${cantDespFmt} ${data.unidad}</strong> de <em>${data.material_descripcion}</em> al poste. (Stock restante en bodega: <strong>${stockRestFmt} ${data.unidad}</strong>). ¡Puedes despachar otro material!`;
                    }
                    alertaDespacho.classList.remove('hidden');
                }

                // 5. Limpiar campos y dar foco al select para permitir despachar otro material inmediatamente
                if (inputDespachoCantidad) inputDespachoCantidad.value = '';
                if (selectMat) {
                    selectMat.selectedIndex = 0;
                    selectMat.focus();
                }

            } else {
                const errMsg = data.error || 'Ocurrió un error al despachar el material.';
                if (alertaDespacho && textoAlerta) {
                    alertaDespacho.className = 'p-3 rounded-lg text-xs font-semibold flex items-center justify-between bg-red-100 text-red-900 border border-red-300 transition-all';
                    textoAlerta.innerHTML = ` <strong>Error:</strong> ${errMsg}`;
                    alertaDespacho.classList.remove('hidden');
                } else {
                    alert(errMsg);
                }
            }
        } catch (err) {
            console.error('Error en despacho AJAX:', err);
            if (alertaDespacho && textoAlerta) {
                alertaDespacho.className = 'p-3 rounded-lg text-xs font-semibold flex items-center justify-between bg-red-100 text-red-900 border border-red-300 transition-all';
                textoAlerta.innerHTML = ` <strong>Error de conexión:</strong> No se pudo completar el despacho. Intenta de nuevo.`;
                alertaDespacho.classList.remove('hidden');
            } else {
                alert('No se pudo conectar con el servidor para despachar.');
            }
        } finally {
            btnEjecutarDespacho.disabled = false;
            if (iconoBtn) iconoBtn.textContent = '';
            if (textoBtn) textoBtn.textContent = 'Despachar al Poste';
        }
    }

    if (btnEjecutarDespacho) {
        btnEjecutarDespacho.addEventListener('click', ejecutarDespachoBodegaAsync);
    }

    if (inputDespachoCantidad) {
        inputDespachoCantidad.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                ejecutarDespachoBodegaAsync();
            }
        });
    }

    // Materiales dinámicos (Botón agregar y sub-luminarias)
    const btnAgregarMaterialNodo = document.getElementById("btnAgregarMaterialNodo");
    const filasMaterialesNodo = document.getElementById("filasMaterialesNodo");
    if (btnAgregarMaterialNodo && filasMaterialesNodo) {
        btnAgregarMaterialNodo.addEventListener("click", function () {
            filasMaterialesNodo.appendChild(crearFilaMaterial());
        });

        // Eventos delegados de eliminación de material y sub-luminarias
        filasMaterialesNodo.addEventListener("click", function (e) {
            // 1. Agregar otra potencia y código a este material de luminaria
            const btnAddSub = e.target.closest(".btnAgregarSubLum");
            if (btnAddSub) {
                const td = btnAddSub.closest("td");
                const contSub = td? td.querySelector(".contenedor-sub-lums"): null;
                if (contSub) {
                    const ultPot = contSub.querySelector(".fila-sub-lum:last-child.input-sub-potencia");
                    const potSug = ultPot? ultPot.value: "";
                    const nuevaSub = crearSubFilaLuminaria(potSug, "");
                    contSub.appendChild(nuevaSub);
                    actualizarSerializacionLuminarias(td);
                    const nuevoInputCod = nuevaSub.querySelector(".input-sub-codigo");
                    if (nuevoInputCod) nuevoInputCod.focus();
                }
                return;
            }

            // 2. Quitar sub-fila de luminaria
            const btnQuitSub = e.target.closest(".btnQuitarSubLum");
            if (btnQuitSub) {
                const filaSub = btnQuitSub.closest(".fila-sub-lum");
                const td = btnQuitSub.closest("td");
                if (filaSub) filaSub.remove();
                actualizarSerializacionLuminarias(td);
                return;
            }

            // 3. Eliminar fila completa de material
            const btnEliminar = e.target.closest(".btnEliminarMaterialNodo");
            if (btnEliminar) {
                const filas = filasMaterialesNodo.querySelectorAll(".fila-material-nodo");
                if (filas.length > 1) {
                    btnEliminar.closest(".fila-material-nodo").remove();
                } else {
                    const fila = btnEliminar.closest(".fila-material-nodo");
                    if (fila) {
                        const sel = fila.querySelector('select[name="material_id[]"]');
                        if (sel) {
                            sel.selectedIndex = 0;
                            onSelectMaterialNodo(sel);
                        }
                        const inInst = fila.querySelector('input[name="cantidad_instalada[]"]');
                        if (inInst) inInst.value = '';
                        const inRet = fila.querySelector('input[name="cantidad_retirada[]"]');
                        if (inRet) inRet.value = '';
                    }
                }
            }
        });

        // Sincronización en tiempo real al escribir potencia o código
        filasMaterialesNodo.addEventListener("input", function (e) {
            if (e.target.matches(".input-sub-potencia,.input-sub-codigo")) {
                const td = e.target.closest("td");
                actualizarSerializacionLuminarias(td);
            }
        });
    }

    // Actividades y Servicios de Mano de Obra Múltiple (Botón agregar fila)
    const btnAgregarFilaMO = document.getElementById("btnAgregarFilaMO");
    const filasMOMultiple = document.getElementById("filasMOMultiple");
    if (btnAgregarFilaMO && filasMOMultiple) {
        btnAgregarFilaMO.addEventListener("click", function () {
            filasMOMultiple.appendChild(crearFilaMO());
        });

        filasMOMultiple.addEventListener("click", function (e) {
            const btnEliminar = e.target.closest(".btnEliminarFilaMO");
            if (btnEliminar) {
                const filas = filasMOMultiple.querySelectorAll(".fila-mo-item");
                if (filas.length > 1) {
                    btnEliminar.closest(".fila-mo-item").remove();
                } else {
                    const fila = btnEliminar.closest(".fila-mo-item");
                    if (fila) {
                        const sel = fila.querySelector('select[name="item_mano_obra_id[]"]');
                        if (sel) sel.selectedIndex = 0;
                        const inCant = fila.querySelector('input[name="cantidad[]"]');
                        if (inCant) inCant.value = '1';
                        const inObs = fila.querySelector('[name="observacion[]"]');
                        if (inObs) inObs.value = '';
                    }
                }
            }
        });
    }

    // Sincronización final antes del envío del formulario de apoyo
    const formModalApoyo = document.getElementById("formModalApoyo");
    if (formModalApoyo) {
        formModalApoyo.addEventListener("submit", function () {
            document.querySelectorAll("#filasMaterialesNodo.fila-material-nodo td:first-child").forEach(td => {
                actualizarSerializacionLuminarias(td);
            });
        });
    }

    // Inicializar con 1 fila si están vacíos al cargar
    if (filasMaterialesNodo && filasMaterialesNodo.children.length === 0) {
        filasMaterialesNodo.appendChild(crearFilaMaterial());
    }
    if (filasMOMultiple && filasMOMultiple.children.length === 0) {
        filasMOMultiple.appendChild(crearFilaMO());
    }

    // Auto-abrir modal si la URL contiene?editar_apoyo=ID o?apoyo_id=ID
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const editarApoyoId = urlParams.get('editar_apoyo') || urlParams.get('apoyo_id');
        if (editarApoyoId && typeof apoyosData!== 'undefined' && apoyosData[editarApoyoId]) {
            cambiarPestana('materiales');
            abrirModalEditarApoyo(editarApoyoId);
            const elFila = document.getElementById('fila-apoyo-' + editarApoyoId);
            if (elFila) {
                elFila.classList.add('ring-2', 'ring-primary', 'bg-amber-100');
                setTimeout(() => elFila.scrollIntoView({ behavior: 'smooth', block: 'center' }), 200);
            }
        }
    } catch (e) {
        console.error('Error al auto-abrir modal de apoyo:', e);
    }
});
