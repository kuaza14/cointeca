/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * cesantias_editar.js - Cálculo y validación en edición de solicitudes de cesantías.
 */

function actualizarCampos() {

    let tipo = document.getElementById("tipo_retiro").value;

    document.getElementById("campos_vivienda").style.display = "none";
    document.getElementById("campos_educacion").style.display = "none";
    document.getElementById("campos_definitivo").style.display = "none";

    if(tipo === "VIVIENDA") {
        document.getElementById("campos_vivienda").style.display = "block";
    }

    if(tipo === "EDUCACION") {
        document.getElementById("campos_educacion").style.display = "block";
    }

    if(tipo === "DEFINITIVO") {
        document.getElementById("campos_definitivo").style.display = "block";
    }

}

document
    .getElementById("tipo_retiro")
    .addEventListener("change", actualizarCampos);

window.onload = actualizarCampos;
