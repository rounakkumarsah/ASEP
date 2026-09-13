'use client';

import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  NodeProps,
  BackgroundVariant,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { usePlaygroundStore } from '@/lib/stores/playgroundStore';
import initialGraphData from '@/lib/workflow-graph.json';
import {
  Play,
  ShieldAlert,
  ListTodo,
  Globe,
  Database,
  Code2,
  CheckCircle2,
  Flag,
  Cpu,
  Loader2,
  Check,
} from 'lucide-react';

const ICON_MAP: Record<string, React.ElementType> = {
  Play,
  ShieldAlert,
  ListTodo,
  Globe,
  Database,
  Code2,
  CheckCircle2,
  Flag,
  Cpu,
};

interface AgentNodeData extends Record<string, unknown> {
  id: string;
  label: string;
  role: string;
  description: string;
  icon: string;
  color: string;
  stepIndex: number;
}

function CustomAgentNode({ id, data }: NodeProps<Node<AgentNodeData>>) {
  const { activeNode, completedNodes } = usePlaygroundStore();
  const isActive = activeNode === id;
  const isCompleted = completedNodes.includes(id) && !isActive;

  const IconComponent = ICON_MAP[data.icon] || Cpu;

  return (
    <div
      className={`relative rounded-xl border p-4 transition-all duration-300 w-64 select-none ${
        isActive
          ? 'bg-[#131E2E] border-[#22D3EE] shadow-[0_0_30px_rgba(34,211,238,0.4)] ring-2 ring-[#22D3EE]/50 scale-105 z-20'
          : isCompleted
          ? 'bg-[#0F172A]/90 border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
          : 'bg-[#111622]/80 border-border/50 opacity-75 hover:opacity-100 hover:border-border'
      }`}
    >
      {/* Handles for Flow Edges */}
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-[#22D3EE] !w-2.5 !h-2.5 !border-2 !border-background"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!bg-[#22D3EE] !w-2.5 !h-2.5 !border-2 !border-background"
      />

      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div
            className="h-7 w-7 rounded-lg flex items-center justify-center border transition-all"
            style={{
              backgroundColor: isActive ? `${data.color}25` : 'rgba(255,255,255,0.05)',
              borderColor: isActive ? data.color : 'rgba(255,255,255,0.1)',
              color: data.color,
            }}
          >
            <IconComponent className="h-4 w-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider block">
              STEP 0{data.stepIndex}
            </span>
            <h4 className="text-xs font-semibold text-foreground tracking-tight leading-none">
              {data.label}
            </h4>
          </div>
        </div>

        {/* Live Status Indicator */}
        {isActive ? (
          <span className="flex items-center gap-1 text-[10px] text-[#22D3EE] font-medium bg-[#22D3EE]/10 px-1.5 py-0.5 rounded border border-[#22D3EE]/30 animate-pulse">
            <Loader2 className="h-2.5 w-2.5 animate-spin" />
            Active
          </span>
        ) : isCompleted ? (
          <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-medium bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">
            <Check className="h-2.5 w-2.5" />
            Done
          </span>
        ) : (
          <span className="text-[10px] text-muted-foreground/60 font-mono">
            Idle
          </span>
        )}
      </div>

      {/* Role Badge */}
      <div className="mb-2">
        <span
          className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border inline-block"
          style={{
            backgroundColor: `${data.color}15`,
            borderColor: `${data.color}40`,
            color: data.color,
          }}
        >
          {data.role}
        </span>
      </div>

      {/* Description */}
      <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
        {data.description}
      </p>

      {/* Active Pulse Glow Aura */}
      {isActive && (
        <span className="absolute -inset-0.5 rounded-xl bg-gradient-to-r from-[#22D3EE] to-blue-500 opacity-20 blur-sm pointer-events-none -z-10 animate-pulse" />
      )}
    </div>
  );
}

export function WorkflowVisualizer() {
  const { activeNode, completedNodes } = usePlaygroundStore();

  const nodeTypes = useMemo(() => ({ agentNode: CustomAgentNode }), []);

  // Update edges dynamically: animate and highlight active edges
  const edges: Edge[] = useMemo(() => {
    return initialGraphData.edges.map((e) => {
      const isTraversed = completedNodes.includes(e.source);
      const isTargetActive = activeNode === e.target;
      const isLoopback = e.id.includes('loopback');

      return {
        ...e,
        animated: isTargetActive || (isTraversed && !isLoopback),
        style: {
          stroke: isLoopback
            ? '#EF4444'
            : isTargetActive
            ? '#22D3EE'
            : isTraversed
            ? '#10B981'
            : '#334155',
          strokeWidth: isTargetActive ? 3 : 2,
          strokeDasharray: isLoopback ? '5 5' : undefined,
        },
      };
    });
  }, [activeNode, completedNodes]);

  return (
    <div className="h-full w-full bg-[#0A0D14] relative overflow-hidden flex flex-col">
      {/* Visualizer Top Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/40 bg-background/40 backdrop-blur z-10">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-[#22D3EE] animate-ping" />
          <span className="text-xs font-semibold tracking-wide uppercase text-muted-foreground">
            Antigravity DAG Architecture
          </span>
          <span className="text-[10px] text-muted-foreground bg-accent/40 border border-border/50 px-1.5 py-0.5 rounded">
            8 Multi-Agent Nodes
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#22D3EE]" />
            <span className="text-[11px] text-muted-foreground">Active Node</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-[11px] text-muted-foreground">Completed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[#EF4444]" />
            <span className="text-[11px] text-muted-foreground">HITL Loopback</span>
          </div>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 h-full w-full">
        <ReactFlow
          nodes={initialGraphData.nodes as unknown as Node<AgentNodeData>[]}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.2}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
          className="bg-[#090D16]"
        >
          <Background color="#1E293B" variant={BackgroundVariant.Dots} gap={20} size={1} />
          <Controls className="!bg-[#0D1117] !border-border/60 !rounded-lg !shadow-xl" />
          <MiniMap
            nodeColor={(node) => {
              if (node.id === activeNode) return '#22D3EE';
              if (completedNodes.includes(node.id)) return '#10B981';
              return '#1E293B';
            }}
            maskColor="rgba(9, 13, 22, 0.8)"
            className="!bg-[#0D1117] !border-border/50 !rounded-lg !overflow-hidden"
          />
        </ReactFlow>
      </div>
    </div>
  );
}