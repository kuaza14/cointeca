/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * vacaciones.js - Filtrado en vivo de solicitudes de vacaciones por estado y empleado.
 */

// ==========================================
// AJUSTE DE VACACIONES HISTÓRICAS (PRE-SISTEMA)
// ==========================================
let currentAcumulados = 0;
let currentEnSistema = 0;

function actualizarPreviewPendientes() {
    const input = document.getElementById("inputDiasHistoricos");
    const preview = document.getElementById("previewPendientesFinal");
    if (!input ||!preview) return;

    let historicosVal = parseInt(input.value, 10);
    if (isNaN(historicosVal) || historicosVal < 0) {
        historicosVal = 0;
    }
    const pendientes = Math.max(0, currentAcumulados - (historicosVal + currentEnSistema));
    preview.textContent = pendientes + (pendientes === 1? " día": " días");
}

function abrirAjustarHistorico(id, nombre, anios, acumulados, historicos, enSistema) {
    const modal = document.getElementById("modalAjustarHistorico");
    if (!modal) return;

    currentAcumulados = Number(acumulados) || 0;
    currentEnSistema = Number(enSistema) || 0;
    const historicosNum = Number(historicos) || 0;

    const form = document.getElementById("formAjustarHistorico");
    if (form) {
        form.action = "/rrhh/vacaciones/" + id + "/ajustar-historico/";
    }

    const elNombre = document.getElementById("ajusteNombreEmpleado");
    if (elNombre) elNombre.textContent = " " + nombre;

    const elAnios = document.getElementById("ajusteAnios");
    if (elAnios) elAnios.textContent = anios + (Number(anios) === 1? " año": " años");

    const elAcum = document.getElementById("ajusteAcumulados");
    if (elAcum) elAcum.textContent = currentAcumulados + " días";

    const elEnSis = document.getElementById("ajusteEnSistema");
    if (elEnSis) elEnSis.textContent = currentEnSistema + " días";

    const elAntes = document.getElementById("ajustePendientesAntes");
    if (elAntes) {
        const antes = Math.max(0, currentAcumulados - (historicosNum + currentEnSistema));
        elAntes.textContent = antes + " días";
    }

    const input = document.getElementById("inputDiasHistoricos");
    if (input) {
        input.value = historicosNum;
    }

    actualizarPreviewPendientes();

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    setTimeout(() => {
        if (input) input.focus();
    }, 50);
}

function cerrarAjustarHistorico() {
    const modal = document.getElementById("modalAjustarHistorico");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}

// ==========================================
// EDICIÓN DE VACACIONES
// ==========================================
let currentEditarId = null;
let currentEditarNombre = "";
let currentEditarDiasOriginales = 0;
let currentEditarMaxDisponibles = 0;

function esFestivoOFinDeSemana(dStr) {
    if (typeof FESTIVOS_COLOMBIA!== "undefined" && Array.isArray(FESTIVOS_COLOMBIA)) {
        if (FESTIVOS_COLOMBIA.includes(dStr)) return true;
    }
    const parts = dStr.split("-").map(Number);
    const dt = new Date(parts[0], parts[1] - 1, parts[2]);
    return dt.getDay() === 0; // 0 = Domingo. Sábado (6) sí se labora en Cointeca.
}

