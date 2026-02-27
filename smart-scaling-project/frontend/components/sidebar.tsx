'use client';

import { GitBranch } from 'lucide-react';

export function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-64 bg-sidebar border-r border-border p-4">
      <div className="flex items-center gap-2 px-2 mb-6">
        <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
          <GitBranch className="w-5 h-5 text-primary-foreground" />
        </div>
        <div>
          <h2 className="font-bold text-foreground">Scaling</h2>
          <p className="text-xs text-muted-foreground">Orchestrator</p>
        </div>
      </div>

      <div className="space-y-6 text-sm">
        <div className="bg-primary/10 border border-primary/30 rounded-lg p-3">
          <p className="text-xs font-semibold text-primary mb-3">WORKFLOW (Exécution Automatique)</p>
          <div className="space-y-3 text-xs leading-relaxed">
            <div className="flex gap-2">
              <span className="text-primary font-bold flex-shrink-0">1</span>
              <div>
                <p className="font-medium text-foreground">Phase A</p>
                <p className="text-muted-foreground">Sélectionnez un Stack → Déploiement & Découverte</p>
              </div>
            </div>
            <div className="flex gap-2">
              <span className="text-primary font-bold flex-shrink-0">2</span>
              <div>
                <p className="font-medium text-foreground">Phase B</p>
                <p className="text-muted-foreground">Sélectionnez une VM → Cliquez "Activer Auto-Scaling"</p>
              </div>
            </div>
            <div className="flex gap-2">
              <span className="text-primary font-bold flex-shrink-0">3</span>
              <div>
                <p className="font-medium text-foreground">Phase C</p>
                <p className="text-muted-foreground">Observez le graphique et l'audit trail</p>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-border pt-4">
          <p className="text-xs font-semibold text-muted-foreground mb-2">API ENDPOINTS</p>
          <div className="space-y-1 text-xs font-mono text-muted-foreground">
            <p>1. GET /stacks</p>
            <p>2. GET /stacks/&lt;id&gt;/resources</p>
            <p>3. POST /scaler/start</p>
            <p>4. GET /metrics/&lt;id&gt;</p>
            <p>5. GET /scaler/audit</p>
          </div>
        </div>
      </div>

      <div className="mt-auto pt-4 border-t border-border text-xs text-muted-foreground">
        <p>Master 2 SSI</p>
        <p>Smart Scaling Orchestrator</p>
      </div>
    </aside>
  );
}
