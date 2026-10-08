/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * cesantias_crear.js - Validación dinámica de motivos y montos para retiro de cesantías.
 */

const tipo = document.getElementById('tipo_retiro');

tipo.addEventListener('change', function(){

    document.getElementById('campos_vivienda').style.display = 'none';
    document.getElementById('campos_educacion').style.display = 'none';
    document.getElementById('campos_definitivo').style.display = 'none';

    if(this.value === 'VIVIENDA'){
        document.getElementById('campos_vivienda').style.display = 'block';
    }

    if(this.value === 'EDUCACION'){
        document.getElementById('campos_educacion').style.display = 'block';
    }

    if(this.value === 'DEFINITIVO'){
        document.getElementById('campos_definitivo').style.display = 'block';
    }

});
