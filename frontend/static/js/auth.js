/*
Gestion de l'authentification
*/

document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.getElementById('login-form');
  const btnLogin = document.getElementById('btn-login');
  const errorMessage = document.getElementById('error-message');

  if (loginForm) {
    loginForm.addEventListener('submit', async function (e) {
      e.preventDefault();

      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;

      // Desactiver le bouton pendant la requete
      btnLogin.disabled = true;
      btnLogin.textContent = 'Connexion...';
      errorMessage.style.display = 'none';

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
          // Sauvegarder le token
          saveSessionToken(data.data.session_token);

          // Rediriger vers le dashboard
          window.location.href = '/dashboard';
        } else {
          // Afficher l'erreur
          errorMessage.textContent = data.error || 'Identifiants invalides';
          errorMessage.style.display = 'block';

          btnLogin.disabled = false;
          btnLogin.textContent = 'Se connecter';
        }
      } catch (error) {
        errorMessage.textContent = 'Erreur de connexion au serveur';
        errorMessage.style.display = 'block';

        btnLogin.disabled = false;
        btnLogin.textContent = 'Se connecter';
      }
    });
  }
});
