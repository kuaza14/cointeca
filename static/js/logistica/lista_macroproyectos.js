/**
 * COINTECA S.A.S. - Módulo de Logística
 * lista_macroproyectos.js - Control de acordeones y tarjetas de macroproyectos en logística.
 */

(function () {
    const inputBuscador = document.getElementById("buscadorMacroLogistica");
    const btnLimpiar = document.getElementById("btnLimpiarBuscador");
    const filas = document.querySelectorAll(".fila-macro-logistica");
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
})();
