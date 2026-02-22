import time
import threading
from datetime import datetime
from config.settings import Config

class ScalingManager:
    """
    Module de décision intelligent.
    Fait le pont entre les métriques reçues et les actions Nova.
    Respecte la contrainte de Cooldown (Cahier de Conception).
    """

    def __init__(self, openstack_client):
        self.client = openstack_client
        self.monitored_instances = {}  # {instance_id: {'last_action': timestamp}}
        self.is_running = False
        self._lock = threading.Lock()

    def start_monitoring(self, instance_id):
        """Active la surveillance pour une instance spécifique"""
        with self._lock:
            if instance_id not in self.monitored_instances:
                self.monitored_instances[instance_id] = {'last_action': 0}
                print(f"🔍 Monitoring activé pour : {instance_id}")
            
            if not self.is_running:
                self.is_running = True
                threading.Thread(target=self._decision_loop, daemon=True).start()

    def stop_monitoring(self, instance_id):
        """Désactive la surveillance"""
        with self._lock:
            self.monitored_instances.pop(instance_id, None)

    def _decision_loop(self):
        """Boucle de décision autonome (Use Case : Surveillance Métrique)"""
        while self.is_running:
            for instance_id, data in list(self.monitored_instances.items()):
                self._evaluate_instance(instance_id, data)
            time.sleep(Config.MONITOR_INTERVAL)

    def _evaluate_instance(self, instance_id, data):
        """Logique de calcul et vérification des seuils"""
        now = time.time()
        
        # 1. Vérification du Cooldown (Anti-oscillation)
        if now - data['last_action'] < Config.SCALING_COOLDOWN:
            return # Trop tôt pour agir encore

        # 2. Récupération de la charge CPU moyenne (via Modèle)
        cpu_load = self.client.fetch_cpu_metrics(instance_id)
        if cpu_load is None: return

        # 3. Récupération de la flavor actuelle
        server = self.client.get_server_details(instance_id)
        current_flavor_name = self.client.conn.compute.get_flavor(server.flavor['id']).name

        # 4. Logique de Scaling Vertical (UP / DOWN)
        if current_flavor_name in Config.FLAVOR_SEQUENCE:
            idx = Config.FLAVOR_SEQUENCE.index(current_flavor_name)
            
            # Seuil Haut -> Scale UP
            if cpu_load > Config.CPU_HIGH_THRESHOLD:
                if idx < len(Config.FLAVOR_SEQUENCE) - 1:
                    target = Config.FLAVOR_SEQUENCE[idx + 1]
                    self._execute_scaling(instance_id, target, "UP")
            
            # Seuil Bas -> Scale DOWN
            elif cpu_load < Config.CPU_LOW_THRESHOLD:
                if idx > 0:
                    target = Config.FLAVOR_SEQUENCE[idx - 1]
                    self._execute_scaling(instance_id, target, "DOWN")

    def _execute_scaling(self, instance_id, target_flavor, direction):
        """Exécution et Audit (SSI)"""
        print(f"⚡ Action détectée : {direction} vers {target_flavor}")
        if self.client.trigger_resize(instance_id, target_flavor):
            # On attend un peu que Nova traite, puis on confirme
            time.sleep(10) 
            self.client.confirm_resize(instance_id)
            
            # Mise à jour du timestamp pour le Cooldown
            self.monitored_instances[instance_id]['last_action'] = time.time()