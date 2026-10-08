/**
 * COINTECA S.A.S. - Módulo de Gerencia
 * facturacion_form.js - Importación asíncrona de datos desde proyectos de ingeniería para facturación.
 */

document.getElementById('btn-importar-ingenieria').addEventListener('click', function() {
    const proyectoSelect = document.getElementById('campo-proyecto');
    const proyectoId = proyectoSelect ? proyectoSelect.value : '';
    const btn = this;
    const apiUrl = btn.dataset.url;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span>⏳ Consultando...</span>';
    btn.disabled = true;

    fetch(`${apiUrl}?proyecto_id=${proyectoId}`)
        .then(response => response.json())
        .then(data => {
            btn.innerHTML = originalText;
            btn.disabled = false;
            if (data.total > 0) {
                document.getElementById('campo-facturacion_real').value = Math.round(data.total);
                const infoDiv = document.getElementById('info-importacion');
                const textoSpan = document.getElementById('texto-importacion');
                textoSpan.innerHTML = `✓ Se importó <strong>$${data.total_formateado} COP</strong> desde las liquidaciones de <em>${data.proyecto_referencia}</em>.`;
                infoDiv.classList.remove('hidden');
            } else {
                alert(`No se encontraron liquidaciones de mano de obra en ingeniería para este proyecto.`);
            }
        })
        .catch(err => {
            btn.innerHTML = originalText;
            btn.disabled = false;
            console.error(err);
            alert('Error al consultar las liquidaciones de ingeniería.');
        });
});
