/**
 * COINTECA S.A.S. - Módulo de Recursos Humanos
 * empleado_crear.js - Validaciones de formulario para registro de colaboradores.
 */

// Formateo en tiempo real de salario a pesos colombianos
const salarioInput = document.getElementById('salario');
if (salarioInput) {
    salarioInput.addEventListener('input', function() {
        let valor = this.value.replace(/\D/g, '');
        if (valor) {
            this.value = Number(valor).toLocaleString('es-CO');
        } else {
            this.value = '';
        }
    });
}

// Previsualización de foto seleccionada
function previsualizarFoto(input) {
    const preview = document.getElementById('previewAvatar');
    const placeholder = document.getElementById('placeholderAvatar');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
        }
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.style.display = 'none';
        placeholder.style.display = 'flex';
    }
}
