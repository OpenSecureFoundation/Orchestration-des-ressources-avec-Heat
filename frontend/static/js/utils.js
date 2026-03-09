/*
Fonctions utilitaires globales
*/

// Configuration API
const API_BASE = '';

// Obtenir le token de session depuis localStorage
function getSessionToken() {
  return localStorage.getItem('session_token');
}

// Sauvegarder le token de session
function saveSessionToken(token) {
  localStorage.setItem('session_token', token);
}

// Supprimer le token de session
function clearSessionToken() {
  localStorage.removeItem('session_token');
}

// Effectuer une requete API avec gestion des erreurs
async function apiRequest(url, options = {}) {
  const token = getSessionToken();

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'X-Session-Token': token || ''
    }
  };

  const finalOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  };

  try {
    const response = await fetch(API_BASE + url, finalOptions);
    const data = await response.json();

    // Si non authentifie, rediriger vers login
    if (response.status === 401) {
      clearSessionToken();
      window.location.href = '/login';
      return null;
    }

    return {
      success: response.ok,
      status: response.status,
      data: data
    };
  } catch (error) {
    console.error('Erreur API:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Methodes HTTP raccourcies
const api = {
  get: (url) => apiRequest(url, { method: 'GET' }),

  post: (url, data) => apiRequest(url, {
    method: 'POST',
    body: JSON.stringify(data)
  }),

  put: (url, data) => apiRequest(url, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),

  delete: (url) => apiRequest(url, { method: 'DELETE' })
};

// Afficher une notification temporaire
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;

  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Formater une date ISO en format lisible
function formatDate(isoDate) {
  if (!isoDate) return '-';

  const date = new Date(isoDate);
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');

  return `${day}/${month}/${year} ${hours}:${minutes}`;
}

// Formater un timestamp Unix
function formatTimestamp(timestamp) {
  return formatDate(new Date(timestamp * 1000).toISOString());
}

// Confirmer une action
function confirmAction(message) {
  return confirm(message);
}

// Deconnexion
async function logout() {
  if (!confirmAction('Voulez-vous vraiment vous deconnecter ?')) {
    return;
  }

  await api.post('/api/auth/logout', {});
  clearSessionToken();
  window.location.href = '/login';
}

// Ouvrir/fermer une modal
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Gestion des tabs
document.addEventListener('DOMContentLoaded', function () {
  const tabBtns = document.querySelectorAll('.tab-btn');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const targetTab = this.getAttribute('data-tab');

      // Desactiver tous les tabs
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      // Activer le tab cible
      this.classList.add('active');
      document.getElementById('tab-' + targetTab).classList.add('active');
    });
  });

  // Fermer les modals en cliquant en dehors
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function (e) {
      if (e.target === this) {
        this.classList.remove('active');
      }
    });
  });
});

// Animation CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
