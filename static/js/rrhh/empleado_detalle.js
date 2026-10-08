/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * empleado_detalle.js - Navegación por pestañas del expediente del colaborador y modales.
 */

function abrirModalRetirar() {
    const modal = document.getElementById("modalRetiro");
    if (modal) {
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }
}

function cerrarModalRetirar() {
    const modal = document.getElementById("modalRetiro");
    if (modal) {
        modal.classList.add("hidden");
        document.body.style.overflow = "";
    }
}

function abrirModalReintegrar() {
    const modal = document.getElementById("modalReintegrar");
    if (modal) {
        modal.classList.remove("hidden");
        document.body.style.overflow = "hidden";
    }
}

function cerrarModalReintegrar() {
    const modal = document.getElementById("modalReintegrar");
    if (modal) {
        modal.classList.add("hidden");
        document.body.style.overflow = "";
    }
}

document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        cerrarModalRetirar();
        cerrarModalReintegrar();
    }
});

document.querySelectorAll('.moneda-col').forEach(campo => {
    if (campo.value !== '') {
        let valor = campo.value.replace(/\D/g, '');
        campo.value = Number(valor).toLocaleString('es-CO');
    }
    campo.addEventListener('input', function() {
        let valor = this.value.replace(/\D/g, '');
        if (valor !== '') {
            this.value = Number(valor).toLocaleString('es-CO');
        } else {
            this.value = '';
        }
    });
});
