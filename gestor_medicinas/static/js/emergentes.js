function cerrarOverlay(id) {
    document.getElementById(id).style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    // Quitar clase que oculta el main para evitar flash
    document.querySelector('main.noshow').classList.remove('noshow');

    // Configurar botones suma
    document.querySelectorAll('.btn_sumar').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const desc = btn.dataset.desc;
            const cantidad = btn.dataset.cantidad;
            const overlay = document.getElementById('overlay_suma');
            const form = document.getElementById('form_suma');
            const texto = document.getElementById('texto_suma');
            const input_cantidad_actual = document.getElementById('cantidad_actual_suma');
            const input_suma = document.getElementById('input_suma');

            texto.textContent = `Suma para: ${desc}`;
            form.action = `/sumar_medicina/${id}`;
            input_cantidad_actual.textContent = cantidad;
            input_suma.value = '';
            overlay.style.display = 'flex';
        });
    });

    // Pertenece al modal de resta
    document.querySelectorAll('.btn_restar').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const desc = btn.dataset.desc;
            const cantidadStr = btn.dataset.cantidad;
            const cantidad = parseFloat(cantidadStr);
            const overlay = document.getElementById('overlay_resta');
            const form = document.getElementById('form_resta');
            const texto = document.getElementById('texto_resta');
            const input_cantidad_actual = document.getElementById('cantidad_actual_resta');
            const input_resta = document.getElementById('input_resta');

            texto.textContent = `Resta para: ${desc}`;
            form.action = `/restar_medicina/${id}`;
            input_cantidad_actual.textContent = cantidadStr;
            input_resta.value = '';

            if (!isNaN(cantidad)) {
                input_resta.max = cantidad;
            } else {
                input_resta.removeAttribute('max');
            }

            overlay.style.display = 'flex';
        });
    });

    // Configurar botones borrar para abrir modal confirmación
    document.querySelectorAll('.btn_borrar').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const desc = btn.dataset.desc;
            const overlay = document.getElementById('overlay_borrar');
            const form = document.getElementById('form_borrar');
            const texto = document.getElementById('texto_borrar');

            texto.textContent = `¿Estás seguro que deseas borrar la medicina "${desc}"?`;
            form.action = `/borrar_medicina/${id}`;
            overlay.style.display = 'flex';
        });
    });

    // Cerrar modales al hacer clic en editar o borrar para evitar mostrar form oculto
    document.querySelectorAll('a.btn_restar, form button.btn_restar').forEach(el => {
        el.addEventListener('click', () => {
            document.getElementById('overlay_suma').style.display = 'none';
            document.getElementById('overlay_resta').style.display = 'none';
            document.getElementById('overlay_borrar').style.display = 'none';
        });
    });
});
