'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Server, Network } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { Stack, StackResource } from '@/lib/types';

interface StackExplorerProps {
  stacks: Stack[];
  resources: StackResource[];
  selectedStackId: string | null;
  selectedResourceId: string | null;
  onSelectStack: (stackId: string) => void;
  onSelectResource: (resourceId: string) => void;
  loading: boolean;
}

export function StackExplorer({
  stacks,
  resources,
  selectedStackId,
  selectedResourceId,
  onSelectStack,
  onSelectResource,
  loading,
}: StackExplorerProps) {
  const [expandedStacks, setExpandedStacks] = useState<Set<string>>(new Set());

  const toggleStackExpanded = (stackId: string) => {
    const newExpanded = new Set(expandedStacks);
    if (newExpanded.has(stackId)) {
      newExpanded.delete(stackId);
    } else {
      newExpanded.add(stackId);
    }
    setExpandedStacks(newExpanded);
  };

  const isStackExpanded = (stackId: string) => expandedStacks.has(stackId);

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Infrastructure</h2>
        <p className="text-xs text-muted-foreground mt-1">Stack {'>'} Réseaux {'>'} Instances</p>
      </div>

      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-4 text-center text-muted-foreground">Chargement...</div>
        ) : stacks.length === 0 ? (
          <div className="p-4 text-center text-muted-foreground text-sm">Aucun Stack</div>
        ) : (
          <div className="p-2">
            {stacks.map((stack) => (
              <div key={stack.id} className="mb-2">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => {
                      toggleStackExpanded(stack.id);
                      onSelectStack(stack.id);
                    }}
                    className={`p-1 hover:bg-sidebar-accent rounded transition-colors ${
                      selectedStackId === stack.id ? 'bg-sidebar-accent' : ''
                    }`}
                  >
                    {isStackExpanded(stack.id) ? (
                      <ChevronDown className="w-4 h-4 text-primary" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>

                  <Button
                    variant="ghost"
                    className={`justify-start flex-1 h-8 px-2 text-sm font-medium ${
                      selectedStackId === stack.id
                        ? 'bg-primary/20 text-primary'
                        : 'text-foreground hover:bg-sidebar-accent'
                    }`}
                    onClick={() => {
                      onSelectStack(stack.id);
                      setExpandedStacks(new Set([...expandedStacks, stack.id]));
                    }}
                  >
                    {stack.name}
                  </Button>

                  <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                    {stack.status}
                  </span>
                </div>

                {/* Ressources du Stack */}
                {isStackExpanded(stack.id) && selectedStackId === stack.id && (
                  <div className="ml-6 mt-2 space-y-1">
                    {resources.length === 0 ? (
                      <div className="text-xs text-muted-foreground py-2">Aucune ressource</div>
                    ) : (
                      resources.map((resource) => {
                        const isVM = resource.type === 'OS::Nova::Server';
                        const Icon = isVM ? Server : Network;

                        return (
                          <div key={resource.physical_id}>
                            <Button
                              variant="ghost"
                              className={`justify-start w-full h-8 px-2 text-xs font-medium ${
                                selectedResourceId === resource.physical_id
                                  ? isVM
                                    ? 'bg-primary/30 text-primary border-l-2 border-primary'
                                    : 'bg-primary/20 text-primary'
                                  : isVM
                                    ? 'text-foreground hover:bg-primary/10'
                                    : 'text-foreground/60 hover:bg-sidebar-accent'
                              }`}
                              onClick={() => onSelectResource(resource.physical_id)}
                            >
                              <Icon className={`w-3 h-3 mr-2 flex-shrink-0 ${isVM ? 'text-primary' : 'text-muted-foreground'}`} />
                              <span className="truncate">{resource.name}</span>
                              {isVM && <span className="ml-auto text-primary text-xs">VM</span>}
                              <span className="ml-2 text-xs">
                                {resource.status === 'ACTIVE' && (
                                  <span className="w-2 h-2 bg-green-500 rounded-full inline-block"></span>
                                )}
                                {resource.status === 'RESIZE' && (
                                  <span className="w-2 h-2 bg-yellow-500 rounded-full inline-block"></span>
                                )}
                                {resource.status === 'VERIFY_RESIZE' && (
                                  <span className="w-2 h-2 bg-yellow-500 rounded-full inline-block animate-pulse"></span>
                                )}
                                {resource.status === 'ERROR' && (
                                  <span className="w-2 h-2 bg-red-500 rounded-full inline-block"></span>
                                )}
                              </span>
                            </Button>
                            {isVM && selectedResourceId === resource.physical_id && (
                              <div className="text-xs text-primary mt-1 ml-4 font-medium">
                                ↓ Cliquez "Activer Auto-Scaling" à droite
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
