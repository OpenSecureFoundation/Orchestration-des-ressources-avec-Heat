'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Button } from '@/components/ui/button';
import { Activity, TrendingUp, AlertCircle, Loader2, Gauge } from 'lucide-react';
import type { StackResource, MetricsResponse, AuditEvent } from '@/lib/types';

interface MonitoringPanelProps {
  resource: StackResource;
  metrics: MetricsResponse | null;
  auditEvents: AuditEvent[];
  isMonitoring: boolean;
  onStartMonitoring: () => void;
}

export function MonitoringPanel({
  resource,
  metrics,
  auditEvents,
  isMonitoring,
  onStartMonitoring,
}: MonitoringPanelProps) {
  const isVM = resource.type === 'OS::Nova::Server';
  
  // Sécurisation contre le crash .toFixed() si current_load est undefined
  const currentLoad = metrics?.current_load ?? 0;

  // Détermination de la couleur en fonction de la charge
  const getStatusColor = (load: number) => {
    if (load > 80) return 'text-red-500';
    if (load > 20) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="flex flex-col gap-4 h-full animate-in fade-in duration-500">
      {/* En-tête : Détails de l'instance */}
      <div className="bg-card rounded-xl border border-border p-5 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">{resource.name}</h2>
              <span className="text-[10px] bg-muted px-2 py-0.5 rounded uppercase font-mono">
                {resource.type.split('::').pop()}
              </span>
            </div>
            <p className="text-xs font-mono text-muted-foreground break-all">ID: {resource.physical_id}</p>
          </div>

          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
            resource.status === 'ACTIVE' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
          }`}>
            <span className={`w-2 h-2 rounded-full animate-pulse ${
              resource.status === 'ACTIVE' ? 'bg-green-500' : 'bg-yellow-500'
            }`} />
            {resource.status}
          </div>
        </div>
      </div>

      {/* Alerte si ce n'est pas une VM */}
      {!isVM && (
        <div className="flex-1 border-2 border-dashed border-muted rounded-xl flex flex-col items-center justify-center p-8 text-center bg-muted/5">
          <AlertCircle className="w-12 h-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium">Monitoring Indisponible</h3>
          <p className="text-sm text-muted-foreground max-w-xs mt-2">
            Le Smart-Scaling nécessite une instance de calcul (Nova). Les ressources de type {resource.type} ne peuvent pas être scalées individuellement.
          </p>
        </div>
      )}

      {/* Contrôle de l'Auto-Scaling */}
      {isVM && (
        <div className="bg-card rounded-xl border border-border p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-4">
            <div className={`p-2 rounded-lg ${isMonitoring ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
              {isMonitoring ? <Loader2 className="w-5 h-5 animate-spin" /> : <Activity className="w-5 h-5" />}
            </div>
            <div>
              <p className="text-sm font-semibold">Orchestration Inteligente</p>
              <p className="text-[11px] text-muted-foreground uppercase tracking-wider">
                Status: {isMonitoring ? 'Surveillance Active' : 'Prêt à activer'}
              </p>
            </div>
          </div>

          <Button
            onClick={onStartMonitoring}
            disabled={isMonitoring}
            size="sm"
            className={`${isMonitoring ? 'bg-muted text-muted-foreground' : 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'}`}
          >
            {isMonitoring ? 'Système Automatisé' : 'Activer Auto-Scaling'}
          </Button>
        </div>
      )}

      {/* Section Métriques */}
      {isMonitoring && (
        <div className="flex-1 bg-card rounded-xl border border-border p-5 flex flex-col shadow-sm min-h-[300px]">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-muted-foreground" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Performances Temps Réel</h3>
            </div>
            <div className={`text-3xl font-black ${getStatusColor(currentLoad)}`}>
              {currentLoad.toFixed(1)}%
            </div>
          </div>

          {/* Graphique Dynamique */}
          <div className="flex-1 w-full min-h-0">
            {metrics?.history && metrics.history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics.history}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted))" />
                  <XAxis 
                    dataKey="time" 
                    hide 
                  />
                  <YAxis 
                    stroke="hsl(var(--muted-foreground))" 
                    fontSize={10} 
                    tickLine={false} 
                    axisLine={false}
                    domain={[0, 100]}
                    tickFormatter={(val) => `${val}%`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }}
                    itemStyle={{ color: 'hsl(var(--primary))', fontSize: '12px' }}
                  />
                  {/* Seuils visuels */}
                  <ReferenceLine y={80} stroke="red" strokeDasharray="3 3" label={{ position: 'right', value: 'High', fill: 'red', fontSize: 10 }} />
                  <ReferenceLine y={20} stroke="green" strokeDasharray="3 3" label={{ position: 'right', value: 'Low', fill: 'green', fontSize: 10 }} />
                  
                  <Line
                    type="stepAfter"
                    dataKey="val"
                    stroke="hsl(var(--primary))"
                    strokeWidth={3}
                    dot={false}
                    animationDuration={300}
                    isAnimationActive={true}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex flex-col items-center justify-center h-full space-y-3">
                <Loader2 className="w-6 h-6 animate-spin text-primary/40" />
                <p className="text-xs text-muted-foreground italic">Collecte des métriques Gnocchi en cours...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Trail : Historique des décisions */}
      {isMonitoring && auditEvents.length > 0 && (
        <div className="bg-card rounded-xl border border-border p-4 shadow-inner bg-muted/5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-primary" />
            <h3 className="text-xs font-bold uppercase tracking-tighter">Journal d'orchestration</h3>
          </div>

          <div className="space-y-2">
            {auditEvents
              .filter((e) => e.vm === resource.name || e.resource_id === resource.physical_id)
              .slice(0, 3)
              .map((event, idx) => (
                <div key={idx} className="group flex items-center justify-between p-2 rounded-lg bg-background border border-border/50 hover:border-primary/50 transition-colors">
                  <div className="flex flex-col">
                    <span className={`text-[10px] font-bold ${event.action.includes('UP') ? 'text-red-400' : 'text-green-400'}`}>
                      {event.action}
                    </span>
                    <span className="text-[10px] text-muted-foreground italic">
                      {event.from} → {event.to}
                    </span>
                  </div>
                  <time className="text-[9px] font-mono text-muted-foreground">{event.timestamp}</time>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}