function formatearFechaISO(dt) {
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, "0");
    const d = String(dt.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

function formatearFechaLegible(dt) {
    const meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
    const d = String(dt.getDate()).padStart(2, "0");
    const m = meses[dt.getMonth()];
    const y = dt.getFullYear();
    return `${d} ${m} ${y}`;
}

function calcularFechasHabiles(fechaInicioStr, diasTomados) {
    if (!fechaInicioStr || diasTomados <= 0) return null;
    const parts = fechaInicioStr.split("-").map(Number);
    let cur = new Date(parts[0], parts[1] - 1, parts[2]);

    // Si fecha de inicio cae en domingo o festivo, avanzar al primer día hábil
    while (esFestivoOFinDeSemana(formatearFechaISO(cur))) {
        cur.setDate(cur.getDate() + 1);
    }
    const fechaInicioEfectiva = new Date(cur);

    let contados = 0;
    while (contados < diasTomados) {
        if (!esFestivoOFinDeSemana(formatearFechaISO(cur))) {
            contados++;
        }
        if (contados < diasTomados) {
            cur.setDate(cur.getDate() + 1);
        }
    }
    const fechaFin = new Date(cur);

    let regreso = new Date(fechaFin);
    regreso.setDate(regreso.getDate() + 1);
    while (esFestivoOFinDeSemana(formatearFechaISO(regreso))) {
        regreso.setDate(regreso.getDate() + 1);
    }

    return {
        inicio: fechaInicioEfectiva,
        fin: fechaFin,
        regreso: regreso
    };
}

function actualizarCalculosEditar() {
    const inputFecha = document.getElementById("editarFechaInicio");
    const inputDias = document.getElementById("editarDiasTomados");
    const elInicio = document.getElementById("previewFechaInicio");
    const elFin = document.getElementById("previewFechaFin");
    const elRegreso = document.getElementById("previewFechaRegreso");
    const elSaldo = document.getElementById("previewSaldoResultante");
    const alertaExceso = document.getElementById("alertaExcesoDias");
    const btnGuardar = document.getElementById("btnGuardarEditar");

    if (!inputFecha ||!inputDias) return;

    const fechaStr = inputFecha.value;
    const dias = parseInt(inputDias.value, 10);

    if (!fechaStr || isNaN(dias) || dias <= 0) {
        if (elInicio) elInicio.textContent = "—";
        if (elFin) elFin.textContent = "—";
        if (elRegreso) elRegreso.textContent = "—";
        if (elSaldo) elSaldo.textContent = "—";
        if (btnGuardar) btnGuardar.disabled = true;
        return;
    }

    // Validar tope de días
    if (dias > currentEditarMaxDisponibles) {
        if (alertaExceso) alertaExceso.classList.remove("hidden");
        if (btnGuardar) btnGuardar.disabled = true;
    } else {
        if (alertaExceso) alertaExceso.classList.add("hidden");
        if (btnGuardar) btnGuardar.disabled = false;
    }

    const calc = calcularFechasHabiles(fechaStr, dias);
    if (calc) {
        if (elInicio) elInicio.textContent = formatearFechaLegible(calc.inicio);
        if (elFin) elFin.textContent = formatearFechaLegible(calc.fin);
        if (elRegreso) elRegreso.textContent = formatearFechaLegible(calc.regreso);
    }

    const saldoRestante = Math.max(0, currentEditarMaxDisponibles - dias);
    if (elSaldo) {
        elSaldo.textContent = saldoRestante + (saldoRestante === 1? " día": " días");
    }
}

function abrirEditarVacacion(id, nombre, periodo, fechaInicio, diasTomados, observaciones, pendientesActuales, acumulados) {
    const modal = document.getElementById("modalEditar");
    if (!modal) return;

    currentEditarId = id;
    currentEditarNombre = nombre || "el colaborador";
    currentEditarDiasOriginales = Number(diasTomados) || 0;
    currentEditarMaxDisponibles = (Number(pendientesActuales) || 0) + currentEditarDiasOriginales;

    const elNombre = document.getElementById("editarNombreEmpleado");
    if (elNombre) elNombre.textContent = nombre || "el colaborador";

    const elOriginales = document.getElementById("editarDiasOriginales");
    if (elOriginales) elOriginales.textContent = currentEditarDiasOriginales + " d";

    const elMaximo = document.getElementById("editarSaldoMaximo");
    if (elMaximo) elMaximo.textContent = currentEditarMaxDisponibles + " d";

    const inputId = document.getElementById("editarVacacionId");
    if (inputId) inputId.value = id;

    const form = document.getElementById("formEditar");
    if (form) form.action = "/rrhh/vacaciones/" + id + "/editar/";

    const inputPeriodo = document.getElementById("editarPeriodo");
    if (inputPeriodo) inputPeriodo.value = periodo || "";

    const inputFecha = document.getElementById("editarFechaInicio");
    if (inputFecha) inputFecha.value = fechaInicio || "";

    const inputDias = document.getElementById("editarDiasTomados");
    if (inputDias) {
        inputDias.value = currentEditarDiasOriginales;
        inputDias.max = currentEditarMaxDisponibles;
    }

    const inputObs = document.getElementById("editarObservaciones");
    if (inputObs) inputObs.value = observaciones || "";

    actualizarCalculosEditar();

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function cerrarEditar() {
    const modal = document.getElementById("modalEditar");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}

// Abrir eliminación directamente desde el modal de edición
function abrirEliminarDesdeEditar() {
    if (!currentEditarId) return;
    cerrarEditar();
    abrirEliminarVacacion(currentEditarId, currentEditarNombre, currentEditarDiasOriginales);
}

// Alias para compatibilidad
function abrirEditar(id, periodo, fecha_inicio, dias, observaciones) {
    abrirEditarVacacion(id, "Colaborador", periodo, fecha_inicio, dias, observaciones, 0, 0);
}

// ==========================================
// ELIMINACIÓN DE VACACIONES
// ==========================================
function abrirEliminarVacacion(id, nombre, dias) {
    const modal = document.getElementById("modalEliminar");
    if (!modal) return;

    const form = document.getElementById("formEliminar");
    if (form) form.action = "/rrhh/vacaciones/" + id + "/eliminar/";

    const elNombre = document.getElementById("eliminarNombreEmpleado");
    if (elNombre) elNombre.textContent = nombre || "el colaborador";

    const elDias = document.getElementById("eliminarDiasReintegro");
    if (elDias) elDias.textContent = dias || 0;

    modal.classList.remove("hidden");
    modal.classList.add("flex");
}

function cerrarEliminar() {
    const modal = document.getElementById("modalEliminar");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}

function abrirEliminar(id) {
    abrirEliminarVacacion(id, "Colaborador", 0);
}

document.addEventListener("DOMContentLoaded", function() {
    // Buscador en vivo
    const buscador = document.getElementById("buscarEmpleado");
    const contador = document.getElementById("contadorResultados");
    const filas = document.querySelectorAll(".fila-empleado");

    if (buscador && filas.length > 0) {
        buscador.addEventListener("input", function() {
            const texto = this.value.toLowerCase().trim();
            let visibles = 0;

            filas.forEach(function(fila) {
                const contenido = fila.textContent.toLowerCase();
                if (contenido.includes(texto)) {
                    fila.style.display = "";
                    visibles++;
                } else {
                    fila.style.display = "none";
                }
            });

            if (contador) {
                contador.textContent = visibles;
            }
        });
    }

    // Input reactivo en modal de ajuste histórico
    const inputHist = document.getElementById("inputDiasHistoricos");
    if (inputHist) {
        inputHist.addEventListener("input", actualizarPreviewPendientes);
        inputHist.addEventListener("keyup", actualizarPreviewPendientes);
        inputHist.addEventListener("change", actualizarPreviewPendientes);
    }

    // Inputs reactivos en modal de edición de vacaciones
    const inputEditFecha = document.getElementById("editarFechaInicio");
    const inputEditDias = document.getElementById("editarDiasTomados");
    if (inputEditFecha) {
        inputEditFecha.addEventListener("change", actualizarCalculosEditar);
        inputEditFecha.addEventListener("input", actualizarCalculosEditar);
    }
    if (inputEditDias) {
        inputEditDias.addEventListener("input", actualizarCalculosEditar);
        inputEditDias.addEventListener("keyup", actualizarCalculosEditar);
        inputEditDias.addEventListener("change", actualizarCalculosEditar);
    }

    // Cierre al hacer click en el backdrop oscuro
    const modals = [
        { id: "modalAjustarHistorico", close: cerrarAjustarHistorico },
        { id: "modalEditar", close: cerrarEditar },
        { id: "modalEliminar", close: cerrarEliminar }
    ];

    modals.forEach(({ id, close }) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("click", function(e) {
                if (e.target === el) {
                    close();
                }
            });
        }
    });

    // Tecla Escape para cerrar modales
    window.addEventListener("keydown", function(e) {
        if (e.key === "Escape") {
            cerrarAjustarHistorico();
            cerrarEditar();
            cerrarEliminar();
        }
    });
});
