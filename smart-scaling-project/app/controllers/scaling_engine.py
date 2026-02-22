import threading
import time
import json
from datetime import datetime, timezone
from config.settings import SCALING_POLICY, FLAVOR_SEQUENCE, AUDIT_LOG

class ScalingEngine:
    def __init__(self, model):
        self.model = model
        self.running = False
        self.monitored_instances = {}  # {instance_id: stack_name}
        self.cooldowns = {}            # {instance_id: last_action_timestamp}
        self.lock = threading.Lock()

    def start_monitoring(self, instance_id, stack_name="manual"):
        """Ajoute une instance à la surveillance et lance le thread si besoin"""
        with self.lock:
            self.monitored_instances[instance_id] = stack_name
            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self._control_loop, daemon=True)
                self.thread.start()
        return True

    def stop_monitoring(self, instance_id=None):
        """Arrête la surveillance pour une instance ou pour tout le système"""
        with self.lock:
            if instance_id:
                self.monitored_instances.pop(instance_id, None)
            else:
                self.running = False
                self.monitored_instances = {}

    def _write_audit(self, event):
        """Enregistre les actions dans le fichier audit_scaling.log"""
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def _control_loop(self):
        """Boucle principale de décision (Basée sur ton server.py)"""
        while self.running:
            for i_id, s_name in list(self.monitored_instances.items()):
                # 1. Récupération des métriques via le Modèle
                cpu_avg, _ = self.model.get_metrics(i_id, "cpu_util", SCALING_POLICY["monitor_interval"])
                
                # 2. Vérification du Cooldown (Anti-yoyo)
                now = time.monotonic()
                if i_id in self.cooldowns and (now - self.cooldowns[i_id]) < SCALING_POLICY["cooldown_seconds"]:
                    continue

                # 3. Logique de décision pour Scaling Vertical
                # Récupérer la flavor actuelle via le modèle
                server = self.model.conn.compute.get_server(i_id)
                current_flavor = self.model.get_flavor_details(server.flavor['id']).name
                
                if current_flavor not in FLAVOR_SEQUENCE: continue
                idx = FLAVOR_SEQUENCE.index(current_flavor)

                action = None
                if cpu_avg > SCALING_POLICY["cpu_upper_threshold"] and idx < len(FLAVOR_SEQUENCE) - 1:
                    action = "UP"
                    target_flavor = FLAVOR_SEQUENCE[idx + 1]
                elif cpu_avg < SCALING_POLICY["cpu_lower_threshold"] and idx > 0:
                    action = "DOWN"
                    target_flavor = FLAVOR_SEQUENCE[idx - 1]

                # 4. Exécution du Resize (Nova)
                if action:
                    success, msg = self.model.resize_instance(i_id, target_flavor)
                    if success:
                        self.cooldowns[i_id] = now
                        self._write_audit({
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "instance_id": i_id,
                            "action": f"SCALE_{action}",
                            "old_flavor": current_flavor,
                            "new_flavor": target_flavor,
                            "trigger_value": cpu_avg
                        })
            
            time.sleep(SCALING_POLICY["monitor_interval"])