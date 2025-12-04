

//====> Este de aca es para hacer funcionar el ojo de mostrar las contraseñas
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const togglePassword = document.querySelector('.toggle-password');
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        togglePassword.textContent = '👁️‍🗨️'; // Cambia el ícono a un "ojo cerrado"
    } else {
        passwordInput.type = 'password';
        togglePassword.textContent = '👁️'; // Cambia el ícono a un "ojo abierto"
    }
}



//====> Y este de aca hace funcionar el mensjae de alerta del login 
function showAlert(message) {
    document.getElementById('alertMessage').innerText = message;
    document.getElementById('customAlert').style.display = 'block';
    document.getElementById('overlay').style.display = 'block';
}

// Función para cerrar la alerta personalizada
function closeAlert() {
    document.getElementById('customAlert').style.display = 'none';
    document.getElementById('overlay').style.display = 'none';
}

// Ejemplo de cómo usar la alerta personalizada
// showAlert('Este es un mensaje de alerta personalizado.');



// Obtiene todos los mensajes de error NO asociados a campos específicos
var errorDiv = document.getElementById('error-messages');
var errorMessages = Array.from(errorDiv.getElementsByTagName('p')).map(function(p) {
    return p.innerText;
});
            
// Si hay mensajes de error (NO de campos), los muestra en la alerta personalizada
if (errorMessages.length > 0) {
    showAlert("Atención: " + errorMessages.join("\n")); // Un solo mensaje genérico
}