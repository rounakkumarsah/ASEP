"use client";

import React, { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

// ── Node Types & Config ───────────────────────────────────────────────────────
interface AgentNode {
  id: string;
  name: string;
  category: "core" | "planner" | "executor" | "memory" | "governance" | "eval" | "mcp" | "edge";
  // 3D coordinates on sphere / cluster (-1 to 1)
  x3: number;
  y3: number;
  z3: number;
  // Dynamic 2D projection
  px: number;
  py: number;
  pz: number;
  scale: number;
  alpha: number;
  // Node properties
  radius: number;
  color: string;
  glowColor: string;
  pulsePhase: number;
  pulseSpeed: number;
  active: boolean;
  activityTimer: number;
  connectedTo: number[];
  statusText: string;
  metric: string;
}

interface DataPacket {
  fromIndex: number;
  toIndex: number;
  progress: number; // 0 to 1
  speed: number;
  color: string;
  size: number;
}

interface StarParticle {
  x: number;
  y: number;
  z: number;
  size: number;
  alpha: number;
  twinkleSpeed: number;
}

const AGENT_CATALOG: Array<{
  name: string;
  category: AgentNode["category"];
  status: string;
  metric: string;
  color: string;
  glow: string;
}> = [
  { name: "ASEP CORE", category: "core", status: "ONLINE", metric: "100%", color: "#22D3EE", glow: "rgba(34,211,238,0.6)" },
  { name: "PLANNER-01", category: "planner", status: "ACTIVE", metric: "4 tasks/s", color: "#38BDF8", glow: "rgba(56,189,248,0.5)" },
  { name: "PLANNER-02", category: "planner", status: "ROUTING", metric: "DAG opt", color: "#38BDF8", glow: "rgba(56,189,248,0.5)" },
  { name: "EXEC-DOCKER", category: "executor", status: "SANDBOXED", metric: "14ms", color: "#2DD4A3", glow: "rgba(45,212,163,0.5)" },
  { name: "EXEC-ISOLATE", category: "executor", status: "VERIFIED", metric: "0 leaks", color: "#2DD4A3", glow: "rgba(45,212,163,0.5)" },
  { name: "EXEC-RUNNER", category: "executor", status: "RUNNING", metric: "npm build", color: "#2DD4A3", glow: "rgba(45,212,163,0.5)" },
  { name: "MEM-VECTOR", category: "memory", status: "SYNCED", metric: "1536d", color: "#67E8F9", glow: "rgba(103,232,249,0.5)" },
  { name: "MEM-GRAPH", category: "memory", status: "CONNECTED", metric: "Neo4j 5.2", color: "#67E8F9", glow: "rgba(103,232,249,0.5)" },
  { name: "MEM-EPISODIC", category: "memory", status: "STORED", metric: "4.2k ctx", color: "#67E8F9", glow: "rgba(103,232,249,0.5)" },
  { name: "GOV-POLICY", category: "governance", status: "ENFORCED", metric: "SOC2 OK", color: "#F5B942", glow: "rgba(245,185,66,0.5)" },
  { name: "GOV-HITL", category: "governance", status: "LOCKED", metric: "Gated", color: "#F5B942", glow: "rgba(245,185,66,0.5)" },
  { name: "EVAL-GUARD", category: "eval", status: "SCORING", metric: "99.4%", color: "#A78BFA", glow: "rgba(167,139,250,0.5)" },
  { name: "EVAL-BENCH", category: "eval", status: "PASS", metric: "0 flaws", color: "#A78BFA", glow: "rgba(167,139,250,0.5)" },
  { name: "MCP-GITHUB", category: "mcp", status: "LINKED", metric: "v0.4.1", color: "#34D399", glow: "rgba(52,211,153,0.5)" },
  { name: "MCP-SLACK", category: "mcp", status: "STREAMING", metric: "Alerts", color: "#34D399", glow: "rgba(52,211,153,0.5)" },
  { name: "MCP-DOCKER", category: "mcp", status: "READY", metric: "IPC Bus", color: "#34D399", glow: "rgba(52,211,153,0.5)" },
  { name: "EDGE-US-WEST", category: "edge", status: "PRIMARY", metric: "8ms", color: "#818CF8", glow: "rgba(129,140,248,0.5)" },
  { name: "EDGE-EU-CENTRAL", category: "edge", status: "SYNCED", metric: "24ms", color: "#818CF8", glow: "rgba(129,140,248,0.5)" },
  { name: "EDGE-AP-EAST", category: "edge", status: "ROUTED", metric: "48ms", color: "#818CF8", glow: "rgba(129,140,248,0.5)" },
  { name: "GPU-CLUSTER-A", category: "core", status: "98.2% TFLOPS", metric: "H100 x8", color: "#22D3EE", glow: "rgba(34,211,238,0.6)" },
  { name: "GPU-CLUSTER-B", category: "core", status: "READY", metric: "A100 x16", color: "#22D3EE", glow: "rgba(34,211,238,0.6)" },
  { name: "TRACE-COLLECTOR", category: "executor", status: "DRAINING", metric: "1.2k/s", color: "#2DD4A3", glow: "rgba(45,212,163,0.5)" },
  { name: "SEMANTIC-CACHE", category: "memory", status: "HIT: 94%", metric: "Redis 7", color: "#67E8F9", glow: "rgba(103,232,249,0.5)" },
  { name: "TELEMETRY-BUS", category: "mcp", status: "NOMINAL", metric: "gRPC OK", color: "#34D399", glow: "rgba(52,211,153,0.5)" },
];

export function NeuralNetworkViz({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Fixed guaranteed non-null refs for closures
    const targetCanvas: HTMLCanvasElement = canvas;
    const targetContainer: HTMLDivElement = container;
    const targetCtx: CanvasRenderingContext2D = ctx;

    let width = 0;
    let height = 0;
    let animId: number;

    // Rotation & Camera state
    let rotX = 0.25;
    let rotY = 0;
    let targetRotX = 0.25;
    let autoRotSpeed = 0.0035;

    // Mouse Interaction
    let mouseX = -9999;
    let mouseY = -9999;
    let isDragging = false;
    let lastPointerX = 0;
    let lastPointerY = 0;
    let dragVelocityX = 0;
    let dragVelocityY = 0;
    let hoveredNodeIndex: number | null = null;

    // Graph Data
    let nodes: AgentNode[] = [];
    let packets: DataPacket[] = [];
    let backgroundStars: StarParticle[] = [];
    const orbitalRingAngles = [0, Math.PI / 3, (2 * Math.PI) / 3];

    // Initialize 3D Starfield
    function initStars(count = 70) {
      backgroundStars = [];
      for (let i = 0; i < count; i++) {
        backgroundStars.push({
          x: (Math.random() - 0.5) * 800,
          y: (Math.random() - 0.5) * 800,
          z: Math.random() * 600 - 300,
          size: Math.random() * 1.5 + 0.5,
          alpha: Math.random() * 0.6 + 0.2,
          twinkleSpeed: Math.random() * 0.02 + 0.005,
        });
      }
    }

    // Generate Nodes Distributed on Spherical Shells + Central Cluster
    function initNodes() {
      nodes = [];
      const total = AGENT_CATALOG.length;

      // Golden ratio spiral on sphere for even distribution
      const goldenRatio = (1 + Math.sqrt(5)) / 2;

      for (let i = 0; i < total; i++) {
        const item = AGENT_CATALOG[i];
        let x3: number, y3: number, z3: number;
        let radius = 7;

        if (i === 0) {
          // Central master node
          x3 = 0;
          y3 = 0;
          z3 = 0;
          radius = 12;
        } else if (i < 7) {
          // Inner core orbit shell (radius 0.45)
          const theta = (2 * Math.PI * i) / 6;
          const phi = Math.PI / 4;
          const r = 0.45;
          x3 = r * Math.cos(theta) * Math.sin(phi);
          y3 = r * Math.sin(theta) * Math.sin(phi);
          z3 = r * Math.cos(phi) * (i % 2 === 0 ? 1 : -1);
          radius = 8;
        } else {
          // Outer geodesic sphere shell (radius 0.85 to 0.98)
          const t = i / total;
          const inc = Math.acos(1 - 2 * t);
          const azimuth = 2 * Math.PI * goldenRatio * i;
          const r = 0.82 + (i % 3) * 0.06;

          x3 = r * Math.sin(inc) * Math.cos(azimuth);
          y3 = r * Math.sin(inc) * Math.sin(azimuth);
          z3 = r * Math.cos(inc);
          radius = item.category === "core" ? 9 : 6.5;
        }

        nodes.push({
          id: `node-${i}`,
          name: item.name,
          category: item.category,
          x3,
          y3,
          z3,
          px: 0,
          py: 0,
          pz: 0,
          scale: 1,
          alpha: 1,
          radius,
          color: item.color,
          glowColor: item.glow,
          pulsePhase: Math.random() * Math.PI * 2,
          pulseSpeed: 0.02 + Math.random() * 0.03,
          active: Math.random() > 0.3,
          activityTimer: Math.random() * 100,
          connectedTo: [],
          statusText: item.status,
          metric: item.metric,
        });
      }

      // Build Topology Connections:
      // Master core connects to inner nodes
      for (let i = 1; i < 7; i++) {
        nodes[0].connectedTo.push(i);
        nodes[i].connectedTo.push(0);
      }

      // Connect inner to outer clusters
      for (let i = 1; i < nodes.length; i++) {
        const targetCount = 2 + (i % 3);
        // Find nearest nodes in 3D
        const distances = nodes
          .map((n, idx) => {
            if (idx === i) return { idx, dist: 999 };
            const dx = n.x3 - nodes[i].x3;
            const dy = n.y3 - nodes[i].y3;
            const dz = n.z3 - nodes[i].z3;
            return { idx, dist: Math.sqrt(dx * dx + dy * dy + dz * dz) };
          })
          .sort((a, b) => a.dist - b.dist);

        for (let k = 0; k < targetCount; k++) {
          const nearest = distances[k];
          if (nearest && nearest.dist < 1.3) {
            if (!nodes[i].connectedTo.includes(nearest.idx)) {
              nodes[i].connectedTo.push(nearest.idx);
            }
            if (!nodes[nearest.idx].connectedTo.includes(i)) {
              nodes[nearest.idx].connectedTo.push(i);
            }
          }
        }
      }
    }

    // Spawn packets along active edges
    function spawnPacket() {
      if (nodes.length < 2) return;
      const fromIndex = Math.floor(Math.random() * nodes.length);
      const fromNode = nodes[fromIndex];
      if (!fromNode || fromNode.connectedTo.length === 0) return;

      const toIndex = fromNode.connectedTo[Math.floor(Math.random() * fromNode.connectedTo.length)];
      const toNode = nodes[toIndex];
      if (!toNode) return;

      packets.push({
        fromIndex,
        toIndex,
        progress: 0,
        speed: 0.012 + Math.random() * 0.018,
        color: fromNode.color,
        size: 3 + Math.random() * 2,
      });
    }

    // Resize Handler
    function handleResize() {
      const rect = targetContainer.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 2, 2);

      targetCanvas.width = width * dpr;
      targetCanvas.height = height * dpr;
      targetCanvas.style.width = `${width}px`;
      targetCanvas.style.height = `${height}px`;

      targetCtx.scale(dpr, dpr);
    }

    handleResize();
    initStars();
    initNodes();

    // ── 3D Projection Math ──────────────────────────────────────────────────
    function project3D(x: number, y: number, z: number, sphereRadius: number): [number, number, number, number] {
      // Scale by sphere radius
      const wx = x * sphereRadius;
      const wy = y * sphereRadius;
      const wz = z * sphereRadius;

      // Rotate Y (yaw)
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const x1 = wx * cosY + wz * sinY;
      const y1 = wy;
      const z1 = -wx * sinY + wz * cosY;

      // Rotate X (pitch)
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const x2 = x1;
      const y2 = y1 * cosX - z1 * sinX;
      const z2 = y1 * sinX + z1 * cosX;

      // Perspective camera
      const fov = 520;
      const distance = 420;
      const cameraZ = z2 + distance;
      const scale = cameraZ > 0 ? fov / cameraZ : 0.001;

      const screenX = width / 2 + x2 * scale;
      const screenY = height / 2 + y2 * scale;

      return [screenX, screenY, z2, scale];
    }

    // ── Animation Loop ──────────────────────────────────────────────────────
    function render(currentTime: number) {

      targetCtx.clearRect(0, 0, width, height);

      // Camera Physics
      if (!isDragging) {
        rotY += autoRotSpeed;
        rotX += (targetRotX - rotX) * 0.05;
        // Damp inertia
        dragVelocityX *= 0.92;
        dragVelocityY *= 0.92;
        rotY += dragVelocityX;
        rotX += dragVelocityY;
      }

      // Orbital Sphere Radius tailored to container
      const baseRadius = Math.min(width, height) * 0.42;

      // 1. Draw Starfield Background
      backgroundStars.forEach((star) => {
        star.alpha += Math.sin(currentTime * star.twinkleSpeed) * 0.01;
        const [sx, sy, , sScale] = project3D(star.x / 400, star.y / 400, star.z / 400, baseRadius * 1.3);
        if (sx > 0 && sx < width && sy > 0 && sy < height) {
          targetCtx.beginPath();
          targetCtx.arc(sx, sy, star.size * Math.max(sScale * 0.8, 0.4), 0, Math.PI * 2);
          targetCtx.fillStyle = `rgba(148, 163, 184, ${Math.max(0.1, Math.min(0.7, star.alpha))})`;
          targetCtx.fill();
        }
      });

      // 2. Draw Concentric 3D Orbital HUD Rings
      orbitalRingAngles.forEach((angleOffset, ringIdx) => {
        const ringRadius = baseRadius * (0.65 + ringIdx * 0.28);
        const segments = 48;
        targetCtx.beginPath();

        for (let i = 0; i <= segments; i++) {
          const theta = (i / segments) * Math.PI * 2;
          // Rotate ring plane
          const rx = Math.cos(theta) * Math.cos(angleOffset);
          const ry = Math.sin(theta);
          const rz = Math.cos(theta) * Math.sin(angleOffset);

          const [sx, sy] = project3D(rx, ry, rz, ringRadius);
          if (i === 0) targetCtx.moveTo(sx, sy);
          else targetCtx.lineTo(sx, sy);
        }

        targetCtx.strokeStyle = ringIdx === 0 ? "rgba(34, 211, 238, 0.12)" : "rgba(45, 212, 163, 0.08)";
        targetCtx.lineWidth = 1;
        targetCtx.setLineDash(ringIdx === 1 ? [4, 8] : [2, 6]);
        targetCtx.stroke();
        targetCtx.setLineDash([]);
      });

      // 3. Project all nodes & update positions
      hoveredNodeIndex = null;
      let minDistance = 24;

      nodes.forEach((node, idx) => {
        const [sx, sy, sz, scale] = project3D(node.x3, node.y3, node.z3, baseRadius);
        node.px = sx;
        node.py = sy;
        node.pz = sz;
        node.scale = scale;
        // Depth-based opacity: front is brighter, back is faded
        node.alpha = Math.max(0.25, Math.min(1, (sz + 220) / 400));
        node.pulsePhase += node.pulseSpeed;

        // Check hover proximity
        const distToMouse = Math.hypot(mouseX - sx, mouseY - sy);
        if (distToMouse < minDistance * scale) {
          hoveredNodeIndex = idx;
          minDistance = distToMouse / scale;
        }
      });

      // 4. Sort nodes by Z-depth (back-to-front rendering)
      const sortedNodeIndices = nodes
        .map((n, index) => ({ index, z: n.pz }))
        .sort((a, b) => a.z - b.z)
        .map((item) => item.index);

      // 5. Draw Neural Edges
      const drawnEdges = new Set<string>();

      nodes.forEach((node, i) => {
        node.connectedTo.forEach((j) => {
          const edgeKey = i < j ? `${i}-${j}` : `${j}-${i}`;
          if (drawnEdges.has(edgeKey)) return;
          drawnEdges.add(edgeKey);

          const targetNode = nodes[j];
          if (!targetNode) return;

          const depthAvg = (node.alpha + targetNode.alpha) / 2;
          const isHighlighted = hoveredNodeIndex === i || hoveredNodeIndex === j;

          // Quadratic curve for 3D tension feel
          targetCtx.beginPath();
          targetCtx.moveTo(node.px, node.py);
          targetCtx.lineTo(targetNode.px, targetNode.py);

          if (isHighlighted) {
            targetCtx.strokeStyle = "rgba(34, 211, 238, 0.85)";
            targetCtx.lineWidth = 2 * depthAvg;
            targetCtx.shadowColor = "#22D3EE";
            targetCtx.shadowBlur = 8;
          } else {
            // Gradient connecting line
            const strokeAlpha = Math.max(0.08, depthAvg * 0.35);
            targetCtx.strokeStyle = `rgba(34, 211, 238, ${strokeAlpha})`;
            targetCtx.lineWidth = Math.max(0.6, 1.2 * depthAvg);
            targetCtx.shadowBlur = 0;
          }
          targetCtx.stroke();
          targetCtx.shadowBlur = 0;
        });
      });

      // 6. Update & Draw Dynamic Packets
      if (Math.random() < 0.3) {
        spawnPacket();
      }

      packets = packets.filter((p) => {
        p.progress += p.speed;
        if (p.progress >= 1) return false;

        const fromNode = nodes[p.fromIndex];
        const toNode = nodes[p.toIndex];
        if (!fromNode || !toNode) return false;

        const curX = fromNode.px + (toNode.px - fromNode.px) * p.progress;
        const curY = fromNode.py + (toNode.py - fromNode.py) * p.progress;
        const curAlpha = (fromNode.alpha + toNode.alpha) / 2;

        targetCtx.beginPath();
        targetCtx.arc(curX, curY, p.size * curAlpha, 0, Math.PI * 2);
        targetCtx.fillStyle = p.color;
        targetCtx.shadowColor = p.color;
        targetCtx.shadowBlur = 10;
        targetCtx.fill();
        targetCtx.shadowBlur = 0;

        return true;
      });

      // 7. Render Nodes (Back to Front)
      sortedNodeIndices.forEach((nodeIdx) => {
        const node = nodes[nodeIdx];
        const isHovered = hoveredNodeIndex === nodeIdx;
        const isMaster = nodeIdx === 0;

        const r = node.radius * node.scale * (isHovered ? 1.4 : 1);
        const pulse = Math.sin(node.pulsePhase) * 0.3 + 0.7;

        // Outer Pulsing Glow Aura
        const auraRadius = r * (isMaster ? 3.2 : 2.4) * pulse;
        const auraGrad = targetCtx.createRadialGradient(node.px, node.py, r * 0.3, node.px, node.py, auraRadius);
        auraGrad.addColorStop(0, node.glowColor);
        auraGrad.addColorStop(1, "rgba(0,0,0,0)");

        targetCtx.beginPath();
        targetCtx.arc(node.px, node.py, auraRadius, 0, Math.PI * 2);
        targetCtx.fillStyle = auraGrad;
        targetCtx.globalAlpha = node.alpha * (isHovered ? 1 : 0.8);
        targetCtx.fill();
        targetCtx.globalAlpha = 1;

        // Outer Ring
        targetCtx.beginPath();
        targetCtx.arc(node.px, node.py, r * 1.3, 0, Math.PI * 2);
        targetCtx.strokeStyle = isHovered ? "#FFFFFF" : node.color;
        targetCtx.lineWidth = isMaster ? 2 : 1;
        targetCtx.globalAlpha = node.alpha;
        targetCtx.stroke();
        targetCtx.globalAlpha = 1;

        // Solid Inner Sphere
        targetCtx.beginPath();
        targetCtx.arc(node.px, node.py, r, 0, Math.PI * 2);
        const sphereGrad = targetCtx.createRadialGradient(
          node.px - r * 0.3,
          node.py - r * 0.3,
          r * 0.1,
          node.px,
          node.py,
          r
        );
        sphereGrad.addColorStop(0, "#FFFFFF");
        sphereGrad.addColorStop(0.4, node.color);
        sphereGrad.addColorStop(1, "#090B0F");

        targetCtx.fillStyle = sphereGrad;
        targetCtx.globalAlpha = node.alpha;
        targetCtx.fill();
        targetCtx.globalAlpha = 1;

        // Labels & HUD Cards (Rendered for foreground nodes or hovered node)
        if (node.pz > -40 || isHovered || isMaster) {
          const labelAlpha = isHovered ? 1 : Math.max(0, (node.pz + 40) / 200);

          if (labelAlpha > 0.05) {
            targetCtx.save();
            targetCtx.globalAlpha = labelAlpha;

            const textX = node.px;
            const textY = node.py - r - 8;

            // Small badge background
            targetCtx.font = `600 ${Math.max(9, Math.round(10 * node.scale))}px ui-monospace, monospace`;
            const textMetrics = targetCtx.measureText(node.name);
            const badgeW = textMetrics.width + 12;
            const badgeH = 16;

            targetCtx.fillStyle = "rgba(9, 11, 15, 0.85)";
            targetCtx.strokeStyle = isHovered ? node.color : "rgba(32, 40, 51, 0.8)";
            targetCtx.lineWidth = 1;

            targetCtx.beginPath();
            targetCtx.roundRect(textX - badgeW / 2, textY - badgeH / 2, badgeW, badgeH, 4);
            targetCtx.fill();
            targetCtx.stroke();

            // Badge Text
            targetCtx.fillStyle = isHovered ? "#22D3EE" : "#F5F7FA";
            targetCtx.textAlign = "center";
            targetCtx.textBaseline = "middle";
            targetCtx.fillText(node.name, textX, textY);

            // If hovered, render telemetry detail popover
            if (isHovered) {
              const hudX = node.px + r + 16;
              const hudY = node.py - 24;
              const hudW = 140;
              const hudH = 54;

              targetCtx.fillStyle = "rgba(13, 17, 23, 0.95)";
              targetCtx.strokeStyle = "rgba(34, 211, 238, 0.6)";
              targetCtx.lineWidth = 1;

              targetCtx.beginPath();
              targetCtx.roundRect(hudX, hudY, hudW, hudH, 6);
              targetCtx.fill();
              targetCtx.stroke();

              // Telemetry content
              targetCtx.textAlign = "left";
              targetCtx.font = "bold 10px ui-monospace, monospace";
              targetCtx.fillStyle = node.color;
              targetCtx.fillText(`STATUS: ${node.statusText}`, hudX + 10, hudY + 16);

              targetCtx.font = "9px ui-monospace, monospace";
              targetCtx.fillStyle = "#9CA6B5";
              targetCtx.fillText(`LATENCY/LOAD: ${node.metric}`, hudX + 10, hudY + 32);
              targetCtx.fillText(`PEERS: ${node.connectedTo.length} linked`, hudX + 10, hudY + 44);
            }

            targetCtx.restore();
          }
        }
      });

      // 8. Core Energy Radiator Rings
      const [coreX, coreY] = project3D(0, 0, 0, baseRadius);
      const corePulse = (currentTime * 0.001) % 1;
      const maxRing = baseRadius * 0.55;

      targetCtx.beginPath();
      targetCtx.arc(coreX, coreY, corePulse * maxRing, 0, Math.PI * 2);
      targetCtx.strokeStyle = `rgba(34, 211, 238, ${(1 - corePulse) * 0.3})`;
      targetCtx.lineWidth = 1.5;
      targetCtx.stroke();

      animId = requestAnimationFrame(render);
    }

    animId = requestAnimationFrame(render);

    // ── Mouse & Pointer Listeners ───────────────────────────────────────────
    function onPointerDown(e: MouseEvent | TouchEvent) {
      isDragging = true;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
      lastPointerX = clientX;
      lastPointerY = clientY;
      targetCanvas.style.cursor = "grabbing";
    }

    function onPointerMove(e: MouseEvent | TouchEvent) {
      const rect = targetCanvas.getBoundingClientRect();
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;

      mouseX = clientX - rect.left;
      mouseY = clientY - rect.top;

      if (isDragging) {
        const dx = clientX - lastPointerX;
        const dy = clientY - lastPointerY;
        lastPointerX = clientX;
        lastPointerY = clientY;

        dragVelocityX = dx * 0.005;
        dragVelocityY = -dy * 0.005;

        rotY += dragVelocityX;
        rotX = Math.max(-Math.PI / 3, Math.min(Math.PI / 3, rotX + dragVelocityY));
      } else {
        // Gentle parallax on hover
        const normX = (mouseX / width - 0.5) * 2;
        const normY = (mouseY / height - 0.5) * 2;
        targetRotX = 0.25 - normY * 0.2;
        autoRotSpeed = 0.0035 + normX * 0.002;
      }
    }

    function onPointerUp() {
      isDragging = false;
      targetCanvas.style.cursor = "grab";
    }

    function onMouseLeave() {
      isDragging = false;
      mouseX = -9999;
      mouseY = -9999;
      targetRotX = 0.25;
      autoRotSpeed = 0.0035;
      targetCanvas.style.cursor = "grab";
    }

    targetCanvas.style.cursor = "grab";
    targetCanvas.addEventListener("mousedown", onPointerDown);
    targetCanvas.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);
    targetCanvas.addEventListener("mouseleave", onMouseLeave);

    targetCanvas.addEventListener("touchstart", onPointerDown, { passive: true });
    targetCanvas.addEventListener("touchmove", onPointerMove, { passive: true });
    window.addEventListener("touchend", onPointerUp);

    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(targetContainer);

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
      targetCanvas.removeEventListener("mousedown", onPointerDown);
      targetCanvas.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);
      targetCanvas.removeEventListener("mouseleave", onMouseLeave);
      targetCanvas.removeEventListener("touchstart", onPointerDown);
      targetCanvas.removeEventListener("touchmove", onPointerMove);
      window.removeEventListener("touchend", onPointerUp);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative w-full h-full min-h-[420px] sm:min-h-[500px] flex items-center justify-center select-none overflow-hidden",
        className
      )}
    >
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}
