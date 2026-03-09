/*
Gestion de la connexion WebSocket pour le temps reel
*/

let socket = null;
let currentServerId = null;

// Initialiser la connexion WebSocket
function initWebSocket() {
  if (socket && socket.connected) {
    return socket;
  }

  socket = io({
    transports: ['websocket', 'polling']
  });

  socket.on('connect', function () {
    console.log('WebSocket connecte');
  });

  socket.on('disconnect', function () {
    console.log('WebSocket deconnecte');
  });

  socket.on('connection_status', function (data) {
    console.log('Statut connexion:', data.status);
  });

  socket.on('error', function (data) {
    console.error('Erreur WebSocket:', data.message);
    showNotification(data.message, 'error');
  });

  return socket;
}

// S'abonner aux mises a jour d'un serveur
function subscribeToServer(serverId) {
  if (!socket) {
    initWebSocket();
  }

  currentServerId = serverId;

  socket.emit('subscribe_server', {
    server_id: serverId,
    session_token: getSessionToken()
  });

  console.log('Abonne au serveur:', serverId);
}

// Se desabonner d'un serveur
function unsubscribeFromServer(serverId) {
  if (!socket) return;

  socket.emit('unsubscribe_server', {
    server_id: serverId
  });

  console.log('Desabonne du serveur:', serverId);
  currentServerId = null;
}

// Ecouter les mises a jour de metriques
function onMetricsUpdate(callback) {
  if (!socket) {
    initWebSocket();
  }

  socket.on('metrics_update', callback);
}

// Ecouter les evenements de scaling
function onScalingEvent(callback) {
  if (!socket) {
    initWebSocket();
  }

  socket.on('scaling_event', callback);
}

// Ecouter les changements de statut
function onStatusChange(callback) {
  if (!socket) {
    initWebSocket();
  }

  socket.on('status_change', callback);
}
