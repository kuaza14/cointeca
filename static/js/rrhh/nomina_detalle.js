/**
 * COINTECA S.A.S. - Recursos Humanos
 * nomina_detalle.js - Matriz interactiva de nómina en vivo, recálculos en navegador y persistencia AJAX.
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

    // Estado local de los registros de empleados
    let detallesData = [];
    let hayCambiosSinGuardar = false;

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

    // Renderizar la tabla completa
    function renderizarTabla() {
        const tbody = document.getElementById('tbody-nomina');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (detallesData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="17" class="py-8 text-center text-slate-400 font-medium">No hay registros en esta nómina. Agrega un colaborador con el botón superior.</td></tr>';
            return;
        }

        detallesData.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.id = `fila-${item.id}`;
            tr.className = 'hover:bg-blue-50/50 transition border-b border-slate-100';

            tr.innerHTML = `
                <td class="py-1.5 px-3 text-center text-slate-400 font-mono text-[11px] border-r border-slate-100">${index + 1}</td>
                <td class="py-1.5 px-3 font-bold text-slate-900 border-r border-slate-100">
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
                    <input type="number" min="0" max="30" step="1" value="${item.dias_laborados}"
                           onchange="actualizarCelda(${item.id}, 'dias_laborados', this.value)"
                           class="w-full text-center font-mono font-black text-blue-900 bg-transparent outline-none focus:bg-white focus:ring-1 focus:ring-blue-500 rounded px-0.5 py-0.5">
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
                    <input type="number" step="1" value="${Math.round(item.horas_extras_recargos + item.otros_devengados)}"
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
                    <input type="number" step="1" value="${Math.round(item.retencion_fuente + item.otras_deducciones + item.deduccion_afsp)}"
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
        const salario = parseFloat(item.salario_basico) || 0;
        const extras = parseFloat(item.horas_extras_recargos) || 0;
        const otrasDctos = parseFloat(item.otras_deducciones) || 0;
        const esAprendiz = !!item.es_aprendiz_sena;

        // Básico proporcional a días trabajados (base 30)
        item.basico_devengado = (salario / 30.0) * dias;

        // Auxilio de transporte: solo si salario <= 2 SMMLV y no es aprendiz SENA
        if (!esAprendiz && salario <= (SMMLV_BASE * 2.0) && salario > 0) {
            item.auxilio_transporte_pactado = AUX_TRANSPORTE_BASE;
            item.auxilio_transporte_devengado = (AUX_TRANSPORTE_BASE / 30.0) * dias;
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

        if (tdBasicoDev) tdBasicoDev.textContent = formatoDinero(item.basico_devengado);
        if (tdAuxTrans) tdAuxTrans.textContent = formatoDinero(item.auxilio_transporte_devengado);
        if (tdTotalDev) tdTotalDev.textContent = formatoDinero(item.total_devengado);
        if (tdSalud) tdSalud.textContent = formatoDinero(item.deduccion_salud);
        if (tdPension) tdPension.textContent = formatoDinero(item.deduccion_pension);
        if (tdTotalDed) tdTotalDed.textContent = '-' + formatoDinero(item.total_deducciones);
        if (tdNeto) tdNeto.textContent = formatoDinero(item.neto_pagar);
    }

    // Actualizar valor de celda editada
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

    // Exponer funciones necesarias globalmente para llamadas desde atributos HTML inline
    window.guardarCambiosEnServidor = guardarCambiosEnServidor;
    window.abrirModalAgregarEmpleado = abrirModalAgregarEmpleado;
    window.cerrarModalAgregarEmpleado = cerrarModalAgregarEmpleado;
    window.autocompletarDesdeSelect = autocompletarDesdeSelect;
    window.actualizarCelda = actualizarCelda;
    window.formatoDinero = formatoDinero;
})();
