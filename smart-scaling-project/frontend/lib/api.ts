/**
 * API Client pour Smart Scaling Orchestrator
 * Contrat strict avec 5 endpoints uniquement
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8765/api';

export const api = {
  /**
   * Phase A: Endpoint 1
   * GET /api/stacks
   * Lister l'infrastructure globale
   */
  async fetchStacks() {
    const res = await fetch(`${API_URL}/stacks`);
    if (!res.ok) throw new Error('Failed to fetch stacks');
    return res.json();
  },

  /**
   * Phase A: Endpoint 2
   * GET /api/stacks/<stack_id>/resources
   * Détails Multi-VM d'une infrastructure (VMs + Réseaux)
   */
  async fetchStackResources(stackId: string) {
    const res = await fetch(`${API_URL}/stacks/${stackId}/resources`);
    if (!res.ok) throw new Error('Failed to fetch stack resources');
    return res.json();
  },

  /**
   * Phase B: Endpoint 3
   * POST /api/scaler/start
   * Activer le Scaling Intelligent
   */
  async startScaling(instanceId: string) {
    const res = await fetch(`${API_URL}/scaler/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instance_id: instanceId }),
    });
    if (!res.ok) throw new Error('Failed to start scaling');
    return res.json();
  },

  /**
   * Phase B/C: Endpoint 4
   * GET /api/metrics/<instance_id>
   * Flux de Métriques (Graphiques) - Polling toutes les 5 secondes
   */
  async fetchMetrics(instanceId: string) {
    const res = await fetch(`${API_URL}/metrics/${instanceId}`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },

  /**
   * Phase C: Endpoint 5
   * GET /api/scaler/audit
   * Historique d'Audit (SSI)
   */
  async fetchAuditTrail() {
    const res = await fetch(`${API_URL}/scaler/audit`);
    if (!res.ok) throw new Error('Failed to fetch audit trail');
    return res.json();
  },
};
