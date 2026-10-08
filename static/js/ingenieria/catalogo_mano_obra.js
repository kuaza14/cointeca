/**
 * COINTECA S.A.S. - Módulo de Ingeniería
 * catalogo_mano_obra.js - Búsqueda en vivo y modales para catálogo de ítems de mano de obra.
 */

function abrirModalPrecio(id, codigo, desc, precio) {
    document.getElementById('modalDesc').innerText = desc;
    document.getElementById('modalCode').innerText = 'Código: ' + codigo;
    document.getElementById('modalPrecioInput').value = precio;
    document.getElementById('formTarifa').action = '/ingenieria/mano-obra/' + id + '/editar-tarifa/';
    document.getElementById('modalEditarTarifa').classList.remove('hidden');
}
function cerrarModalPrecio() {
    document.getElementById('modalEditarTarifa').classList.add('hidden');
}

// Filtro en vivo sin recargar
document.addEventListener("DOMContentLoaded", function() {
    const inputBuscador = document.getElementById("buscadorTarifas");
    const btnLimpiar = document.getElementById("btnLimpiarTarifas");
    const selectCat = document.getElementById("selectCategoriaTarifas");
    const contador = document.getElementById("contadorVisiblesTarifas");
    const filas = document.querySelectorAll(".fila-tarifa");

    function filtrarTarifas() {
        const q = inputBuscador ? inputBuscador.value.toLowerCase().trim() : "";
        const cat = selectCat ? selectCat.value.toLowerCase().trim() : "";

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
        filas.forEach(function(fila) {
            const texto = fila.textContent.toLowerCase();
            const filaCat = (fila.dataset.categoria || "").toLowerCase();

            const coincideTexto = (q === "" || texto.includes(q));
            const coincideCat = (cat === "" || filaCat === cat || filaCat.includes(cat));

            if (coincideTexto && coincideCat) {
                fila.style.display = "";
                visibles++;
            } else {
                fila.style.display = "none";
            }
        });

        if (contador) {
            contador.textContent = visibles;
        }
    }

    if (inputBuscador) {
        inputBuscador.addEventListener("input", filtrarTarifas);
        inputBuscador.addEventListener("keydown", function(e) {
            if (e.key === "Escape") {
                inputBuscador.value = "";
                filtrarTarifas();
            }
        });
    }

    if (selectCat) {
        selectCat.addEventListener("change", filtrarTarifas);
    }

    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", function() {
            if (inputBuscador) {
                inputBuscador.value = "";
                filtrarTarifas();
                inputBuscador.focus();
            }
        });
    }
});
