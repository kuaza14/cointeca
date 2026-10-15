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

        if (!macroOpt ||!macroOpt.value) {
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
        const etiquetaHijo = macroOpt.dataset.etiquetaHijo || (esMt? "Maniobra": "Proyecto");
        const etiquetaPadre = macroOpt.dataset.etiqueta || (esMt? "Circuito": "Macroproyecto");

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
                ayudaTipo.textContent = " En un Circuito solo se pueden registrar maniobras de Media Tensión (MT).";
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
                ayudaTipo.textContent = " En un Macroproyecto solo se pueden registrar proyectos de Alumbrado Público (AP).";
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
                ayudaTipoEditar.textContent = " En un Circuito solo se permiten maniobras de Media Tensión (MT).";
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
            if (valorSeleccionado && valorSeleccionado!== "MT") {
                editTipo.value = valorSeleccionado;
            } else {
                editTipo.value = "AP_BARRIO";
            }
            if (ayudaTipoEditar) {
                ayudaTipoEditar.className = "text-[11px] text-blue-700 font-semibold mt-1";
                ayudaTipoEditar.textContent = " En un Macroproyecto solo se permiten proyectos de Alumbrado Público (AP).";
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
        const etiqueta = btn.dataset.etiqueta || (esMt? "Maniobra": "Proyecto");
        const etiquetaPadre = btn.dataset.etiquetaPadre || (esMt? "Circuito": "Macroproyecto");

        formEditar.action = "/ingenieria/proyectos/" + id + "/editar/";
        editNumero.value = numero;
        editEstado.value = estado;
        if (editMacroId) {
            editMacroId.value = macroId;
        }

        actualizarOpcionesTipoEditar(esMt, tipo);

        if (editNumeroCointeca) {
            editNumeroCointeca.value = esMt? numeroCointeca: "";
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
        if (lblNum) lblNum.innerHTML = "Número " + (esMt? "Maniobra EMCALI": "Proyecto EMCALI") + ' <span class="text-red-600">*</span>';

        modalEditar.classList.remove("hidden");
        modalEditar.classList.add("flex");
        editNumero.focus();
    }

    if (editMacroId) {
        editMacroId.addEventListener("change", function() {
            const opt = editMacroId.selectedOptions[0];
            const esMt = opt? opt.dataset.esMt === "1": false;
            const etiqueta = opt? opt.dataset.etiquetaHijo || (esMt? "Maniobra": "Proyecto"): "Proyecto";
            const etiquetaPadre = opt? opt.dataset.etiqueta || (esMt? "Circuito": "Macroproyecto"): "Macroproyecto";

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
                    if (item.style.display!== "none") {
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
            if (modalSimco && !modalSimco.classList.contains("hidden")) cerrarModalSimco();
        }
    });

    // ==========================================
    // MATRIZ CONTRACTUAL SIMCO (MATERIALES Y MANO DE OBRA)
    // ==========================================
    const modalSimco = document.getElementById("modalSimcoMatriz");
    const btnAbrirModalSimco = document.getElementById("btnAbrirModalSimco");
    const btnCerrarSimcoHeader = document.getElementById("btnCerrarModalSimcoHeader");
    const btnCerrarSimcoFooter = document.getElementById("btnCerrarModalSimcoFooter");
    const simcoSelectProyecto = document.getElementById("simcoSelectProyecto");
    const btnCargarMaterialesProyecto = document.getElementById("btnCargarMaterialesProyecto");
    const simcoInputBuscador = document.getElementById("simcoInputBuscador");
    const btnLimpiarSimcoBuscador = document.getElementById("btnLimpiarSimcoBuscador");
    const simcoContenedorLista = document.getElementById("simcoContenedorLista");
    const btnSimcoMarcarVisibles = document.getElementById("btnSimcoMarcarVisibles");
    const btnSimcoDesmarcarTodos = document.getElementById("btnSimcoDesmarcarTodos");
    const btnSimcoVerSoloChuleados = document.getElementById("btnSimcoVerSoloChuleados");
    const simcoTotalMatsCount = document.getElementById("simcoTotalMatsCount");
    const simcoTotalActsCount = document.getElementById("simcoTotalActsCount");
    const simcoGranTotal = document.getElementById("simcoGranTotal");
    const btnSimcoExportarExcel = document.getElementById("btnSimcoExportarExcel");
    const simcoInfoVisibles = document.getElementById("simcoInfoVisibles");

    let catalogoSimco = {};
    try {
        const rawJson = document.getElementById("catalogo-simco-json")?.textContent || "{}";
        catalogoSimco = JSON.parse(rawJson);
    } catch (e) {
        catalogoSimco = {};
    }

    // Estado en memoria de los 81 materiales: { code: { chuleado: bool, cantidad: num, expandido: bool, actividades: { id_mo: bool } } }
    const estadoSimco = {};
    Object.keys(catalogoSimco).forEach(code => {
        const mat = catalogoSimco[code];
        const actsState = {};
        (mat.actividades || []).forEach(a => {
            actsState[a.id_mo] = true;
        });
        estadoSimco[code] = {
            chuleado: false,
            cantidad: 1,
            expandido: false,
            actividades: actsState
        };
    });

    let soloChuleadosActivo = false;

    function formatearPesos(val) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(val || 0);
    }

    function normalizarSimco(txt) {
        return (txt || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    }

    function renderizarListaSimco() {
        if (!simcoContenedorLista) return;

        const query = normalizarSimco(simcoInputBuscador?.value || "");
        const terminos = query.split(/\s+/).filter(t => t.length > 0);

        const keys = Object.keys(catalogoSimco);
        let itemsRender = [];

        keys.forEach(code => {
            const mat = catalogoSimco[code];
            const state = estadoSimco[code];

            if (soloChuleadosActivo && !state.chuleado) {
                return;
            }

            const codeNorm = normalizarSimco(code);
            const descNorm = normalizarSimco(mat.descripcion);
            const fullNorm = `${codeNorm} ${descNorm}`;

            let coincide = true;
            if (terminos.length > 0) {
                coincide = terminos.every(t => fullNorm.includes(t));
            }

            if (!coincide) return;

            let score = 4;
            if (descNorm.startsWith(query)) score = 1;
            else if (descNorm.split(/\s+/).some(w => w.startsWith(query))) score = 2;
            else if (codeNorm.startsWith(query)) score = 3;

            itemsRender.push({
                code: code,
                score: score,
                desc: descNorm,
                mat: mat,
                state: state
            });
        });

        itemsRender.sort((a, b) => {
            if (a.score !== b.score) return a.score - b.score;
            return a.desc.localeCompare(b.desc);
        });

        if (simcoInfoVisibles) {
            simcoInfoVisibles.textContent = `Mostrando ${itemsRender.length} de ${keys.length} materiales SIMCO`;
        }

        if (itemsRender.length === 0) {
            simcoContenedorLista.innerHTML = `
                <div class="p-8 text-center bg-card rounded-xl border border-dashed border-border text-muted-foreground">
                    <p class="font-bold text-sm">No se encontraron materiales que coincidan con la búsqueda.</p>
                    <p class="text-xs mt-1">Intenta con otro término o desmarca el filtro de "Solo Chuleados".</p>
                </div>
            `;
            actualizarTotalesSimco();
            return;
        }

        let html = "";
        itemsRender.forEach(item => {
            const code = item.code;
            const mat = item.mat;
            const st = item.state;
            const isChecked = st.chuleado;
            const cant = st.cantidad || 1;
            const expandido = st.expandido;

            let tarifaUnitActiva = 0;
            (mat.actividades || []).forEach(act => {
                if (st.actividades[act.id_mo] !== false) {
                    tarifaUnitActiva += act.valor_unitario;
                }
            });
            const subtotalMat = isChecked ? (cant * tarifaUnitActiva) : 0;

            html += `
                <div class="mat-card-simco bg-card rounded-xl border ${isChecked ? 'border-teal-500/80 shadow-xs ring-1 ring-teal-500/30' : 'border-border'} transition p-3 hover:border-teal-400" data-code="${code}">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                        <div class="flex items-start sm:items-center gap-2.5 flex-1 min-w-0">
                            <input type="checkbox"
                                   class="chk-mat-simco size-4 mt-0.5 sm:mt-0 rounded border-border-strong text-teal-600 focus:ring-teal-500 cursor-pointer"
                                   data-code="${code}"
                                   ${isChecked ? 'checked' : ''}>

                            <span class="font-mono text-xs font-black px-2 py-0.5 rounded bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-200 border border-blue-200 dark:border-blue-700 shrink-0">
                                [${code}]
                            </span>

                            <div class="flex-1 min-w-0">
                                <span class="text-xs font-bold text-foreground block truncate" title="${mat.descripcion}">
                                    ${mat.descripcion}
                                </span>
                                <div class="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5">
                                    <span class="px-1.5 py-0.2 rounded bg-muted font-bold text-foreground">${mat.unidad || 'UN'}</span>
                                    <span>•</span>
                                    <span>Tarifa base MO: <strong class="text-teal-700 dark:text-teal-400">${formatearPesos(mat.valor_unitario_suma)}</strong> / ${mat.unidad || 'UN'}</span>
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center gap-2.5 shrink-0 self-end sm:self-auto pl-7 sm:pl-0">
                            <div class="flex items-center gap-1.5">
                                <label class="text-[10px] uppercase font-bold text-muted-foreground">Cant:</label>
                                <input type="number" step="any" min="0.01"
                                       class="input-cant-simco w-20 px-2 py-1 border border-border-strong rounded-lg text-xs font-black text-center text-foreground bg-background focus:ring-2 focus:ring-teal-500 focus:outline-none"
                                       value="${cant}"
                                       data-code="${code}">
                            </div>

                            <div class="text-right min-w-[100px]">
                                <span class="text-[10px] uppercase font-bold text-muted-foreground block">Subtotal</span>
                                <span class="text-xs font-black ${isChecked ? 'text-emerald-700 dark:text-emerald-400' : 'text-muted-foreground'} font-mono">
                                    ${formatearPesos(subtotalMat)}
                                </span>
                            </div>

                            <button type="button"
                                    class="btn-toggle-acts-simco px-2 py-1 rounded bg-muted hover:bg-gray-200 dark:hover:bg-slate-700 text-[10px] font-bold text-muted-foreground hover:text-foreground border border-border transition cursor-pointer"
                                    data-code="${code}"
                                    title="Ver actividades de mano de obra vinculadas">
                                <span>${mat.actividades?.length || 0} MO</span>
                                <span>${expandido ? '▲' : '▼'}</span>
                            </button>
                        </div>
                    </div>

                    <div class="seccion-acts-simco mt-2.5 pt-2 border-t border-border/70 ${expandido ? '' : 'hidden'}" id="acts-container-${code}">
                        <div class="bg-muted/30 rounded-lg p-2.5 space-y-1.5 border border-border/50">
                            <span class="text-[10px] font-black uppercase text-teal-800 dark:text-teal-300 block tracking-wider">
                                Actividades de Mano de Obra Vinculadas (SIMCO / Contractual)
                            </span>
                            <div class="space-y-1">
                                ${(mat.actividades || []).map(act => {
                                    const actChecked = st.actividades[act.id_mo] !== false;
                                    const subAct = isChecked && actChecked ? (cant * act.valor_unitario) : 0;
                                    return `
                                        <div class="flex items-center justify-between text-xs py-1 px-2 rounded hover:bg-background/80 transition">
                                            <div class="flex items-center gap-2 flex-1 min-w-0 pr-2">
                                                <input type="checkbox"
                                                       class="chk-act-simco size-3.5 rounded text-teal-600 focus:ring-teal-500 cursor-pointer"
                                                       data-mat-code="${code}"
                                                       data-mo-code="${act.id_mo}"
                                                       ${actChecked ? 'checked' : ''}>
                                                <span class="font-mono text-[10px] font-bold text-muted-foreground shrink-0">[${act.id_mo}]</span>
                                                <span class="text-xs text-foreground truncate" title="${act.descripcion}">${act.descripcion}</span>
                                            </div>
                                            <div class="flex items-center gap-3 shrink-0 text-right">
                                                <span class="text-[10px] font-semibold text-muted-foreground">${formatearPesos(act.valor_unitario)} / ${act.unidad}</span>
                                                <span class="font-mono text-xs font-bold ${actChecked && isChecked ? 'text-foreground' : 'text-muted-foreground'} min-w-[75px]">
                                                    ${formatearPesos(subAct)}
                                                </span>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        simcoContenedorLista.innerHTML = html;
        actualizarTotalesSimco();
    }

    function actualizarTotalesSimco() {
        let matsCount = 0;
        let actsCount = 0;
        let granTotal = 0;

        Object.keys(catalogoSimco).forEach(code => {
            const st = estadoSimco[code];
            if (!st || !st.chuleado) return;

            matsCount++;
            const cant = st.cantidad || 0;
            const mat = catalogoSimco[code];

            (mat.actividades || []).forEach(act => {
                if (st.actividades[act.id_mo] !== false) {
                    actsCount++;
                    granTotal += (cant * act.valor_unitario);
                }
            });
        });

        if (simcoTotalMatsCount) simcoTotalMatsCount.textContent = matsCount;
        if (simcoTotalActsCount) simcoTotalActsCount.textContent = actsCount;
        if (simcoGranTotal) simcoGranTotal.textContent = `${formatearPesos(granTotal)} COP`;
    }

    function abrirModalSimco() {
        if (!modalSimco) return;
        modalSimco.classList.remove("hidden");
        document.body.style.overflow = "hidden";
        renderizarListaSimco();
    }

    function cerrarModalSimco() {
        if (!modalSimco) return;
        modalSimco.classList.add("hidden");
        document.body.style.overflow = "";
    }

    if (btnAbrirModalSimco) {
        btnAbrirModalSimco.addEventListener("click", function () {
            abrirModalSimco();
        });
    }

    if (btnCerrarSimcoHeader) btnCerrarSimcoHeader.addEventListener("click", cerrarModalSimco);
    if (btnCerrarSimcoFooter) btnCerrarSimcoFooter.addEventListener("click", cerrarModalSimco);

    if (modalSimco) {
        modalSimco.addEventListener("click", function (e) {
            if (e.target === modalSimco) cerrarModalSimco();
        });
    }

    document.querySelectorAll(".btnAbrirSimcoFila").forEach(btn => {
        btn.addEventListener("click", function () {
            const proyId = this.getAttribute("data-id");
            abrirModalSimco();
            if (simcoSelectProyecto && proyId) {
                simcoSelectProyecto.value = proyId;
                cargarMaterialesDelProyecto(proyId);
            }
        });
    });

    if (btnCargarMaterialesProyecto) {
        btnCargarMaterialesProyecto.addEventListener("click", function () {
            const proyId = simcoSelectProyecto ? simcoSelectProyecto.value : "";
            if (!proyId) {
                alert("Por favor selecciona un proyecto de la lista para cargar sus materiales.");
                return;
            }
            cargarMaterialesDelProyecto(proyId);
        });
    }

    if (simcoSelectProyecto) {
        simcoSelectProyecto.addEventListener("change", function () {
            if (this.value) {
                cargarMaterialesDelProyecto(this.value);
            }
        });
    }

    function cargarMaterialesDelProyecto(proyectoId) {
        if (!proyectoId) return;

        const simcoTextoCargar = document.getElementById("simcoTextoCargar");
        if (simcoTextoCargar) simcoTextoCargar.textContent = "Cargando...";

        fetch(`/ingenieria/api/proyecto/${proyectoId}/materiales-simco/`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    return;
                }

                Object.keys(estadoSimco).forEach(k => {
                    estadoSimco[k].chuleado = false;
                });

                let cargados = 0;
                (data.materiales || []).forEach(m => {
                    const code = String(m.item);
                    if (estadoSimco[code]) {
                        estadoSimco[code].chuleado = true;
                        estadoSimco[code].cantidad = m.cantidad > 0 ? m.cantidad : 1;
                        estadoSimco[code].expandido = true;
                        cargados++;
                    }
                });

                if (cargados > 0) {
                    soloChuleadosActivo = true;
                    if (btnSimcoVerSoloChuleados) {
                        btnSimcoVerSoloChuleados.classList.add("bg-teal-600", "text-white");
                        btnSimcoVerSoloChuleados.classList.remove("bg-card", "text-foreground");
                        btnSimcoVerSoloChuleados.setAttribute("data-activo", "1");
                    }
                } else {
                    alert("Este proyecto aún no tiene materiales pedidos o instalados con conexiones SIMCO. Puedes chulearlos manualmente.");
                }

                renderizarListaSimco();
            })
            .catch(err => {
                console.error("Error al cargar materiales del proyecto:", err);
                alert("Ocurrió un error al consultar los materiales del proyecto.");
            })
            .finally(() => {
                if (simcoTextoCargar) simcoTextoCargar.textContent = "Cargar Materiales";
            });
    }

    if (simcoInputBuscador) {
        simcoInputBuscador.addEventListener("input", function () {
            if (btnLimpiarSimcoBuscador) {
                if (this.value.trim().length > 0) {
                    btnLimpiarSimcoBuscador.classList.remove("hidden");
                } else {
                    btnLimpiarSimcoBuscador.classList.add("hidden");
                }
            }
            renderizarListaSimco();
        });
    }

    if (btnLimpiarSimcoBuscador) {
        btnLimpiarSimcoBuscador.addEventListener("click", function () {
            if (simcoInputBuscador) {
                simcoInputBuscador.value = "";
                this.classList.add("hidden");
                renderizarListaSimco();
                simcoInputBuscador.focus();
            }
        });
    }

    if (btnSimcoMarcarVisibles) {
        btnSimcoMarcarVisibles.addEventListener("click", function () {
            document.querySelectorAll("#simcoContenedorLista .mat-card-simco").forEach(card => {
                const code = card.getAttribute("data-code");
                if (estadoSimco[code]) {
                    estadoSimco[code].chuleado = true;
                }
            });
            renderizarListaSimco();
        });
    }

    if (btnSimcoDesmarcarTodos) {
        btnSimcoDesmarcarTodos.addEventListener("click", function () {
            Object.keys(estadoSimco).forEach(k => {
                estadoSimco[k].chuleado = false;
            });
            renderizarListaSimco();
        });
    }

    if (btnSimcoVerSoloChuleados) {
        btnSimcoVerSoloChuleados.addEventListener("click", function () {
            soloChuleadosActivo = !soloChuleadosActivo;
            this.setAttribute("data-activo", soloChuleadosActivo ? "1" : "0");
            if (soloChuleadosActivo) {
                this.classList.add("bg-teal-600", "text-white");
                this.classList.remove("bg-card", "text-foreground");
            } else {
                this.classList.remove("bg-teal-600", "text-white");
                this.classList.add("bg-card", "text-foreground");
            }
            renderizarListaSimco();
        });
    }

    if (simcoContenedorLista) {
        simcoContenedorLista.addEventListener("change", function (e) {
            if (e.target.matches(".chk-mat-simco")) {
                const code = e.target.getAttribute("data-code");
                if (estadoSimco[code]) {
                    estadoSimco[code].chuleado = e.target.checked;
                    renderizarListaSimco();
                }
            }

            if (e.target.matches(".chk-act-simco")) {
                const matCode = e.target.getAttribute("data-mat-code");
                const moCode = e.target.getAttribute("data-mo-code");
                if (estadoSimco[matCode] && estadoSimco[matCode].actividades) {
                    estadoSimco[matCode].actividades[moCode] = e.target.checked;
                    renderizarListaSimco();
                }
            }
        });

        simcoContenedorLista.addEventListener("input", function (e) {
            if (e.target.matches(".input-cant-simco")) {
                const code = e.target.getAttribute("data-code");
                const val = parseFloat(e.target.value) || 0;
                if (estadoSimco[code]) {
                    estadoSimco[code].cantidad = val;
                    actualizarTotalesSimco();

                    const card = e.target.closest(".mat-card-simco");
                    if (card) {
                        const mat = catalogoSimco[code];
                        let t = 0;
                        (mat.actividades || []).forEach(a => {
                            if (estadoSimco[code].actividades[a.id_mo] !== false) t += a.valor_unitario;
                        });
                        const stSpan = card.querySelector(".text-right .font-mono");
                        if (stSpan && estadoSimco[code].chuleado) {
                            stSpan.textContent = formatearPesos(val * t);
                        }
                    }
                }
            }
        });

        simcoContenedorLista.addEventListener("click", function (e) {
            const btnToggle = e.target.closest(".btn-toggle-acts-simco");
            if (btnToggle) {
                const code = btnToggle.getAttribute("data-code");
                if (estadoSimco[code]) {
                    estadoSimco[code].expandido = !estadoSimco[code].expandido;
                    const container = document.getElementById(`acts-container-${code}`);
                    if (container) {
                        container.classList.toggle("hidden", !estadoSimco[code].expandido);
                    }
                    const arrowSpan = btnToggle.querySelector("span:last-child");
                    if (arrowSpan) {
                        arrowSpan.textContent = estadoSimco[code].expandido ? "▲" : "▼";
                    }
                }
            }
        });
    }

    if (btnSimcoExportarExcel) {
        btnSimcoExportarExcel.addEventListener("click", function () {
            const itemsExportar = [];
            Object.keys(catalogoSimco).forEach(code => {
                const st = estadoSimco[code];
                if (st && st.chuleado) {
                    const actsActivas = [];
                    Object.keys(st.actividades).forEach(moId => {
                        if (st.actividades[moId]) actsActivas.push(moId);
                    });
                    itemsExportar.push({
                        item: code,
                        cantidad: st.cantidad || 1,
                        actividades: actsActivas
                    });
                }
            });

            if (itemsExportar.length === 0) {
                alert("Por favor selecciona o chulea al menos un material para exportar a Excel.");
                return;
            }

            const inputProyId = document.getElementById("simcoExcelProyectoId");
            const inputItemsJson = document.getElementById("simcoExcelItemsJson");
            const formExportar = document.getElementById("formExportarSimcoExcel");

            if (inputProyId) inputProyId.value = simcoSelectProyecto ? simcoSelectProyecto.value : "";
            if (inputItemsJson) inputItemsJson.value = JSON.stringify(itemsExportar);
            if (formExportar) formExportar.submit();
        });
    }
})();

