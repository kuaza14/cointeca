/**
 * COINTECA S.A.S. - Módulo de Ingeniería
 * lista_proyectos.js - Búsqueda interactiva de proyectos de ingeniería, filtros y control de modales de creación.
 */

(function () {
    // ==========================================
    // BUSCADOR EN TIEMPO REAL
    // ==========================================
    const inputBuscador = document.getElementById("buscadorProyectos");
    const btnLimpiar = document.getElementById("btnLimpiarBuscador");
    const filas = document.querySelectorAll(".fila-proyecto");
    const contadorVisibles = document.getElementById("contadorVisibles");
    const sinResultadosLive = document.getElementById("sinResultadosLive");

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

        inputBuscador.addEventListener("input", filtrarProyectos);

        if (btnLimpiar) {
            btnLimpiar.addEventListener("click", function () {
                inputBuscador.value = "";
                filtrarProyectos();
                inputBuscador.focus();

                if (window.location.search.includes("q=")) {
                    window.location.href = window.location.pathname;
                }
            });
        }
    }

    // ==========================================
    // OPCIONES DE TIPO (AP vs MT)
    // ==========================================
    const OPCIONES_AP = [
        { valor: "AP_BARRIO", texto: "Alumbrado Público Barrio (AP)" },
        { valor: "AP_PARQUE", texto: "Alumbrado Público Parque / Cancha (AP)" },
        { valor: "AP", texto: "Alumbrado Público (General)" },
        { valor: "BT", texto: "Baja Tensión (BT)" }
    ];

    const OPCIONES_MT = [
        { valor: "MT", texto: "Media Tensión (MT)" }
    ];

    // ==========================================
    // MODAL NUEVO PROYECTO
    // ==========================================
    const modal = document.getElementById("modalProyecto");
    const btnNuevo = document.getElementById("btnNuevoProyecto");
    const btnCerrar = document.getElementById("cerrarModal");
    const btnCancelar = document.getElementById("cancelarModal");
    const primerCampo = document.getElementById("numero_emcali");
    const selectMacro = document.getElementById("macroproyecto_id");
    const selectTipo = document.getElementById("tipo");
    const lblNumero = document.getElementById("lblNumeroEmcali");
    const btnSubmitCrear = document.getElementById("btnSubmitCrearProyecto");
    const textoTituloModal = document.getElementById("textoTituloModalProyecto");
    const ayudaTipo = document.getElementById("ayudaTipoDinamico");

    function actualizarOpcionesTipoNuevo(macroOpt) {
        if (!selectTipo) return;
        const contenedorCampoCointeca = document.getElementById("contenedorCampoCointeca");
        const inputNumeroCointeca = document.getElementById("numero_cointeca");

        if (!macroOpt || !macroOpt.value) {
            selectTipo.innerHTML = `
                <option value="">(Primero seleccione Macroproyecto o Circuito)</option>
                <option value="BT">Baja Tensión (BT)</option>
                <option value="AP_BARRIO">Alumbrado Público Barrio (AP)</option>
                <option value="AP_PARQUE">Alumbrado Público Parque / Cancha (AP)</option>
                <option value="AP">Alumbrado Público (General)</option>
                <option value="MT">Media Tensión (MT)</option>
            `;
            if (lblNumero) lblNumero.innerHTML = 'Número o Código de Proyecto / Maniobra <span class="text-red-600">*</span>';
            if (primerCampo) primerCampo.placeholder = "Ej: 2024-BT-001, 001, etc.";
            if (btnSubmitCrear) btnSubmitCrear.textContent = "Crear Proyecto / Maniobra";
            if (textoTituloModal) textoTituloModal.textContent = "Nuevo Proyecto / Maniobra";
            if (ayudaTipo) { ayudaTipo.classList.add("hidden"); ayudaTipo.textContent = ""; }
            if (contenedorCampoCointeca) {
                contenedorCampoCointeca.classList.add("hidden");
                if (inputNumeroCointeca) inputNumeroCointeca.value = "";
            }
            return;
        }

        const esMt = macroOpt.dataset.esMt === "1";
        const etiquetaHijo = macroOpt.dataset.etiquetaHijo || (esMt ? "Maniobra" : "Proyecto");
        const etiquetaPadre = macroOpt.dataset.etiqueta || (esMt ? "Circuito" : "Macroproyecto");

        if (esMt) {
            // CIRCUITO -> Solo MT
            selectTipo.innerHTML = '<option value="MT" selected>Media Tensión (MT)</option>';
            if (lblNumero) lblNumero.innerHTML = 'Número Maniobra EMCALI <span class="text-red-600">*</span>';
            if (primerCampo) primerCampo.placeholder = "Ej: 001, MAN-01, etc.";
            if (contenedorCampoCointeca) contenedorCampoCointeca.classList.remove("hidden");
            if (btnSubmitCrear) btnSubmitCrear.textContent = "Crear " + etiquetaHijo;
            if (textoTituloModal) textoTituloModal.textContent = "Nueva " + etiquetaHijo;
            if (ayudaTipo) {
                ayudaTipo.className = "text-[11px] text-purple-700 font-semibold mt-1";
                ayudaTipo.textContent = "⚡ En un Circuito solo se pueden registrar maniobras de Media Tensión (MT).";
                ayudaTipo.classList.remove("hidden");
            }
        } else {
            // MACROPROYECTO -> Solo AP
            let html = '<option value="">Seleccione tipo de AP…</option>';
            OPCIONES_AP.forEach(function(op) {
                html += '<option value="' + op.valor + '">' + op.texto + '</option>';
            });
            selectTipo.innerHTML = html;
            if (lblNumero) lblNumero.innerHTML = 'Número Proyecto EMCALI <span class="text-red-600">*</span>';
            if (primerCampo) primerCampo.placeholder = "Ej: 2024-BT-001, AP-CANCHA-01, etc.";
            if (contenedorCampoCointeca) {
                contenedorCampoCointeca.classList.add("hidden");
                if (inputNumeroCointeca) inputNumeroCointeca.value = "";
            }
            if (btnSubmitCrear) btnSubmitCrear.textContent = "Crear " + etiquetaHijo;
            if (textoTituloModal) textoTituloModal.textContent = "Nuevo " + etiquetaHijo;
            if (ayudaTipo) {
                ayudaTipo.className = "text-[11px] text-blue-700 font-semibold mt-1";
                ayudaTipo.textContent = "💡 En un Macroproyecto solo se pueden registrar proyectos de Alumbrado Público (AP).";
                ayudaTipo.classList.remove("hidden");
            }
        }
    }

    if (selectMacro) {
        selectMacro.addEventListener("change", function() {
            const opt = selectMacro.selectedOptions[0];
            actualizarOpcionesTipoNuevo(opt);
        });
    }

    function abrir() {
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        const contenedorCampoCointeca = document.getElementById("contenedorCampoCointeca");
        const enMacro = modal && modal.dataset.enMacro === "1";
        const esMtFijo = modal && modal.dataset.esMt === "1";

        if (enMacro) {
            if (contenedorCampoCointeca) {
                if (esMtFijo) contenedorCampoCointeca.classList.remove("hidden");
                else contenedorCampoCointeca.classList.add("hidden");
            }
        } else {
            if (selectMacro && selectMacro.value) {
                actualizarOpcionesTipoNuevo(selectMacro.selectedOptions[0]);
            } else {
                if (contenedorCampoCointeca) contenedorCampoCointeca.classList.add("hidden");
            }
        }
        if (primerCampo) primerCampo.focus();
    }

    function cerrar() {
        modal.classList.remove("flex");
        modal.classList.add("hidden");
        const inputNumeroCointeca = document.getElementById("numero_cointeca");
        if (inputNumeroCointeca) inputNumeroCointeca.value = "";
        if (btnNuevo) btnNuevo.focus();
    }

    if (btnNuevo) btnNuevo.addEventListener("click", abrir);
    if (btnCerrar) btnCerrar.addEventListener("click", cerrar);
    if (btnCancelar) btnCancelar.addEventListener("click", cerrar);

    if (modal) {
        modal.addEventListener("click", function (evento) {
            if (evento.target === modal) {
                cerrar();
            }
        });
    }

    // ==========================================
    // MODAL EDITAR PROYECTO
    // ==========================================
    const modalEditar = document.getElementById("modalEditarProyecto");
    const formEditar = document.getElementById("formEditarProyecto");
    const editNumero = document.getElementById("edit_numero_emcali");
    const editContenedorCampoCointeca = document.getElementById("editContenedorCampoCointeca");
    const editNumeroCointeca = document.getElementById("edit_numero_cointeca");
    const editTipo = document.getElementById("edit_tipo");
    const editEstado = document.getElementById("edit_estado");
    const editMacroId = document.getElementById("edit_macroproyecto_id");
    const btnCerrarEditar = document.getElementById("cerrarModalEditar");
    const btnCancelarEditar = document.getElementById("cancelarModalEditar");

    function actualizarOpcionesTipoEditar(esMt, valorSeleccionado) {
        if (!editTipo) return;
        const ayudaTipoEditar = document.getElementById("ayudaEditTipoDinamico");
        if (esMt) {
            editTipo.innerHTML = '<option value="MT" selected>Media Tensión (MT)</option>';
            editTipo.value = "MT";
            if (editContenedorCampoCointeca) editContenedorCampoCointeca.classList.remove("hidden");
            if (ayudaTipoEditar) {
                ayudaTipoEditar.className = "text-[11px] text-purple-700 font-semibold mt-1";
                ayudaTipoEditar.textContent = "⚡ En un Circuito solo se permiten maniobras de Media Tensión (MT).";
                ayudaTipoEditar.classList.remove("hidden");
            }
        } else {
            let html = '';
            OPCIONES_AP.forEach(function(op) {
                html += '<option value="' + op.valor + '">' + op.texto + '</option>';
            });
            editTipo.innerHTML = html;
            if (editContenedorCampoCointeca) {
                editContenedorCampoCointeca.classList.add("hidden");
                if (editNumeroCointeca) editNumeroCointeca.value = "";
            }
            if (valorSeleccionado && valorSeleccionado !== "MT") {
                editTipo.value = valorSeleccionado;
            } else {
                editTipo.value = "AP_BARRIO";
            }
            if (ayudaTipoEditar) {
                ayudaTipoEditar.className = "text-[11px] text-blue-700 font-semibold mt-1";
                ayudaTipoEditar.textContent = "💡 En un Macroproyecto solo se permiten proyectos de Alumbrado Público (AP).";
                ayudaTipoEditar.classList.remove("hidden");
            }
        }
    }

    function abrirEditar(btn) {
        const id = btn.dataset.id;
        const numero = btn.dataset.numero || "";
        const numeroCointeca = btn.dataset.numeroCointeca || "";
        const tipo = btn.dataset.tipo || "";
        const estado = btn.dataset.estado || "Planeación";
        const macroId = btn.dataset.macroId || "";
        const esMt = btn.dataset.esMt === "1";
        const etiqueta = btn.dataset.etiqueta || (esMt ? "Maniobra" : "Proyecto");
        const etiquetaPadre = btn.dataset.etiquetaPadre || (esMt ? "Circuito" : "Macroproyecto");

        formEditar.action = "/ingenieria/proyectos/" + id + "/editar/";
        editNumero.value = numero;
        editEstado.value = estado;
        if (editMacroId) {
            editMacroId.value = macroId;
        }

        actualizarOpcionesTipoEditar(esMt, tipo);

        if (editNumeroCointeca) {
            editNumeroCointeca.value = esMt ? numeroCointeca : "";
        }
        if (editContenedorCampoCointeca) {
            if (esMt) editContenedorCampoCointeca.classList.remove("hidden");
            else editContenedorCampoCointeca.classList.add("hidden");
        }

        const textoTitulo = document.getElementById("textoTituloModalEditar");
        if (textoTitulo) textoTitulo.textContent = "Editar " + etiqueta;
        const lblMacro = document.getElementById("lblEditMacroproyecto");
        if (lblMacro) lblMacro.textContent = etiquetaPadre;
        const lblNum = document.getElementById("lblEditNumero");
        if (lblNum) lblNum.innerHTML = "Número " + (esMt ? "Maniobra EMCALI" : "Proyecto EMCALI") + ' <span class="text-red-600">*</span>';

        modalEditar.classList.remove("hidden");
        modalEditar.classList.add("flex");
        editNumero.focus();
    }

    if (editMacroId) {
        editMacroId.addEventListener("change", function() {
            const opt = editMacroId.selectedOptions[0];
            const esMt = opt ? opt.dataset.esMt === "1" : false;
            const etiqueta = opt ? opt.dataset.etiquetaHijo || (esMt ? "Maniobra" : "Proyecto") : "Proyecto";
            const etiquetaPadre = opt ? opt.dataset.etiqueta || (esMt ? "Circuito" : "Macroproyecto") : "Macroproyecto";

            const textoTitulo = document.getElementById("textoTituloModalEditar");
            if (textoTitulo) textoTitulo.textContent = "Editar " + etiqueta;
            const lblMacro = document.getElementById("lblEditMacroproyecto");
            if (lblMacro) lblMacro.textContent = etiquetaPadre;
            const lblNum = document.getElementById("lblEditNumero");
            if (lblNum) lblNum.innerHTML = "Número o Código de " + etiqueta + ' <span class="text-red-600">*</span>';

            actualizarOpcionesTipoEditar(esMt, editTipo.value);
        });
    }

    function cerrarEditar() {
        modalEditar.classList.remove("flex");
        modalEditar.classList.add("hidden");
        if (editNumeroCointeca) editNumeroCointeca.value = "";
    }

    document.querySelectorAll(".btnEditarProyecto").forEach(function(btn) {
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
    // MODAL ELIMINAR PROYECTO
    // ==========================================
    const modalEliminar = document.getElementById("modalEliminarProyecto");
    const formEliminar = document.getElementById("formEliminarProyecto");
    const deleteNombre = document.getElementById("deleteProyectoNombre");
    const deleteTextoTipo = document.getElementById("deleteTextoTipo");
    const btnCerrarEliminar = document.getElementById("cerrarModalEliminar");
    const btnCancelarEliminar = document.getElementById("cancelarModalEliminar");

    function abrirEliminar(btn) {
        const id = btn.dataset.id;
        const numero = btn.dataset.numero || "";
        const etiqueta = btn.dataset.etiqueta || "el proyecto";

        formEliminar.action = "/ingenieria/proyectos/" + id + "/eliminar/";
        deleteNombre.textContent = numero;
        if (deleteTextoTipo) deleteTextoTipo.textContent = etiqueta;

        modalEliminar.classList.remove("hidden");
        modalEliminar.classList.add("flex");
    }

    function cerrarEliminar() {
        modalEliminar.classList.remove("flex");
        modalEliminar.classList.add("hidden");
    }

    document.querySelectorAll(".btnEliminarProyecto").forEach(function(btn) {
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

    // Cerrar con Escape cualquier modal abierto
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") {
            if (modal && !modal.classList.contains("hidden")) cerrar();
            if (modalEditar && !modalEditar.classList.contains("hidden")) cerrarEditar();
            if (modalEliminar && !modalEliminar.classList.contains("hidden")) cerrarEliminar();
            if (modalImprimir && !modalImprimir.classList.contains("hidden")) cerrarModalImprimir();
        }
    });
})();
