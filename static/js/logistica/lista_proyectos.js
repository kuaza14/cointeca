/**
 * COINTECA S.A.S. - Módulo de Logística
 * lista_proyectos.js - Búsqueda interactiva de proyectos, filtros y control de modales de creación.
 */

document.addEventListener("DOMContentLoaded", function () {
    const checkTodos = document.getElementById("checkTodosProyectos");
    const checksProyectos = document.querySelectorAll(".check-proyecto");
    const contador = document.getElementById("contadorSeleccionados");
    const btnInforme = document.getElementById("btnGenerarInforme");
    const formInforme = document.getElementById("formInformeConsolidado");

    // Modal nuevo proyecto
    const btnNuevo = document.getElementById("btnNuevoProyecto");
    const modalNuevo = document.getElementById("modalNuevoProyecto");
    const cerrarModal = document.getElementById("cerrarModalNuevo");
    const cancelarModal = document.getElementById("cancelarModalNuevo");
    const selectMacroLog = document.getElementById("macroproyecto_id");
    const selectTipoLog = document.getElementById("tipo");
    const lblNumeroLog = document.getElementById("lblNumeroEmcaliLogistica");
    const inputNumeroLog = document.getElementById("numero_emcali");
    const btnSubmitCrearLog = document.getElementById("btnSubmitCrearProyectoLogistica");
    const textoTituloModalLog = document.getElementById("textoTituloModalNuevoLogistica");
    const ayudaTipoLog = document.getElementById("ayudaTipoDinamicoLogistica");

    const OPCIONES_AP_LOG = [
        { valor: "AP_BARRIO", texto: "Alumbrado Público Barrio (AP)" },
        { valor: "AP_PARQUE", texto: "Alumbrado Público Parque / Cancha (AP)" },
        { valor: "AP", texto: "Alumbrado Público (General)" },
        { valor: "BT", texto: "Baja Tensión (BT)" }
    ];

    function actualizarOpcionesTipoNuevoLogistica(macroOpt) {
        if (!selectTipoLog) return;
        if (!macroOpt ||!macroOpt.value) {
            selectTipoLog.innerHTML = `
                <option value="">(Primero seleccione Macroproyecto o Circuito)</option>
                <option value="BT">Baja Tensión (BT)</option>
                <option value="AP_BARRIO">Alumbrado Público Barrio (AP)</option>
                <option value="AP_PARQUE">Alumbrado Público Parque / Cancha (AP)</option>
                <option value="AP">Alumbrado Público (General)</option>
                <option value="MT">Media Tensión (MT)</option>
            `;
            if (lblNumeroLog) lblNumeroLog.innerHTML = 'Número o Código de Proyecto / Maniobra <span class="text-red-600">*</span>';
            if (inputNumeroLog) inputNumeroLog.placeholder = "Ej: 9901, 001, etc.";
            if (btnSubmitCrearLog) btnSubmitCrearLog.textContent = "Crear Proyecto / Maniobra";
            if (textoTituloModalLog) textoTituloModalLog.textContent = "Nuevo Proyecto / Maniobra";
            if (ayudaTipoLog) { ayudaTipoLog.classList.add("hidden"); ayudaTipoLog.textContent = ""; }
            return;
        }

        const esMt = macroOpt.dataset.esMt === "1";
        const etiquetaHijo = macroOpt.dataset.etiquetaHijo || (esMt? "Maniobra": "Proyecto");

        if (esMt) {
            selectTipoLog.innerHTML = '<option value="MT" selected>Media Tensión (MT)</option>';
            if (lblNumeroLog) lblNumeroLog.innerHTML = 'Número o Código de ' + etiquetaHijo + ' <span class="text-red-600">*</span>';
            if (inputNumeroLog) inputNumeroLog.placeholder = "Ej: 001, MAN-01, etc.";
            if (btnSubmitCrearLog) btnSubmitCrearLog.textContent = "Crear " + etiquetaHijo;
            if (textoTituloModalLog) textoTituloModalLog.textContent = "Nueva " + etiquetaHijo;
            if (ayudaTipoLog) {
                ayudaTipoLog.className = "text-[11px] text-purple-700 font-semibold mt-1";
                ayudaTipoLog.textContent = " En un Circuito solo se pueden registrar maniobras de Media Tensión (MT).";
                ayudaTipoLog.classList.remove("hidden");
            }
        } else {
            let html = '<option value="">Seleccione tipo de AP…</option>';
            OPCIONES_AP_LOG.forEach(function(op) {
                html += '<option value="' + op.valor + '">' + op.texto + '</option>';
            });
            selectTipoLog.innerHTML = html;
            if (lblNumeroLog) lblNumeroLog.innerHTML = 'Número o Código de ' + etiquetaHijo + ' <span class="text-red-600">*</span>';
            if (inputNumeroLog) inputNumeroLog.placeholder = "Ej: 9901, AP-CANCHA-01, etc.";
            if (btnSubmitCrearLog) btnSubmitCrearLog.textContent = "Crear " + etiquetaHijo;
            if (textoTituloModalLog) textoTituloModalLog.textContent = "Nuevo " + etiquetaHijo;
            if (ayudaTipoLog) {
                ayudaTipoLog.className = "text-[11px] text-blue-700 font-semibold mt-1";
                ayudaTipoLog.textContent = " En un Macroproyecto solo se pueden registrar proyectos de Alumbrado Público (AP).";
                ayudaTipoLog.classList.remove("hidden");
            }
        }
    }

    if (selectMacroLog) {
        selectMacroLog.addEventListener("change", function() {
            const opt = selectMacroLog.selectedOptions[0];
            actualizarOpcionesTipoNuevoLogistica(opt);
        });
    }

    function abrirModal() {
        if (modalNuevo) {
            modalNuevo.classList.remove("hidden");
            modalNuevo.classList.add("flex");
            if (selectMacroLog && selectMacroLog.value) {
                actualizarOpcionesTipoNuevoLogistica(selectMacroLog.selectedOptions[0]);
            }
            const inputNom = document.getElementById("numero_emcali");
            if (inputNom) inputNom.focus();
        }
    }

    function cerrarModalFn() {
        if (modalNuevo) {
            modalNuevo.classList.add("hidden");
            modalNuevo.classList.remove("flex");
        }
    }

    if (btnNuevo) btnNuevo.addEventListener("click", abrirModal);
    if (cerrarModal) cerrarModal.addEventListener("click", cerrarModalFn);
    if (cancelarModal) cancelarModal.addEventListener("click", cerrarModalFn);

    function actualizarContador() {
        const seleccionados = document.querySelectorAll(".check-proyecto:checked").length;
        if (contador) contador.textContent = seleccionados;

        if (btnInforme) {
            if (seleccionados === 0) {
                btnInforme.classList.add("opacity-50", "cursor-not-allowed");
            } else {
                btnInforme.classList.remove("opacity-50", "cursor-not-allowed");
            }
        }
    }

    if (checkTodos) {
        checkTodos.addEventListener("change", function () {
            checksProyectos.forEach(chk => {
                const fila = chk.closest("tr");
                if (!fila || fila.style.display!== "none") {
                    chk.checked = checkTodos.checked;
                }
            });
            actualizarContador();
        });
    }

    checksProyectos.forEach(chk => {
        chk.addEventListener("change", function () {
            const checksVisibles = Array.from(checksProyectos).filter(chk => {
                const fila = chk.closest("tr");
                return!fila || fila.style.display!== "none";
            });
            const todosMarcados = checksVisibles.length > 0 && checksVisibles.every(c => c.checked);
            if (checkTodos) {
                checkTodos.checked = todosMarcados;
            }
            actualizarContador();
        });
    });

    if (formInforme) {
        formInforme.addEventListener("submit", function (e) {
            const seleccionados = document.querySelectorAll(".check-proyecto:checked").length;
            if (seleccionados === 0) {
                e.preventDefault();
                alert("Por favor selecciona al menos un proyecto marcando su casilla.");
            }
        });
    }

    // Buscador en tiempo real de Proyectos
    const inputBuscador = document.getElementById("buscadorProyectosLogistica");
    const btnLimpiar = document.getElementById("btnLimpiarBuscadorProyectos");
    const contadorVisibles = document.getElementById("contadorVisiblesProyectos");
    const filasProyectos = document.querySelectorAll(".fila-proyecto");

    if (inputBuscador) {
        function filtrarProyectos() {
            const query = inputBuscador.value.toLowerCase().trim();
            let visibles = 0;

            if (btnLimpiar) {
                if (query.length > 0) {
                    btnLimpiar.classList.remove("hidden");
                    btnLimpiar.classList.add("flex");
                } else {
                    btnLimpiar.classList.add("hidden");
                    btnLimpiar.classList.remove("flex");
                }
            }

            filasProyectos.forEach(function (fila) {
                const texto = fila.textContent.toLowerCase();
                if (texto.includes(query)) {
                    fila.style.display = "";
                    visibles++;
                } else {
                    fila.style.display = "none";
                }
            });

            if (contadorVisibles) {
                contadorVisibles.textContent = visibles;
            }
        }

        inputBuscador.addEventListener("input", filtrarProyectos);

        if (btnLimpiar) {
            btnLimpiar.addEventListener("click", function () {
                inputBuscador.value = "";
                filtrarProyectos();
                inputBuscador.focus();
            });
        }
    }

    actualizarContador();
});
