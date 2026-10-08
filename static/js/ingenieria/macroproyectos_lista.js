/**
 * COINTECA S.A.S. - Módulo de Ingeniería
 * macroproyectos_lista.js - Control de tarjetas colapsables de macroproyectos y búsqueda en ingeniería.
 */

(function () {
    // ==========================================
    // BUSCADOR EN TIEMPO REAL
    // ==========================================
    const inputBuscador = document.getElementById("buscadorMacroproyectos");
    const btnLimpiar = document.getElementById("btnLimpiarBuscador");
    const filas = document.querySelectorAll(".fila-macroproyecto");
    const contadorVisibles = document.getElementById("contadorVisibles");
    const sinResultadosLive = document.getElementById("sinResultadosLive");

    if (inputBuscador) {
        function filtrarMacroproyectos() {
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

            filas.forEach(function (fila) {
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

            if (sinResultadosLive) {
                if (visibles === 0 && filas.length > 0) {
                    sinResultadosLive.classList.remove("hidden");
                } else {
                    sinResultadosLive.classList.add("hidden");
                }
            }
        }

        inputBuscador.addEventListener("input", filtrarMacroproyectos);

        if (btnLimpiar) {
            btnLimpiar.addEventListener("click", function () {
                inputBuscador.value = "";
                filtrarMacroproyectos();
                inputBuscador.focus();

                if (window.location.search.includes("q=")) {
                    window.location.href = window.location.pathname;
                }
            });
        }
    }

    // ==========================================
    // MODAL NUEVO MACROPROYECTO / CIRCUITO
    // ==========================================
    const modalMacro = document.getElementById("modalMacroproyecto");
    const btnNuevoMacro = document.getElementById("btnNuevoMacro");
    const btnCerrarMacro = document.getElementById("cerrarModalMacro");
    const btnCancelarMacro = document.getElementById("cancelarModalMacro");
    const primerCampoMacro = document.getElementById("nombre_macro");
    const selectTipoMacro = document.getElementById("tipo_macro");
    const tituloModalMacro = document.getElementById("tituloModalMacro");
    const lblNombreMacro = document.getElementById("lblNombreMacro");
    const inputNombreMacro = document.getElementById("nombre_macro");
    const btnSubmitCrearMacro = document.getElementById("btnSubmitCrearMacro");

    function actualizarLabelsCrearMacro(tipo) {
        if (tipo === "MT") {
            if (tituloModalMacro) tituloModalMacro.innerHTML = "<span>⚡</span> Nuevo Circuito (Media Tensión)";
            if (lblNombreMacro) lblNombreMacro.innerHTML = 'Nombre del Circuito <span class="text-red-600">*</span>';
            if (inputNombreMacro) inputNombreMacro.placeholder = "Ej: Circuito San Nicolás, Circuito Aguablanca...";
            if (btnSubmitCrearMacro) btnSubmitCrearMacro.textContent = "Crear Circuito";
        } else {
            if (tituloModalMacro) tituloModalMacro.innerHTML = "<span>🏢</span> Nuevo Macroproyecto (Alumbrado Público)";
            if (lblNombreMacro) lblNombreMacro.innerHTML = 'Nombre del Macroproyecto <span class="text-red-600">*</span>';
            if (inputNombreMacro) inputNombreMacro.placeholder = "Ej: Macroproyecto Ciudad Córdoba...";
            if (btnSubmitCrearMacro) btnSubmitCrearMacro.textContent = "Crear Macroproyecto";
        }
    }

    if (selectTipoMacro) {
        selectTipoMacro.addEventListener("change", function() {
            actualizarLabelsCrearMacro(this.value);
        });
    }

    function abrirMacro() {
        modalMacro.classList.remove("hidden");
        modalMacro.classList.add("flex");
        if (selectTipoMacro) {
            actualizarLabelsCrearMacro(selectTipoMacro.value);
        }
        if (primerCampoMacro) primerCampoMacro.focus();
    }

    function cerrarMacro() {
        modalMacro.classList.remove("flex");
        modalMacro.classList.add("hidden");
        if (btnNuevoMacro) btnNuevoMacro.focus();
    }

    if (btnNuevoMacro) btnNuevoMacro.addEventListener("click", abrirMacro);
    if (btnCerrarMacro) btnCerrarMacro.addEventListener("click", cerrarMacro);
    if (btnCancelarMacro) btnCancelarMacro.addEventListener("click", cerrarMacro);

    if (modalMacro) {
        modalMacro.addEventListener("click", function (e) {
            if (e.target === modalMacro) cerrarMacro();
        });
    }

    // ==========================================
    // MODAL EDITAR MACROPROYECTO
    // ==========================================
    const modalEditar = document.getElementById("modalEditarMacroproyecto");
    const formEditar = document.getElementById("formEditarMacroproyecto");
    const selectEditTipoMacro = document.getElementById("edit_tipo_macro");
    const editNombre = document.getElementById("edit_nombre_macro");
    const editDescripcion = document.getElementById("edit_descripcion_macro");
    const editEstado = document.getElementById("edit_estado_macro");
    const textoTituloModalEditarMacro = document.getElementById("textoTituloModalEditarMacro");
    const lblEditNombreMacro = document.getElementById("lblEditNombreMacro");
    const btnSubmitEditarMacro = document.getElementById("btnSubmitEditarMacro");
    const btnCerrarEditar = document.getElementById("cerrarModalEditarMacro");
    const btnCancelarEditar = document.getElementById("cancelarModalEditarMacro");

    function actualizarLabelsEditarMacro(tipo) {
        if (tipo === "MT") {
            if (textoTituloModalEditarMacro) textoTituloModalEditarMacro.textContent = "Editar Circuito (Media Tensión)";
            if (lblEditNombreMacro) lblEditNombreMacro.innerHTML = 'Nombre del Circuito <span class="text-red-600">*</span>';
            if (btnSubmitEditarMacro) btnSubmitEditarMacro.textContent = "Guardar Circuito";
        } else {
            if (textoTituloModalEditarMacro) textoTituloModalEditarMacro.textContent = "Editar Macroproyecto (Alumbrado Público)";
            if (lblEditNombreMacro) lblEditNombreMacro.innerHTML = 'Nombre del Macroproyecto <span class="text-red-600">*</span>';
            if (btnSubmitEditarMacro) btnSubmitEditarMacro.textContent = "Guardar Macroproyecto";
        }
    }

    if (selectEditTipoMacro) {
        selectEditTipoMacro.addEventListener("change", function() {
            actualizarLabelsEditarMacro(this.value);
        });
    }

    function abrirEditar(btn) {
        const id = btn.dataset.id;
        const tipo = btn.dataset.tipo || "AP";
        const nombre = btn.dataset.nombre || "";
        const descripcion = btn.dataset.descripcion || "";
        const estado = btn.dataset.estado || "Planeación";

        formEditar.action = "/ingenieria/macroproyectos/" + id + "/editar/";
        if (selectEditTipoMacro) selectEditTipoMacro.value = tipo;
        editNombre.value = nombre;
        editDescripcion.value = descripcion;
        editEstado.value = estado;

        actualizarLabelsEditarMacro(tipo);

        modalEditar.classList.remove("hidden");
        modalEditar.classList.add("flex");
        editNombre.focus();
    }

    function cerrarEditar() {
        modalEditar.classList.remove("flex");
        modalEditar.classList.add("hidden");
    }

    document.querySelectorAll(".btnEditarMacro").forEach(function(btn) {
        btn.addEventListener("click", function() {
            abrirEditar(btn);
        });
    });

    if (btnCerrarEditar) btnCerrarEditar.addEventListener("click", cerrarEditar);
    if (btnCancelarEditar) btnCancelarEditar.addEventListener("click", cerrarEditar);
    if (modalEditar) {
        modalEditar.addEventListener("click", function(e) {
            if (e.target === modalEditar) cerrarEditar();
        });
    }

    // ==========================================
    // MODAL ELIMINAR MACROPROYECTO
    // ==========================================
    const modalEliminar = document.getElementById("modalEliminarMacroproyecto");
    const formEliminar = document.getElementById("formEliminarMacroproyecto");
    const deleteNombre = document.getElementById("deleteMacroNombre");
    const deleteProyectosCount = document.getElementById("deleteMacroProyectosCount");
    const deleteTextoTipoMacro = document.getElementById("deleteTextoTipoMacro");
    const deleteTextoHijosPlural = document.getElementById("deleteTextoHijosPlural");
    const btnCerrarEliminar = document.getElementById("cerrarModalEliminarMacro");
    const btnCancelarEliminar = document.getElementById("cancelarModalEliminarMacro");

    function abrirEliminar(btn) {
        const id = btn.dataset.id;
        const nombre = btn.dataset.nombre || "";
        const proyectosCount = btn.dataset.proyectos || "0";
        const etiqueta = btn.dataset.etiqueta || "Macroproyecto";
        const hijosPlural = btn.dataset.etiquetaHijosPlural || "proyectos";

        formEliminar.action = "/ingenieria/macroproyectos/" + id + "/eliminar/";
        deleteNombre.textContent = nombre;
        deleteProyectosCount.textContent = proyectosCount;

        if (deleteTextoTipoMacro) {
            deleteTextoTipoMacro.textContent = (etiqueta.toLowerCase().includes("circuito") ? "el circuito" : "el macroproyecto");
        }
        if (deleteTextoHijosPlural) {
            deleteTextoHijosPlural.textContent = hijosPlural;
        }

        modalEliminar.classList.remove("hidden");
        modalEliminar.classList.add("flex");
    }

    function cerrarEliminar() {
        modalEliminar.classList.remove("flex");
        modalEliminar.classList.add("hidden");
    }

    document.querySelectorAll(".btnEliminarMacro").forEach(function(btn) {
        btn.addEventListener("click", function() {
            abrirEliminar(btn);
        });
    });

    if (btnCerrarEliminar) btnCerrarEliminar.addEventListener("click", cerrarEliminar);
    if (btnCancelarEliminar) btnCancelarEliminar.addEventListener("click", cerrarEliminar);
    if (modalEliminar) {
        modalEliminar.addEventListener("click", function(e) {
            if (e.target === modalEliminar) cerrarEliminar();
        });
    }

    // ==========================================
    // MODAL IMPRIMIR FORMATO POSTE A POSTE
    // ==========================================
    const modalImprimir = document.getElementById("modalImprimirFormato");
    const btnAbrirModalImprimir = document.getElementById("btnAbrirModalImprimir");
    const btnCerrarModalImprimir = document.getElementById("cerrarModalImprimir");
    const btnCerrarModalImprimirFooter = document.getElementById("btnCerrarModalImprimirFooter");
    const buscadorModal = document.getElementById("buscadorModalImprimir");
    const btnLimpiarModal = document.getElementById("btnLimpiarBuscadorModal");
    const itemsProyectos = document.querySelectorAll(".item-proyecto-imprimir");
    const contadorModal = document.getElementById("contadorModalImprimir");
    const sinResultadosModal = document.getElementById("sinResultadosModalImprimir");

    function abrirModalImprimir() {
        if (!modalImprimir) return;
        modalImprimir.classList.remove("hidden");
        modalImprimir.classList.add("flex");
        if (buscadorModal) {
            buscadorModal.value = "";
            filtrarModalImprimir();
            setTimeout(function() { buscadorModal.focus(); }, 50);
        }
    }

    function cerrarModalImprimir() {
        if (!modalImprimir) return;
        modalImprimir.classList.remove("flex");
        modalImprimir.classList.add("hidden");
        if (btnAbrirModalImprimir) btnAbrirModalImprimir.focus();
    }

    function filtrarModalImprimir() {
        if (!buscadorModal) return;
        const q = buscadorModal.value.toLowerCase().trim();
        let visibles = 0;

        if (btnLimpiarModal) {
            if (q.length > 0) {
                btnLimpiarModal.classList.remove("hidden");
                btnLimpiarModal.classList.add("flex");
            } else {
                btnLimpiarModal.classList.add("hidden");
                btnLimpiarModal.classList.remove("flex");
            }
        }

        itemsProyectos.forEach(function (item) {
            const numero = item.dataset.numero || "";
            const tipo = item.dataset.tipo || "";
            const macro = item.dataset.macro || "";

            if (numero.includes(q) || tipo.includes(q) || macro.includes(q)) {
                item.style.display = "";
                visibles++;
            } else {
                item.style.display = "none";
            }
        });

        if (contadorModal) {
            contadorModal.textContent = visibles;
        }

        if (sinResultadosModal) {
            if (visibles === 0 && itemsProyectos.length > 0) {
                sinResultadosModal.classList.remove("hidden");
            } else {
                sinResultadosModal.classList.add("hidden");
            }
        }
    }

    if (btnAbrirModalImprimir) btnAbrirModalImprimir.addEventListener("click", abrirModalImprimir);
    if (btnCerrarModalImprimir) btnCerrarModalImprimir.addEventListener("click", cerrarModalImprimir);
    if (btnCerrarModalImprimirFooter) btnCerrarModalImprimirFooter.addEventListener("click", cerrarModalImprimir);

    if (buscadorModal) {
        buscadorModal.addEventListener("input", filtrarModalImprimir);
        buscadorModal.addEventListener("keydown", function(e) {
            if (e.key === "Enter") {
                e.preventDefault();
                // Abrir la primera coincidencia visible
                for (let i = 0; i < itemsProyectos.length; i++) {
                    const item = itemsProyectos[i];
                    if (item.style.display !== "none") {
                        const link = item.querySelector(".btn-imprimir-accion");
                        if (link) {
                            window.open(link.href, "_blank");
                            break;
                        }
                    }
                }
            }
        });
    }

    if (btnLimpiarModal) {
        btnLimpiarModal.addEventListener("click", function () {
            buscadorModal.value = "";
            filtrarModalImprimir();
            buscadorModal.focus();
        });
    }

    if (modalImprimir) {
        modalImprimir.addEventListener("click", function (e) {
            if (e.target === modalImprimir) cerrarModalImprimir();
        });
    }

    // Cerrar con Escape cualquier modal
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            if (modalMacro && !modalMacro.classList.contains("hidden")) cerrarMacro();
            if (modalEditar && !modalEditar.classList.contains("hidden")) cerrarEditar();
            if (modalEliminar && !modalEliminar.classList.contains("hidden")) cerrarEliminar();
            if (modalImprimir && !modalImprimir.classList.contains("hidden")) cerrarModalImprimir();
        }
    });
})();
