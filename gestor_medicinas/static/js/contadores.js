document.addEventListener('DOMContentLoaded', function() {
    const contadores = document.querySelectorAll('.contador');
    
    contadores.forEach(contador => {
        const valorFinal = parseInt(contador.textContent);
        let actual = 0;
        const velocidad = 2;
        
        const timer = setInterval(() => {
            actual += 1;
            if (actual > valorFinal) {
                actual = valorFinal;
                clearInterval(timer);
            }
            contador.textContent = actual;
        }, velocidad);
    });
});
