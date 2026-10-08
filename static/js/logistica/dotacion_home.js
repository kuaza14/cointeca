/**
 * COINTECA S.A.S. - Módulo de Logística
 * dotacion_home.js - Búsqueda y filtros en vivo del catálogo e inventario de dotaciones.
 */

document.addEventListener("DOMContentLoaded", function () {
    const inputBuscador = document.getElementById("buscadorDotacion");
    const btnLimpiar = document.getElementById("btnLimpiarBuscadorDotacion");
    const contador = document.getElementById("contadorEmpleadosVisible");
    const sinResultados = document.getElementById("sinResultadosDotacion");
    const filas = document.querySelectorAll(".fila-empleado-dotacion");

    function filtrarEmpleados() {
        const q = inputBuscador ? inputBuscador.value.toLowerCase().trim() : "";

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
            fila.style.display = match ? "" : "none";
            if (match) visibles++;
        });

        if (contador) {
            contador.textContent = visibles;
        }

        if (sinResultados) {
            if (visibles === 0 && filas.length > 0) {
                sinResultados.classList.remove("hidden");
            } else {
                sinResultados.classList.add("hidden");
            }
        }
    }

    if (inputBuscador) {
        inputBuscador.addEventListener("input", filtrarEmpleados);
        inputBuscador.addEventListener("keydown", function (e) {
            if (e.key === "Escape") {
                inputBuscador.value = "";
                filtrarEmpleados();
            }
        });
    }

    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", function () {
            if (inputBuscador) {
                inputBuscador.value = "";
                filtrarEmpleados();
                inputBuscador.focus();
            }
        });
    }
});
