/**
 * COINTECA S.A.S. - Módulo de Logística
 * materiales_requeridos.js - Gestión dinámica de requisiciones de material, adición de filas y validaciones.
 */

function abrirModalAgregar() {
        const modal = document.getElementById('modalAgregarRequerido');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }

    function cerrarModalAgregar() {
        const modal = document.getElementById('modalAgregarRequerido');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }

    document.getElementById('modalAgregarRequerido').addEventListener('click', function(event) {
        if (event.target === this) {
            cerrarModalAgregar();
        }
    });

    let itemsAgregados = [];

    function agregarMaterialALista() {
        const select = document.getElementById('selectMaterialModal');
        const inputCant = document.getElementById('inputCantidadModal');

        const materialId = select.value;
        const cantidadStr = inputCant.value.trim();

        if (!materialId) {
            alert('Por favor selecciona un material del catálogo.');
            select.focus();
            return;
        }

        const cantNum = parseFloat(cantidadStr);
        if (isNaN(cantNum) || cantNum <= 0) {
            alert('Por favor ingresa una cantidad válida mayor a 0.');
            inputCant.focus();
            return;
        }

        const selectedOption = select.options[select.selectedIndex];
        const itemCode = selectedOption.getAttribute('data-item') || '';
        const desc = selectedOption.getAttribute('data-desc') || selectedOption.textContent;
        const unidad = selectedOption.getAttribute('data-unidad') || 'U';

        // Agregar a la lista
        itemsAgregados.push({
            material_id: materialId,
            item: itemCode,
            descripcion: desc,
            unidad: unidad,
            cantidad: cantNum
        });

        // Limpiar inputs
        select.selectedIndex = 0;
        inputCant.value = '';
        select.focus();

        renderizarTablaModal();
    }

    function eliminarItemModal(index) {
        itemsAgregados.splice(index, 1);
        renderizarTablaModal();
    }

    function renderizarTablaModal() {
        const tbody = document.getElementById('cuerpoTablaModal');
        const contador = document.getElementById('contadorItemsLista');
        const btnGuardar = document.getElementById('btnGuardarModal');

        tbody.innerHTML = '';
        contador.textContent = itemsAgregados.length + (itemsAgregados.length === 1? ' material': ' materiales');

        if (itemsAgregados.length === 0) {
            tbody.innerHTML = `
                <tr id="filaVaciaModal">
                    <td colspan="5" class="px-4 py-8 text-center text-gray-400 text-xs">
                        Aún no has agregado materiales a la lista.<br>
                        <span class="text-gray-500 font-medium">Elige arriba y presiona " Agregar a la Lista".</span>
                    </td>
                </tr>
            `;
            btnGuardar.disabled = true;
            return;
        }

        btnGuardar.disabled = false;

        itemsAgregados.forEach((it, idx) => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-blue-50/50 transition';
            tr.innerHTML = `
                <td class="px-3 py-2 font-mono text-xs font-bold text-gray-600">
                    ${it.item}
                    <input type="hidden" name="material_id[]" value="${it.material_id}">
                </td>
                <td class="px-3 py-2 font-semibold text-gray-900 text-xs">
                    ${it.descripcion}
                </td>
                <td class="px-2 py-2 text-center text-xs font-bold text-gray-600">
                    <span class="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200">${it.unidad}</span>
                </td>
                <td class="px-3 py-2 text-right font-black text-blue-900 text-sm">
                    ${it.cantidad}
                    <input type="hidden" name="cantidad[]" value="${it.cantidad}">
                </td>
                <td class="px-2 py-2 text-center">
                    <button type="button" onclick="eliminarItemModal(${idx})"
                            class="text-red-500 hover:text-red-700 hover:bg-red-50 p-1 rounded transition"
                            title="Quitar de la lista">
                        
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Buscador en vivo de materiales requeridos
    document.addEventListener("DOMContentLoaded", function () {
        const inputBuscador = document.getElementById("buscadorRequeridos");
        const btnLimpiar = document.getElementById("btnLimpiarRequeridos");
        const contador = document.getElementById("contadorRequeridosVisible");
        const filas = document.querySelectorAll(".fila-requerido-tabla");

        function filtrarRequeridos() {
            const q = inputBuscador? inputBuscador.value.toLowerCase().trim(): "";

            if (btnLimpiar) {
                if (q.length > 0) {
                    btnLimpiar.classList.remove("hidden");
                    btnLimpiar.classList.add("flex");
                } else {
                    btnLimpiar.classList.add("hidden");
                    btnLimpiar.classList.remove("flex");
                }
            }

            let visibles = 0;
            filas.forEach(function (fila) {
                const texto = fila.textContent.toLowerCase();
                const match = (q === "" || texto.includes(q));
                fila.style.display = match? "": "none";
                if (match) visibles++;
            });

            if (contador) {
                contador.textContent = visibles;
            }
        }

        if (inputBuscador) {
            inputBuscador.addEventListener("input", filtrarRequeridos);
            inputBuscador.addEventListener("keydown", function (e) {
                if (e.key === "Escape") {
                    inputBuscador.value = "";
                    filtrarRequeridos();
                }
            });
        }

        if (btnLimpiar) {
            btnLimpiar.addEventListener("click", function () {
                if (inputBuscador) {
                    inputBuscador.value = "";
                    filtrarRequeridos();
                    inputBuscador.focus();
                }
            });
        }
    });
