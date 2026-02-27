'use client';

import { useState, useEffect } from 'react';
import { Header } from '@/components/header';
import { Sidebar } from '@/components/sidebar';
import { StackExplorer } from '@/components/stack-explorer';
import { MonitoringPanel } from '@/components/monitoring-panel';
import type { Stack, StackResource, MetricsResponse, AuditEvent } from '@/lib/types';

export default function Home() {
  const [stacks, setStacks] = useState<Stack[]>([]);
  const [selectedStackId, setSelectedStackId] = useState<string | null>(null);
  const [resources, setResources] = useState<StackResource[]>([]);
  const [selectedResourceId, setSelectedResourceId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8765/api';

  /**
   * Phase A: Récupérer les Stacks (Infrastructure globale)
   * Endpoint: GET /api/stacks
   */
  useEffect(() => {
    const fetchStacks = async () => {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/stacks`);
        if (!res.ok) throw new Error('Failed to fetch stacks');
        const data = await res.json();
        setStacks(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stacks');
      } finally {
        setLoading(false);
      }
    };

    fetchStacks();
  }, [apiUrl]);

  /**
   * Phase A: Récupérer les ressources d'un Stack (VMs + Réseaux)
   * Endpoint: GET /api/stacks/<stack_id>/resources
   */
  useEffect(() => {
    if (!selectedStackId) {
      setResources([]);
      setSelectedResourceId(null);
      return;
    }

    const fetchResources = async () => {
      try {
        const res = await fetch(`${apiUrl}/stacks/${selectedStackId}/resources`);
        if (!res.ok) throw new Error('Failed to fetch resources');
        const data = await res.json();
        setResources(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch resources');
      }
    };

    fetchResources();
  }, [selectedStackId, apiUrl]);

  /**
   * Phase B/C: Polling des métriques (toutes les 5 secondes si monitoring actif)
   * Endpoint: GET /api/metrics/<instance_id>
   */
  useEffect(() => {
    if (!isMonitoring || !selectedResourceId) {
      setMetrics(null);
      return;
    }

    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${apiUrl}/metrics/${selectedResourceId}`);
        if (!res.ok) throw new Error('Failed to fetch metrics');
        const data = await res.json();
        setMetrics(data);
      } catch (err) {
        console.error('Metrics fetch error:', err);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [isMonitoring, selectedResourceId, apiUrl]);

  /**
   * Phase B: Activer le Scaling Intelligent
   * Endpoint: POST /api/scaler/start
   */
  const handleStartMonitoring = async () => {
    if (!selectedResourceId) return;

    try {
      const res = await fetch(`${apiUrl}/scaler/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instance_id: selectedResourceId }),
      });

      if (!res.ok) throw new Error('Failed to start monitoring');
      setIsMonitoring(true);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start monitoring');
    }
  };

  /**
   * Phase C: Récupérer l'audit trail
   * Endpoint: GET /api/scaler/audit
   */
  useEffect(() => {
    if (!isMonitoring) return;

    const fetchAudit = async () => {
      try {
        const res = await fetch(`${apiUrl}/scaler/audit`);
        if (!res.ok) throw new Error('Failed to fetch audit');
        const data = await res.json();
        setAuditEvents(data);
      } catch (err) {
        console.error('Audit fetch error:', err);
      }
    };

    fetchAudit();
    const interval = setInterval(fetchAudit, 10000); // Toutes les 10 secondes
    return () => clearInterval(interval);
  }, [isMonitoring, apiUrl]);

  // Trouver la ressource sélectionnée
  const selectedResource = selectedResourceId
    ? resources.find(r => r.physical_id === selectedResourceId)
    : null;

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-hidden p-6">
          {error && (
            <div className="mb-4 bg-destructive/10 border border-destructive/50 rounded-lg p-4 text-destructive">
              {error}
            </div>
          )}

          <div className="h-full flex gap-6">
            {/* Panneau gauche: Hiérarchie Stack > Réseaux > Instances */}
            <div className="w-96 flex flex-col">
              <StackExplorer
                stacks={stacks}
                resources={resources}
                selectedStackId={selectedStackId}
                selectedResourceId={selectedResourceId}
                onSelectStack={setSelectedStackId}
                onSelectResource={setSelectedResourceId}
                loading={loading}
              />
            </div>

            {/* Panneau droit: Monitoring et Audit */}
            <div className="flex-1 flex flex-col">
              {selectedResource ? (
                <MonitoringPanel
                  resource={selectedResource}
                  metrics={metrics}
                  auditEvents={auditEvents}
                  isMonitoring={isMonitoring}
                  onStartMonitoring={handleStartMonitoring}
                />
              ) : (
                <div className="flex-1 bg-card rounded-lg border border-border flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-lg font-medium mb-2">Sélectionnez une instance</p>
                    <p className="text-sm text-muted-foreground">
                      Naviguez dans l'infrastructure pour sélectionner une VM
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
