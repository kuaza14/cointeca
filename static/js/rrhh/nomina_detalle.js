/**
 * COINTECA S.A.S. - Recursos Humanos
 * nomina_detalle.js - Matriz interactiva de nómina en vivo, recálculos en navegador,
 * gestión visual de ausencias injustificadas con descuento dominical (Art. 173 CST) y persistencia AJAX.
 */

(function () {
    'use strict';

    // Leer configuración inyectada desde el backend
    let config = {};
    const configEl = document.getElementById('nomina-config');
    if (configEl && configEl.textContent) {
        try {
            config = JSON.parse(configEl.textContent);
        } catch (e) {
            console.error('Error al parsear nómina config:', e);
        }
    }

    const SMMLV_BASE = parseFloat(config.smmlvBase) || 1750905;
    const AUX_TRANSPORTE_BASE = parseFloat(config.auxTransporteBase) || 249095;
    const PERIODO_ID = parseInt(config.periodoId) || 0;
    const PERIODO_MES = parseInt(config.periodoMes) || (new Date().getMonth() + 1);
    const PERIODO_ANO = parseInt(config.periodoAno) || new Date().getFullYear();

    // Estado local de los registros de empleados
    let detallesData = [];
    let hayCambiosSinGuardar = false;

    // Estado local del modal de ausencias
    let empleadoActualModal = null;
    let fechasSeleccionadasModal = new Set();
    let descontarDominicalModal = true;

    const NOMBRES_MESES = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];

    // Inicialización del DOM
    document.addEventListener('DOMContentLoaded', function () {
        const scriptEl = document.getElementById('datos-detalles-json');
        if (scriptEl && scriptEl.textContent) {
            try {
                detallesData = JSON.parse(scriptEl.textContent);
            } catch (e) {
                console.error('Error al parsear datos de nómina:', e);
                detallesData = [];
            }
        }
        renderizarTabla();
        actualizarTotalesGenerales();
    });

    // Formateador de moneda en pesos colombianos
    function formatoDinero(valor) {
        if (isNaN(valor) || valor === null || valor === undefined) return '0';
        return Math.round(valor).toLocaleString('es-CO');
    }

    // Obtener token CSRF
    function obtenerCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input) return input.value;
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    // Utilidades de Fechas y Semanas ISO (Lunes a Domingo)
    function parseDateISO(str) {
        const [y, m, d] = str.split('-').map(Number);
        return new Date(y, m - 1, d);
    }

    function formatDateISO(d) {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function getMondayOfWeek(d) {
        const copy = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        const day = copy.getDay(); // 0: Dom, 1: Lun, ..., 6: Sáb
        const diff = (day === 0 ? -6 : 1 - day);
        copy.setDate(copy.getDate() + diff);
        return copy;
    }

    function getSundayOfWeek(mondayDate) {
        const copy = new Date(mondayDate.getFullYear(), mondayDate.getMonth(), mondayDate.getDate());
        copy.setDate(copy.getDate() + 6);
        return copy;
    }

    // Renderizar botón de ausencias por fila
    function renderizarBotonAusencias(item) {
        const faltas = parseFloat(item.dias_faltas_injustificadas) || 0;
        const dom = parseFloat(item.domingos_descontados) || 0;
        if (faltas > 0) {
            return `
                <button type="button" id="btn-ausencias-${item.id}" onclick="abrirModalAusencias(${item.id})"
                        class="px-2 py-0.5 rounded-lg text-[11px] font-bold bg-amber-100 text-amber-900 border border-amber-300 hover:bg-amber-200 transition cursor-pointer flex items-center justify-center gap-1 mx-auto shadow-2xs"
                        title="Ver / modificar ausencias registradas (${item.fechas_faltas_json ? item.fechas_faltas_json.length : 0} fechas)">
                    <span>📅 ${Math.round(faltas)}d</span>
                    <span class="text-[10px] text-rose-700 font-black">(-${Math.round(dom)} dom)</span>
                </button>
            `;
        }
        return `
            <button type="button" id="btn-ausencias-${item.id}" onclick="abrirModalAusencias(${item.id})"
                    class="px-2 py-0.5 rounded-lg text-[11px] font-semibold text-slate-400 hover:text-blue-700 hover:bg-blue-50 border border-dashed border-slate-300 hover:border-blue-400 transition cursor-pointer flex items-center justify-center gap-1 mx-auto"
                    title="Registrar ausencias y domingos (Art. 173 CST)">
                <span>📅 0 d</span>
            </button>
        `;
    }

    // Renderizar la tabla completa
    function renderizarTabla() {
        const tbody = document.getElementById('tbody-nomina');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (detallesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="18" class="py-8 text-center text-slate-400 font-medium">No hay registros en esta nómina. Agrega un colaborador con el botón superior.</td></tr>';
            return;
        }

        detallesData.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.id = `fila-${item.id}`;
            tr.className = 'hover:bg-blue-50/50 transition border-b border-slate-100';

            tr.innerHTML = `
                <td class="py-1.5 px-2 text-center text-slate-400 font-mono text-[11px] border-r border-slate-100 td-sticky-num" style="left: 0;">${index + 1}</td>
                <td class="py-1.5 px-3 font-bold text-slate-900 border-r border-slate-100 td-sticky-nombre" style="left: 44px;">
                    <span class="block truncate max-w-[220px]" title="${item.nombre_empleado}">${item.nombre_empleado}</span>
                </td>
                <td class="py-1.5 px-3 text-slate-500 font-mono text-[11px] border-r border-slate-100">${item.cedula || '-'}</td>
                <td class="py-1.5 px-3 text-slate-600 text-[11px] border-r border-slate-100">
                    <span class="block truncate max-w-[140px]" title="${item.cargo}">${item.cargo || '-'}</span>
                </td>

                <!-- BÁSICO PACTADO -->
                <td class="py-1 px-2 text-right border-r border-slate-100 bg-slate-50/50">
                    <input type="number" step="1" value="${Math.round(item.salario_basico)}"
                           onchange="actualizarCelda(${item.id}, 'salario_basico', this.value)"
                           class="w-full text-right font-mono font-bold text-slate-900 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-1 py-0.5">
                </td>

                <!-- DÍAS LABORADOS -->
                <td class="py-1 px-1 text-center border-r border-slate-100 bg-blue-50/40">
                    <input type="number" min="0" max="30" step="1" value="${item.dias_laborados}" id="input-dias-${item.id}"
                           onchange="actualizarCelda(${item.id}, 'dias_laborados', this.value)"
                           class="w-full text-center font-mono font-black text-blue-900 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-0.5 py-0.5">
                </td>

                <!-- AUSENCIAS / ART. 173 -->
                <td class="py-1 px-1 text-center border-r border-slate-100 bg-amber-50/30">
                    ${renderizarBotonAusencias(item)}
                </td>

                <!-- BÁSICO DEVENGADO -->
                <td class="py-1.5 px-3 text-right font-mono text-slate-800 border-r border-slate-100" id="basico-dev-${item.id}">
                    ${formatoDinero(item.basico_devengado)}
                </td>

                <!-- AUXILIO TRANSPORTE -->
                <td class="py-1.5 px-3 text-right font-mono text-slate-800 border-r border-slate-100" id="aux-trans-${item.id}">
                    ${formatoDinero(item.auxilio_transporte_devengado)}
                </td>

                <!-- EXTRAS / BONOS -->
                <td class="py-1 px-1.5 text-right border-r border-slate-100">
                    <input type="number" step="1" value="${Math.round((item.horas_extras_recargos || 0) + (item.otros_devengados || 0))}"
                           onchange="actualizarCelda(${item.id}, 'horas_extras_recargos', this.value)"
                           class="w-full text-right font-mono text-slate-800 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-1 py-0.5">
                </td>

                <!-- TOTAL DEVENGADO -->
                <td class="py-1.5 px-3 text-right font-mono font-bold text-slate-900 border-r border-slate-100 bg-amber-50/30" id="total-dev-${item.id}">
                    ${formatoDinero(item.total_devengado)}
                </td>

                <!-- SALUD (4%) -->
                <td class="py-1.5 px-3 text-right font-mono text-rose-600 border-r border-slate-100" id="salud-${item.id}">
                    ${formatoDinero(item.deduccion_salud)}
                </td>

                <!-- PENSIÓN (4%) -->
                <td class="py-1.5 px-3 text-right font-mono text-rose-600 border-r border-slate-100" id="pension-${item.id}">
                    ${formatoDinero(item.deduccion_pension)}
                </td>

                <!-- OTRAS DEDUCCIONES -->
                <td class="py-1 px-1.5 text-right border-r border-slate-100">
                    <input type="number" step="1" value="${Math.round((item.retencion_fuente || 0) + (item.otras_deducciones || 0) + (item.deduccion_afsp || 0))}"
                           onchange="actualizarCelda(${item.id}, 'otras_deducciones', this.value)"
                           class="w-full text-right font-mono text-rose-700 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-rose-500 rounded px-1 py-0.5">
                </td>

                <!-- TOTAL DEDUCCIONES -->
                <td class="py-1.5 px-3 text-right font-mono font-bold text-rose-700 border-r border-slate-100 bg-rose-50/30" id="total-ded-${item.id}">
                    -${formatoDinero(item.total_deducciones)}
                </td>

                <!-- NETO A PAGAR -->
                <td class="py-1.5 px-3 text-right font-mono font-black text-emerald-700 text-xs border-r border-slate-100 bg-emerald-50/40" id="neto-${item.id}">
                    ${formatoDinero(item.neto_pagar)}
                </td>

                <!-- NOVEDAD / NOTA -->
                <td class="py-1 px-2 border-r border-slate-100">
                    <input type="text" value="${item.observaciones || ''}"
                           placeholder="Nota..."
                           onchange="actualizarCelda(${item.id}, 'observaciones', this.value)"
                           class="w-full text-xs text-slate-600 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-1 py-0.5">
                </td>

                <!-- ACCIONES -->
                <td class="py-1.5 px-2 text-center whitespace-nowrap space-x-1">
                    <button type="button" onclick="abrirModalAusencias(${item.id})"
                            class="inline-flex items-center justify-center p-1 rounded-lg text-amber-600 hover:bg-amber-100 transition cursor-pointer"
                            title="Gestionar Ausencias (Art. 173 CST)">
                        <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    </button>
                    <a href="/rrhh/nomina/comprobante/${item.id}/" target="_blank"
                       class="inline-flex items-center justify-center p-1 rounded-lg text-blue-600 hover:bg-blue-100 transition"
                       title="Imprimir Colilla de Pago">
                        <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"></polyline><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
                    </a>
                    <form method="POST" action="/rrhh/nomina/${PERIODO_ID}/eliminar-empleado/${item.id}/"
                          onsubmit="return confirm('¿Eliminar a ${item.nombre_empleado} de esta nómina?');" class="inline">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${obtenerCsrfToken()}">
                        <button type="submit" class="p-1 rounded-lg text-rose-500 hover:bg-rose-100 transition cursor-pointer" title="Eliminar fila">
                            <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                        </button>
                    </form>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Recalcular fila individual en tiempo real en JavaScript
    function recalcularFila(item) {
        const dias = parseFloat(item.dias_laborados) || 0;
        const domDesc = parseFloat(item.domingos_descontados) || 0;
        const salario = parseFloat(item.salario_basico) || 0;
        const extras = parseFloat(item.horas_extras_recargos) || 0;
        const otrasDctos = parseFloat(item.otras_deducciones) || 0;
        const esAprendiz = !!item.es_aprendiz_sena;

        // Básico proporcional a días liquidados (base 30)
        item.basico_devengado = (salario / 30.0) * dias;

        // Auxilio de transporte: solo si salario <= 2 SMMLV y no es aprendiz SENA
        // Nota legal: solo se descuentan las faltas físicas reales (los domingos no generan desplazamiento)
        if (!esAprendiz && salario <= (SMMLV_BASE * 2.0) && salario > 0) {
            item.auxilio_transporte_pactado = AUX_TRANSPORTE_BASE;
            const diasTransporte = Math.max(0, Math.min(30, dias + domDesc));
            item.auxilio_transporte_devengado = (AUX_TRANSPORTE_BASE / 30.0) * diasTransporte;
        } else {
            item.auxilio_transporte_pactado = 0;
            item.auxilio_transporte_devengado = 0;
        }

        item.total_devengado = item.basico_devengado + item.auxilio_transporte_devengado + extras;

        // IBC (Ingreso Base de Cotización, sin auxilio de transporte)
        const ibc = item.basico_devengado + extras;

        if (esAprendiz) {
            item.deduccion_salud = ibc * 0.04;
            item.deduccion_pension = 0;
            item.deduccion_afsp = 0;
        } else {
            item.deduccion_salud = ibc * 0.04;
            item.deduccion_pension = ibc * 0.04;
            if (ibc >= (SMMLV_BASE * 4.0)) {
                item.deduccion_afsp = ibc * 0.01;
            } else {
                item.deduccion_afsp = 0;
            }
        }

        item.total_deducciones = item.deduccion_salud + item.deduccion_pension + item.deduccion_afsp + otrasDctos;
        item.neto_pagar = item.total_devengado - item.total_deducciones;

        // Actualizar DOM de la fila
        const tdBasicoDev = document.getElementById(`basico-dev-${item.id}`);
        const tdAuxTrans = document.getElementById(`aux-trans-${item.id}`);
        const tdTotalDev = document.getElementById(`total-dev-${item.id}`);
        const tdSalud = document.getElementById(`salud-${item.id}`);
        const tdPension = document.getElementById(`pension-${item.id}`);
        const tdTotalDed = document.getElementById(`total-ded-${item.id}`);
        const tdNeto = document.getElementById(`neto-${item.id}`);
        const inputDias = document.getElementById(`input-dias-${item.id}`);

        if (tdBasicoDev) tdBasicoDev.textContent = formatoDinero(item.basico_devengado);
        if (tdAuxTrans) tdAuxTrans.textContent = formatoDinero(item.auxilio_transporte_devengado);
        if (tdTotalDev) tdTotalDev.textContent = formatoDinero(item.total_devengado);
        if (tdSalud) tdSalud.textContent = formatoDinero(item.deduccion_salud);
        if (tdPension) tdPension.textContent = formatoDinero(item.deduccion_pension);
        if (tdTotalDed) tdTotalDed.textContent = '-' + formatoDinero(item.total_deducciones);
        if (tdNeto) tdNeto.textContent = formatoDinero(item.neto_pagar);
        if (inputDias) inputDias.value = item.dias_laborados;

        // Actualizar botón de ausencias
        const btnAusencias = document.getElementById(`btn-ausencias-${item.id}`);
        if (btnAusencias) {
            btnAusencias.outerHTML = renderizarBotonAusencias(item);
        }
    }

    // Actualizar valor de celda editada manualmente
    function actualizarCelda(id, campo, valor) {
        const item = detallesData.find(d => d.id === id);
        if (!item) return;

        if (campo === 'observaciones') {
            item[campo] = valor;
        } else {
            item[campo] = parseFloat(valor) || 0;
        }

        recalcularFila(item);
        actualizarTotalesGenerales();
        marcarCambiosPendientes();
    }

    // Actualizar totales generales en la barra inferior
    function actualizarTotalesGenerales() {
        let totDev = 0;
        let totSalud = 0;
        let totPension = 0;
        let totDed = 0;
        let totNeto = 0;

        detallesData.forEach(item => {
            totDev += item.total_devengado || 0;
            totSalud += item.deduccion_salud || 0;
            totPension += item.deduccion_pension || 0;
            totDed += item.total_deducciones || 0;
            totNeto += item.neto_pagar || 0;
        });

        const elColab = document.getElementById('tot-colaboradores');
        const elDev = document.getElementById('tot-devengado');
        const elSalud = document.getElementById('tot-salud');
        const elPension = document.getElementById('tot-pension');
        const elDed = document.getElementById('tot-deducciones');
        const elNeto = document.getElementById('tot-neto');

        if (elColab) elColab.textContent = `${detallesData.length} personas`;
        if (elDev) elDev.textContent = '$' + formatoDinero(totDev);
        if (elSalud) elSalud.textContent = '$' + formatoDinero(totSalud);
        if (elPension) elPension.textContent = '$' + formatoDinero(totPension);
        if (elDed) elDed.textContent = '-$' + formatoDinero(totDed);
        if (elNeto) elNeto.textContent = '$' + formatoDinero(totNeto);
    }

    // Marcar indicador visual de cambios pendientes
    function marcarCambiosPendientes() {
        hayCambiosSinGuardar = true;
        const ind = document.getElementById('indicador-guardado');
        const txt = document.getElementById('texto-guardado');
        if (ind && txt) {
            ind.className = 'text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 bg-amber-100 text-amber-800 border border-amber-200';
            txt.textContent = '● Cambios sin guardar';
            ind.classList.remove('hidden');
        }
    }

    // Guardar cambios en el servidor vía AJAX
    function guardarCambiosEnServidor() {
        const btn = document.getElementById('btn-guardar-cambios');
        const ind = document.getElementById('indicador-guardado');
        const txt = document.getElementById('texto-guardado');

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span>⏳ Guardando...</span>';
        }

        const payload = {
            filas: detallesData.map(d => ({
                id: d.id,
                salario_basico: d.salario_basico,
                dias_laborados: d.dias_laborados,
                dias_incapacidad: d.dias_incapacidad,
                dias_no_remunerados: d.dias_no_remunerados,
                dias_faltas_injustificadas: d.dias_faltas_injustificadas || 0,
                domingos_descontados: d.domingos_descontados || 0,
                fechas_faltas_json: d.fechas_faltas_json || [],
                descontar_dominical: d.descontar_dominical !== false,
                horas_extras_recargos: d.horas_extras_recargos,
                otros_devengados: d.otros_devengados,
                retencion_fuente: d.retencion_fuente,
                otras_deducciones: d.otras_deducciones,
                observaciones: d.observaciones,
            }))
        };

        fetch(`/rrhh/nomina/${PERIODO_ID}/guardar/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': obtenerCsrfToken(),
            },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg><span>Guardar Cambios</span>';
            }
            if (data.status === 'ok') {
                hayCambiosSinGuardar = false;
                if (ind && txt) {
                    ind.className = 'text-xs font-bold px-3 py-1.5 rounded-lg flex items-center gap-1.5 bg-emerald-100 text-emerald-800 border border-emerald-200';
                    txt.textContent = '✓ Guardado exitoso';
                    setTimeout(() => {
                        if (!hayCambiosSinGuardar) ind.classList.add('hidden');
                    }, 3000);
                }
            } else {
                alert('Error al guardar: ' + (data.message || 'Error desconocido'));
            }
        })
        .catch(err => {
            console.error(err);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<span>Reintentar Guardar</span>';
            }
            alert('Ocurrió un error al guardar los cambios en el servidor.');
        });
    }

    // ==========================================
    // GESTIÓN DEL MODAL DE CALENDARIO DE AUSENCIAS
    // ==========================================

    function abrirModalAusencias(id) {
        const item = detallesData.find(d => d.id === id);
        if (!item) return;

        empleadoActualModal = item;
        fechasSeleccionadasModal = new Set(Array.isArray(item.fechas_faltas_json) ? item.fechas_faltas_json : []);
        descontarDominicalModal = item.descontar_dominical !== false;

        const infoEl = document.getElementById('modal-ausencias-empleado');
        if (infoEl) {
            infoEl.textContent = `Colaborador: ${item.nombre_empleado} | Cédula: ${item.cedula || 'N/A'} | Salario Básico: $${formatoDinero(item.salario_basico)}`;
        }

        const toggleEl = document.getElementById('toggle-descontar-dominical');
        if (toggleEl) {
            toggleEl.checked = descontarDominicalModal;
        }

        const tituloMes = document.getElementById('calendario-titulo-mes');
        if (tituloMes) {
            tituloMes.textContent = `${NOMBRES_MESES[PERIODO_MES - 1]} ${PERIODO_ANO}`;
        }

        renderizarCalendarioModal();
        actualizarResumenModal();

        const modal = document.getElementById('modalCalendarioAusencias');
        if (modal) modal.classList.remove('hidden');
    }

    function cerrarModalAusencias() {
        const modal = document.getElementById('modalCalendarioAusencias');
        if (modal) modal.classList.add('hidden');
        empleadoActualModal = null;
    }

    function alCambiarToggleDominical() {
        const toggleEl = document.getElementById('toggle-descontar-dominical');
        descontarDominicalModal = toggleEl ? toggleEl.checked : true;
        renderizarCalendarioModal();
        actualizarResumenModal();
    }

    function toggleFechaModal(fechaStr) {
        if (fechasSeleccionadasModal.has(fechaStr)) {
            fechasSeleccionadasModal.delete(fechaStr);
        } else {
            fechasSeleccionadasModal.add(fechaStr);
        }
        renderizarCalendarioModal();
        actualizarResumenModal();
    }

    function limpiarAusenciasModal() {
        fechasSeleccionadasModal.clear();
        renderizarCalendarioModal();
        actualizarResumenModal();
    }

    function calcularBalanceAusencias() {
        const faltas = fechasSeleccionadasModal.size;
        const semanasMap = new Map(); // key: mondayISO -> { monday, sunday, fechas: [] }

        fechasSeleccionadasModal.forEach(fechaStr => {
            const dateObj = parseDateISO(fechaStr);
            const mondayObj = getMondayOfWeek(dateObj);
            const sundayObj = getSundayOfWeek(mondayObj);
            const mondayKey = formatDateISO(mondayObj);

            if (!semanasMap.has(mondayKey)) {
                semanasMap.set(mondayKey, {
                    monday: mondayKey,
                    sunday: formatDateISO(sundayObj),
                    fechas: []
                });
            }
            semanasMap.get(mondayKey).fechas.push(fechaStr);
        });

        const numSemanas = semanasMap.size;
        const domingosPerdidos = descontarDominicalModal ? numSemanas : 0;
        const totalDiasDescontados = faltas + domingosPerdidos;
        const diasLaboradosLiquidados = Math.max(0, 30 - totalDiasDescontados);
        const diasTransporteLiquidados = Math.max(0, 30 - faltas);

        return {
            faltas,
            semanasMap,
            numSemanas,
            domingosPerdidos,
            totalDiasDescontados,
            diasLaboradosLiquidados,
            diasTransporteLiquidados
        };
    }

    function renderizarCalendarioModal() {
        const grid = document.getElementById('calendario-grid-dias');
        if (!grid) return;
        grid.innerHTML = '';
        grid.style.cssText = 'display: grid !important; grid-template-columns: repeat(7, minmax(0, 1fr)) !important; gap: 6px !important; width: 100% !important; box-sizing: border-box !important;';

        const ano = PERIODO_ANO;
        const mes = PERIODO_MES;
        const diasEnMes = new Date(ano, mes, 0).getDate();
        const primerDia = new Date(ano, mes - 1, 1);
        const offsetInicio = (primerDia.getDay() + 6) % 7; // Lun: 0, Mar: 1, ..., Dom: 6

        const balance = calcularBalanceAusencias();
        const domingosAfectadosSet = new Set();
        if (descontarDominicalModal) {
            balance.semanasMap.forEach(info => {
                domingosAfectadosSet.add(info.sunday);
            });
        }

        // Celdas vacías previas al día 1
        for (let i = 0; i < offsetInicio; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'calendario-dia-vacio';
            emptyCell.style.cssText = 'min-height: 52px; border-radius: 10px; background-color: #f8fafc; border: 1px dashed #e2e8f0; width: 100%; box-sizing: border-box;';
            grid.appendChild(emptyCell);
        }

        // Celdas de los días del mes
        for (let dia = 1; dia <= diasEnMes; dia++) {
            const fechaObj = new Date(ano, mes - 1, dia);
            const fechaStr = formatDateISO(fechaObj);
            const esDomingo = fechaObj.getDay() === 0;
            const esFalta = fechasSeleccionadasModal.has(fechaStr);
            const esDomingoPenalizado = domingosAfectadosSet.has(fechaStr);

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.dataset.fecha = fechaStr;
            btn.onclick = () => toggleFechaModal(fechaStr);
            btn.className = 'calendario-dia-celda';

            if (esFalta) {
                // Día marcado como falta injustificada
                btn.style.cssText = 'min-height: 52px; width: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 6px 3px; border-radius: 10px; background-color: #e11d48 !important; color: #ffffff !important; border: 2px solid #be123c !important; cursor: pointer; box-shadow: 0 2px 4px rgba(225, 29, 72, 0.3);';
                btn.innerHTML = `
                    <span style="font-size: 13px; font-weight: 800; line-height: 1;">${dia}</span>
                    <span style="font-size: 8px; font-weight: 800; text-transform: uppercase; background-color: rgba(0,0,0,0.25); color: #fff; padding: 2px 4px; border-radius: 4px; letter-spacing: 0.05em;">✕ Falta</span>
                `;
            } else if (esDomingo && esDomingoPenalizado) {
                // Domingo que se pierde según Art. 173 CST
                btn.style.cssText = 'min-height: 52px; width: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 6px 3px; border-radius: 10px; background-color: #fef3c7 !important; color: #78350f !important; border: 2px solid #f59e0b !important; cursor: pointer;';
                btn.title = 'Este descanso dominical se descontará por la falta injustificada ocurrida en la semana (Art. 173 CST)';
                btn.innerHTML = `
                    <span style="font-size: 13px; font-weight: 800; line-height: 1; color: #b91c1c;">${dia}</span>
                    <span style="font-size: 8px; font-weight: 900; text-transform: uppercase; background-color: #f59e0b; color: #0f172a; padding: 2px 3px; border-radius: 4px;">⚠️ Dcto Dom</span>
                `;
            } else if (esDomingo) {
                // Domingo regular de descanso
                btn.style.cssText = 'min-height: 52px; width: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 6px 3px; border-radius: 10px; background-color: #f1f5f9; color: #64748b; border: 1px solid #cbd5e1; cursor: pointer;';
                btn.title = 'Domingo (Descanso legal)';
                btn.innerHTML = `
                    <span style="font-size: 13px; font-weight: 700; line-height: 1;">${dia}</span>
                    <span style="font-size: 8px; font-weight: 600; color: #94a3b8;">Descanso</span>
                `;
            } else {
                // Día hábil estándar
                btn.style.cssText = 'min-height: 52px; width: 100%; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: space-between; padding: 6px 3px; border-radius: 10px; background-color: #ffffff; color: #1e293b; border: 1px solid #e2e8f0; cursor: pointer;';
                btn.innerHTML = `
                    <span style="font-size: 13px; font-weight: 700; line-height: 1;">${dia}</span>
                    <span style="font-size: 8px; font-weight: 500; color: #94a3b8;">Laborable</span>
                `;
            }

            grid.appendChild(btn);
        }
    }

    function actualizarResumenModal() {
        const balance = calcularBalanceAusencias();

        const elSemanas = document.getElementById('resumen-semanas-afectadas');
        const elFaltas = document.getElementById('resumen-dias-falta');
        const elDomingos = document.getElementById('resumen-domingos-perdidos');
        const elTotalDesc = document.getElementById('resumen-total-descuento');
        const elDiasPagar = document.getElementById('resumen-dias-pagar');
        const elTransDias = document.getElementById('resumen-transporte-dias');
        const elFechasLista = document.getElementById('resumen-fechas-lista');

        if (elSemanas) elSemanas.textContent = `${balance.numSemanas} semana(s) afectada(s)`;
        if (elFaltas) elFaltas.textContent = `${balance.faltas} día(s)`;
        if (elDomingos) elDomingos.textContent = `${balance.domingosPerdidos} domingo(s)`;
        if (elTotalDesc) elTotalDesc.textContent = `${balance.totalDiasDescontados} día(s)`;
        if (elDiasPagar) elDiasPagar.textContent = `${balance.diasLaboradosLiquidados} día(s)`;
        if (elTransDias) elTransDias.textContent = `${balance.diasTransporteLiquidados}`;

        if (elFechasLista) {
            if (balance.faltas === 0) {
                elFechasLista.innerHTML = '<span class="text-slate-400 italic">No hay ausencias seleccionadas. La liquidación se realizará sobre 30 días plenos.</span>';
            } else {
                const fechasOrdenadas = Array.from(fechasSeleccionadasModal).sort();
                let desgloseHTML = `<strong>Faltas registradas (${fechasOrdenadas.length}):</strong> ${fechasOrdenadas.join(', ')}`;
                if (balance.domingosPerdidos > 0) {
                    const domingosList = [];
                    balance.semanasMap.forEach(info => domingosList.push(info.sunday));
                    desgloseHTML += `<br><strong class="text-amber-300">Domingos descontados por ley (${balance.domingosPerdidos}):</strong> ${domingosList.join(', ')}`;
                }
                elFechasLista.innerHTML = desgloseHTML;
            }
        }
    }

    function aplicarAusenciasModal() {
        if (!empleadoActualModal) return;

        const balance = calcularBalanceAusencias();
        const fechasOrdenadas = Array.from(fechasSeleccionadasModal).sort();

        empleadoActualModal.fechas_faltas_json = fechasOrdenadas;
        empleadoActualModal.dias_faltas_injustificadas = balance.faltas;
        empleadoActualModal.domingos_descontados = balance.domingosPerdidos;
        empleadoActualModal.descontar_dominical = descontarDominicalModal;
        empleadoActualModal.dias_laborados = balance.diasLaboradosLiquidados;

        // Si hay ausencias y el campo de notas está vacío o solo tenía la nota previa, sugerir nota informativa
        if (balance.faltas > 0) {
            if (!empleadoActualModal.observaciones || empleadoActualModal.observaciones.includes('Ausencia:')) {
                empleadoActualModal.observaciones = `Ausencia: ${balance.faltas}d + ${balance.domingosPerdidos} dom. desc. (Art. 173 CST)`;
            }
        }

        recalcularFila(empleadoActualModal);
        actualizarTotalesGenerales();
        marcarCambiosPendientes();
        cerrarModalAusencias();
    }

    // Modales de agregar colaborador
    function abrirModalAgregarEmpleado() {
        const modal = document.getElementById('modalAgregarEmpleado');
        if (modal) modal.classList.remove('hidden');
    }

    function cerrarModalAgregarEmpleado() {
        const modal = document.getElementById('modalAgregarEmpleado');
        if (modal) modal.classList.add('hidden');
    }

    function autocompletarDesdeSelect() {
        const sel = document.getElementById('select-empleado-modal');
        if (!sel || !sel.value) return;
        const opt = sel.options[sel.selectedIndex];
        if (opt) {
            const cedula = opt.getAttribute('data-cedula') || '';
            const cargo = opt.getAttribute('data-cargo') || '';
            const salario = opt.getAttribute('data-salario') || '1750905';
            document.getElementById('modal-cedula').value = cedula;
            document.getElementById('modal-cargo').value = cargo;
            document.getElementById('modal-salario').value = salario;
            document.getElementById('modal-nombre-custom').value = '';
        }
    }

    // Exponer funciones necesarias globalmente
    window.guardarCambiosEnServidor = guardarCambiosEnServidor;
    window.abrirModalAgregarEmpleado = abrirModalAgregarEmpleado;
    window.cerrarModalAgregarEmpleado = cerrarModalAgregarEmpleado;
    window.autocompletarDesdeSelect = autocompletarDesdeSelect;
    window.actualizarCelda = actualizarCelda;
    window.formatoDinero = formatoDinero;

    // Exponer funciones del modal de ausencias
    window.abrirModalAusencias = abrirModalAusencias;
    window.cerrarModalAusencias = cerrarModalAusencias;
    window.alCambiarToggleDominical = alCambiarToggleDominical;
    window.limpiarAusenciasModal = limpiarAusenciasModal;
    window.aplicarAusenciasModal = aplicarAusenciasModal;
})();
