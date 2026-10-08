/**
 * COINTECA S.A.S. - Módulo de Logística
 * editar_entrada.js - Dinámica de edición de entradas de almacén y recálculos.
 */

function eliminarMaterial(boton) {
    const fila = boton.closest(".material-row");
    if (!fila) {
        return;
    }
    fila.remove();
}


function agregarMaterial() {
    const container = document.getElementById(
        "materiales-container"
    );
    const plantilla = document.getElementById(
        "plantillaMaterialRow"
    );
    if (!container || !plantilla) {
        return;
    }

    const fila = plantilla.content.firstElementChild.cloneNode(true);
    container.appendChild(fila);
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[name="cantidad[]"]').forEach(function (input) {
        if (input.value) {
            input.value = parseFloat(input.value);
        }

    });

});
