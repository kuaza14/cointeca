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
    if (!input || !preview) return;

    let historicosVal = parseInt(input.value, 10);
    if (isNaN(historicosVal) || historicosVal < 0) {
        historicosVal = 0;
    }
    const pendientes = Math.max(0, currentAcumulados - (historicosVal + currentEnSistema));
    preview.textContent = pendientes + (pendientes === 1 ? " día" : " días");
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
    if (elNombre) elNombre.textContent = "👤 " + nombre;

    const elAnios = document.getElementById("ajusteAnios");
    if (elAnios) elAnios.textContent = anios + (Number(anios) === 1 ? " año" : " años");

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

// EDITAR
function abrirEditar(id, periodo, fecha_inicio, dias, observaciones){
    const modal = document.getElementById("modalEditar");
    if (!modal) return;

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    document.getElementById("periodo").value = periodo;
    document.getElementById("fecha_inicio").value = fecha_inicio;
    document.getElementById("dias_tomados").value = dias;
    document.getElementById("observaciones").value = observaciones;

    document.getElementById("formEditar").action = "/rrhh/vacaciones/" + id + "/editar/";
}

function cerrarEditar(){
    const modal = document.getElementById("modalEditar");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
}

// ELIMINAR
function abrirEliminar(id){
    const modal = document.getElementById("modalEliminar");
    if (!modal) return;

    modal.classList.remove("hidden");
    modal.classList.add("flex");

    document.getElementById("formEliminar").action = "/rrhh/vacaciones/" + id + "/eliminar/";
}

function cerrarEliminar(){
    const modal = document.getElementById("modalEliminar");
    if (modal) {
        modal.classList.add("hidden");
        modal.classList.remove("flex");
    }
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
