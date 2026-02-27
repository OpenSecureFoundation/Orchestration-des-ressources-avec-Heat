// ============================================================================
// Types pour le workflow: Stack > Réseaux > Instances (OpenStack Heat)
// ============================================================================

/**
 * Phase A: Déploiement et Découverte
 * - Endpoint: GET /api/stacks
 */
export interface Stack {
  id: string;
  name: string;
  status: 'CREATE_COMPLETE' | 'CREATE_IN_PROGRESS' | 'DELETE_COMPLETE' | 'ERROR';
}

/**
 * Ressource d'un Stack (VM ou Réseau)
 * - Endpoint: GET /api/stacks/<stack_id>/resources
 */
export interface StackResource {
  name: string;
  type: 'OS::Nova::Server' | 'OS::Neutron::Net' | string;
  physical_id: string;
  status: 'ACTIVE' | 'RESIZE' | 'VERIFY_RESIZE' | 'ERROR' | string;
}

/**
 * Instance (VM) avec métadonnées OpenStack
 */
export interface Instance extends StackResource {
  flavor?: string; // Avant scaling: m1.tiny, Après: m1.small
  is_monitored?: boolean;
}

/**
 * Phase B: Configuration et Monitoring (Intelligence)
 * - Endpoint: POST /api/scaler/start avec { instance_id }
 * - Endpoint: GET /api/metrics/<instance_id>
 */
export interface MetricsResponse {
  current_load: number;
  history: MetricPoint[];
}

export interface MetricPoint {
  time: string;
  val: number;
}

/**
 * Phase C: Scaling et Audit (Traçabilité SSI)
 * - Endpoint: GET /api/scaler/audit
 */
export interface AuditEvent {
  timestamp: string;
  vm: string;
  action: 'SCALE_UP' | 'SCALE_DOWN' | string;
  from: string; // Ancienne flavor
  to: string;   // Nouvelle flavor
}
