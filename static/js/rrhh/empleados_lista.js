/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * empleados_lista.js - Búsqueda en vivo de colaboradores por nombre, cédula o cargo.
 */

function abrirModalSalarios() {
    const modal = document.getElementById("modalSalarios");
    if (modal) {
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
        const input = document.getElementById("buscarEnModalSalario");
        if (input) {
            input.value = "";
            input.focus();
            document.querySelectorAll(".fila-modal-salario").forEach(f => f.style.display = "");
            const contador = document.getElementById("contadorModalSalario");
            if (contador) contador.textContent = document.querySelectorAll(".fila-modal-salario").length;
        }
    }
}

function cerrarModalSalarios() {
    const modal = document.getElementById("modalSalarios");
    if (modal) {
        modal.classList.add("hidden");
        document.body.style.overflow = "";
    }
}

document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        cerrarModalSalarios();
    }
});

document.addEventListener("DOMContentLoaded", function() {
    // Buscador tabla principal
    const buscador = document.getElementById("buscarEmpleado");
    const contador = document.getElementById("contadorResultados");
    const filas = document.querySelectorAll(".fila-empleado");

    if (buscador) {
        buscador.addEventListener("input", function() {
            let texto = this.value.toLowerCase().trim();
            let visibles = 0;

            filas.forEach(function(fila) {
                let contenido = fila.textContent.toLowerCase();
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

    // Buscador modal salarios
    const inputModal = document.getElementById("buscarEnModalSalario");
    const contadorModal = document.getElementById("contadorModalSalario");
    const filasModal = document.querySelectorAll(".fila-modal-salario");

    if (inputModal) {
        inputModal.addEventListener("input", function() {
            let texto = this.value.toLowerCase().trim();
            let visibles = 0;

            filasModal.forEach(function(fila) {
                let contenido = fila.textContent.toLowerCase();
                if (contenido.includes(texto)) {
                    fila.style.display = "";
                    visibles++;
                } else {
                    fila.style.display = "none";
                }
            });

            if (contadorModal) {
                contadorModal.textContent = visibles;
            }
        });
    }
});
