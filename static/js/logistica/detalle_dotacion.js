/**
 * COINTECA S.A.S. - Módulo de Logística
 * detalle_dotacion.js - Gestión de entregas de dotación a personal y validaciones.
 */

function abrirModalDotacion(){

    const modal = document.getElementById("modalDotacion");

    modal.classList.remove("hidden");
    modal.classList.add("flex");

}

function cerrarModalDotacion() {

    const modal = document.getElementById("modalDotacion");

    modal.classList.remove("flex");
    modal.classList.add("hidden");

}

function editarRegistro(id, fecha, observacion){

    document.getElementById("registro_id").value = id;

    document.getElementById("accion").value = "editar";

    document.getElementsByName("fecha_entrega")[0].value = fecha;

    document.getElementsByName("observacion")[0].value = observacion;

    abrirModalDotacion();

}

function eliminarRegistro(id){

    if(!confirm("¿Desea eliminar esta entrega de dotación?")){
        return;
    }

    document.getElementById("accion").value = "eliminar";

    document.getElementById("eliminar_id").value = id;

    document.querySelector("form").submit();

}
