"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

// ── Types ────────────────────────────────────────────────────────────────────
interface Node {
  x: number;
  y: number;
  z: number;                   // 0..1 "depth"
  vx: number;
  vy: number;
  radius: number;
  label: string;
  pulse: number;               // 0..1 pulse phase
  pulseSpeed: number;
  energy: number;              // glow intensity 0..1
  energyTarget: number;
  connections: number[];
  type: "core" | "agent" | "memory" | "compute" | "edge";
}

interface Packet {
  from: number;
  to: number;
  t: number;                   // 0..1 progress along edge
  speed: number;
  color: string;
}

// ── Constants ────────────────────────────────────────────────────────────────
const AGENT_LABELS = [
  "PLANNER", "EXECUTOR", "MEMORY", "GOVERNANCE",
  "EVAL", "CONTROL", "GPU-A", "GPU-B",
  "MCP-01", "MCP-02", "MCP-03",
  "EU-EDGE", "AP-EDGE", "US-EAST", "SANDBOX",
];

const TYPE_COLORS: Record<Node["type"], string> = {
  core:    "#22D3EE",
  agent:   "#67E8F9",
  memory:  "#2DD4A3",
  compute: "#F5B942",
  edge:    "#818CF8",
};

const PACKET_COLORS = ["#22D3EE", "#2DD4A3", "#67E8F9", "#38BDF8", "#F5B942"];

// ── Utils ─────────────────────────────────────────────────────────────────────
function lerp(a: number, b: number, t: number) { return a + (b - a) * t; }
function clamp(v: number, lo: number, hi: number) { return Math.max(lo, Math.min(hi, v)); }
function rand(lo: number, hi: number) { return lo + Math.random() * (hi - lo); }

function project(
  x: number, y: number, z: number,
  cx: number, cy: number,
  fov: number
): [number, number, number] {
  const scale = fov / (fov + z * 200);
  return [(x - cx) * scale + cx, (y - cy) * scale + cy, scale];
}

// ── Component ─────────────────────────────────────────────────────────────────
export function NeuralNetworkViz({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const wrapper = wrapperRef.current;
    if (!canvas || !wrapper) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Guaranteed non-null references inside closures
    const targetCanvas: HTMLCanvasElement = canvas;
    const targetWrapper: HTMLDivElement = wrapper;
    const targetCtx: CanvasRenderingContext2D = ctx;

    // ── State ───────────────────────────────────────────────────────────────
    let W = 0, H = 0;
    let nodes: Node[] = [];
    let packets: Packet[] = [];
    let mouse = { x: -9999, y: -9999 };
    let rotY = 0;           // auto-rotation angle
    const rotX = 0.18;        // tilt
    let dragX = 0, dragY = 0;
    let isDragging = false;
    let lastDX = 0, lastDY = 0;
    let inertiaX = 0, inertiaY = 0;
    let lastMouse = { x: 0, y: 0 };
    let frame = 0;
    let rafId = 0;

    // ── Build graph ─────────────────────────────────────────────────────────
    function buildGraph(w: number, h: number) {
      const cx = w / 2, cy = h / 2;
      const R = Math.min(w, h) * 0.38;
      const types: Node["type"][] = ["core","agent","agent","agent","agent","memory","memory","compute","compute","edge","edge","agent","agent","memory","edge"];

      nodes = AGENT_LABELS.map((label, i) => {
        let px: number, py: number, pz: number;
        if (i === 0) {
          px = cx; py = cy; pz = 0.5;          // center core
        } else {
          const layer   = i < 5 ? 1 : i < 10 ? 2 : 3;
          const count   = layer === 1 ? 4 : layer === 2 ? 5 : 5;
          const base    = layer === 1 ? 1 : layer === 2 ? 5 : 10;
          const idx     = i - base;
          const angle   = (idx / count) * Math.PI * 2 + (layer === 2 ? 0.4 : 0);
          const radius  = layer === 1 ? R * 0.42 : layer === 2 ? R * 0.78 : R * 1.1;
          px = cx + Math.cos(angle) * radius;
          py = cy + Math.sin(angle) * radius;
          pz = 0.2 + Math.random() * 0.6;
        }
        return {
          x: px, y: py, z: pz,
          vx: rand(-0.12, 0.12),
          vy: rand(-0.12, 0.12),
          radius: i === 0 ? 14 : types[i] === "memory" ? 9 : types[i] === "compute" ? 10 : 7,
          label,
          pulse:      Math.random(),
          pulseSpeed: rand(0.012, 0.028),
          energy:     rand(0.4, 0.8),
          energyTarget: rand(0.4, 0.8),
          connections: [],
          type: types[i] ?? "agent",
        };
      });

      // Connect: core → all layer-1; layer-1 → layer-2 (partial); layer-2 → layer-3 (partial)
      const connect = (a: number, b: number) => {
        if (!nodes[a].connections.includes(b)) nodes[a].connections.push(b);
        if (!nodes[b].connections.includes(a)) nodes[b].connections.push(a);
      };
      for (let i = 1; i <= 4; i++) connect(0, i);
      [[1,5],[1,6],[2,6],[2,7],[3,7],[3,8],[4,8],[4,9],[1,9]].forEach(([a,b]) => connect(a,b));
      [[5,10],[5,11],[6,11],[6,12],[7,12],[7,13],[8,13],[9,14],[9,10]].forEach(([a,b]) => connect(a,b));
      connect(10,11); connect(12,13); connect(13,14);
    }

    // ── Resize ──────────────────────────────────────────────────────────────
    function resize() {
      const rect = targetWrapper.getBoundingClientRect();
      W = rect.width;
      H = rect.height;
      const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 2, 2);
      targetCanvas.width  = W * dpr;
      targetCanvas.height = H * dpr;
      targetCanvas.style.width  = `${W}px`;
      targetCanvas.style.height = `${H}px`;
      targetCtx.scale(dpr, dpr);
      buildGraph(W, H);
    }

    // ── Spawn packet ─────────────────────────────────────────────────────────
    function spawnPacket() {
      const from = Math.floor(Math.random() * nodes.length);
      const conns = nodes[from].connections;
      if (!conns.length) return;
      const to = conns[Math.floor(Math.random() * conns.length)];
      packets.push({
        from, to,
        t: 0,
        speed: rand(0.008, 0.018),
        color: PACKET_COLORS[Math.floor(Math.random() * PACKET_COLORS.length)],
      });
    }

    // ── Transform node to screen (rotated) ──────────────────────────────────
    function transform(n: Node): [number, number, number] {
      // center
      const cx = W / 2, cy = H / 2;
      const dx = n.x - cx, dy = n.y - cy;
      // rotate Y
      const cosY = Math.cos(rotY + dragX);
      const sinY = Math.sin(rotY + dragX);
      const x3 = dx * cosY - n.z * 200 * sinY;
      const z3 = dx * sinY + n.z * 200 * cosY;
      // rotate X (tilt)
      const cosX = Math.cos(rotX + dragY);
      const sinX = Math.sin(rotX + dragY);
      const y3 = dy * cosX - z3 * sinX;
      const z4 = dy * sinX + z3 * cosX;

      return project(x3 + cx, y3 + cy, z4, cx, cy, 600);
    }

    // ── Draw ─────────────────────────────────────────────────────────────────
    function draw() {
      targetCtx.clearRect(0, 0, W, H);

      // Sort nodes by Z (back-to-front)
      const sorted = nodes
        .map((n, i) => ({ n, i, proj: transform(n) }))
        .sort((a, b) => b.proj[2] - a.proj[2]);

      // ── Edges ────────────────────────────────────────────────────────────
      sorted.forEach(({ n, i, proj }) => {
        n.connections.forEach((j) => {
          if (j <= i) return;            // draw each edge once
          const [x1, y1] = proj;
          const [x2, y2] = transform(nodes[j]);
          const depth = (proj[2] + transform(nodes[j])[2]) / 2;
          const alpha = clamp(depth * 0.4, 0.04, 0.18);

          // Mouse proximity brightens edges
          const midX = (x1 + x2) / 2, midY = (y1 + y2) / 2;
          const mdist = Math.hypot(mouse.x - midX, mouse.y - midY);
          const bright = clamp(1 - mdist / 180, 0, 1);

          targetCtx.beginPath();
          targetCtx.moveTo(x1, y1);

          // slight curve for visual depth
          const cx2 = midX;
          const cy2 = midY;
          targetCtx.quadraticCurveTo(cx2, cy2, x2, y2);

          targetCtx.strokeStyle = `rgba(34,211,238,${alpha + bright * 0.22})`;
          targetCtx.lineWidth = depth * 0.9 + bright * 0.8;
          targetCtx.stroke();
        });
      });

      // ── Packets ──────────────────────────────────────────────────────────
      packets = packets.filter(p => {
        p.t += p.speed;
        if (p.t >= 1) return false;

        const [ax, ay] = transform(nodes[p.from]);
        const [bx, by] = transform(nodes[p.to]);
        const px2 = lerp(ax, bx, p.t);
        const py2 = lerp(ay, by, p.t);

        const alpha = 1 - Math.abs(p.t - 0.5) * 1.6;
        targetCtx.beginPath();
        targetCtx.arc(px2, py2, 3.5, 0, Math.PI * 2);
        targetCtx.fillStyle = p.color + Math.round(clamp(alpha, 0.15, 1) * 255).toString(16).padStart(2, "0");
        targetCtx.fill();

        // glow trail
        const grad = targetCtx.createRadialGradient(px2, py2, 0, px2, py2, 12);
        grad.addColorStop(0, p.color + "55");
        grad.addColorStop(1, p.color + "00");
        targetCtx.beginPath();
        targetCtx.arc(px2, py2, 12, 0, Math.PI * 2);
        targetCtx.fillStyle = grad;
        targetCtx.fill();

        return true;
      });

      // ── Nodes ────────────────────────────────────────────────────────────
      sorted.forEach(({ n, proj }) => {
        const [sx, sy, scale] = proj;
        const r = n.radius * scale * 1.1;
        const color = TYPE_COLORS[n.type];
        const dist  = Math.hypot(mouse.x - sx, mouse.y - sy);
        const hover = clamp(1 - dist / (80 * scale), 0, 1);

        // Pulse
        n.pulse = (n.pulse + n.pulseSpeed) % 1;
        const pv = Math.sin(n.pulse * Math.PI * 2) * 0.5 + 0.5;

        // Energy drift
        if (Math.random() < 0.02) n.energyTarget = rand(0.4, 1);
        n.energy = lerp(n.energy, n.energyTarget, 0.02);
        const glow = n.energy + hover * 0.4;

        // Outer pulse ring
        if (pv > 0.5 || hover > 0.1) {
          const rr = r + (pv + hover) * 18;
          targetCtx.beginPath();
          targetCtx.arc(sx, sy, rr, 0, Math.PI * 2);
          targetCtx.strokeStyle = color + Math.round(clamp((1 - pv) * 0.35 * glow, 0, 0.5) * 255).toString(16).padStart(2, "0");
          targetCtx.lineWidth = 1.5;
          targetCtx.stroke();
        }

        // Glow halo
        const halo = targetCtx.createRadialGradient(sx, sy, r * 0.5, sx, sy, r * 3.5);
        halo.addColorStop(0, color + Math.round(glow * 0.55 * 255).toString(16).padStart(2, "0"));
        halo.addColorStop(1, color + "00");
        targetCtx.beginPath();
        targetCtx.arc(sx, sy, r * 3.5, 0, Math.PI * 2);
        targetCtx.fillStyle = halo;
        targetCtx.fill();

        // Core circle
        const fill = targetCtx.createRadialGradient(sx - r * 0.3, sy - r * 0.3, 0, sx, sy, r);
        fill.addColorStop(0, "#ffffff");
        fill.addColorStop(0.35, color);
        fill.addColorStop(1, color + "88");
        targetCtx.beginPath();
        targetCtx.arc(sx, sy, r, 0, Math.PI * 2);
        targetCtx.fillStyle = fill;
        targetCtx.fill();

        // Inner core dot (core node only)
        if (n.type === "core") {
          targetCtx.beginPath();
          targetCtx.arc(sx, sy, r * 0.38, 0, Math.PI * 2);
          targetCtx.fillStyle = "#ffffff";
          targetCtx.fill();
        }

        // Label (only near-front nodes or hovered)
        if (scale > 0.82 || hover > 0.3) {
          const labelAlpha = clamp((scale - 0.7) * 3 + hover * 0.8, 0, 1);
          targetCtx.font = `bold ${Math.round(9 * scale)}px monospace`;
          targetCtx.textAlign = "center";
          targetCtx.fillStyle = `rgba(245,247,250,${labelAlpha})`;
          targetCtx.fillText(n.label, sx, sy + r + 13 * scale);
        }
      });

      frame++;
    }

    // ── Physics tick ─────────────────────────────────────────────────────────
    function tick() {
      if (!isDragging) {
        rotY    += 0.0018;              // auto-rotate
        dragX = lerp(dragX, 0, 0.04);  // spring back
        dragY = lerp(dragY, 0, 0.04);
        inertiaX *= 0.92;
        inertiaY *= 0.92;
        dragX += inertiaX * 0.1;
        dragY += inertiaY * 0.04;
      }

      // Drift nodes slightly (organic movement)
      nodes.forEach(n => {
        n.x += n.vx * 0.18;
        n.y += n.vy * 0.18;
        // soft repel from edges
        const mx = W / 2, my = H / 2;
        const dist = Math.hypot(n.x - mx, n.y - my);
        const maxR = Math.min(W, H) * 0.46;
        if (dist > maxR) {
          n.vx -= (n.x - mx) * 0.0012;
          n.vy -= (n.y - my) * 0.0012;
        }
        n.vx *= 0.98;
        n.vy *= 0.98;
      });

      // Spawn packets periodically
      if (frame % 28 === 0) spawnPacket();

      draw();
      rafId = requestAnimationFrame(tick);
    }

    // ── Pointer events ───────────────────────────────────────────────────────
    function onMouseMove(e: MouseEvent) {
      const rect = targetCanvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      if (isDragging) {
        const dx = e.clientX - lastMouse.x;
        const dy = e.clientY - lastMouse.y;
        lastDX = dx; lastDY = dy;
        dragX += dx * 0.007;
        dragY += dy * 0.004;
        lastMouse = { x: e.clientX, y: e.clientY };
      }
    }

    function onMouseDown(e: MouseEvent) {
      isDragging = true;
      lastMouse = { x: e.clientX, y: e.clientY };
      targetCanvas.style.cursor = "grabbing";
    }

    function onMouseUp() {
      isDragging = false;
      inertiaX = lastDX;
      inertiaY = lastDY;
      targetCanvas.style.cursor = "grab";
    }

    function onMouseLeave() {
      mouse = { x: -9999, y: -9999 };
      if (isDragging) {
        isDragging = false;
        inertiaX = lastDX;
        inertiaY = lastDY;
        targetCanvas.style.cursor = "grab";
      }
    }

    // Touch
    function onTouchStart(e: TouchEvent) {
      isDragging = true;
      lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    function onTouchMove(e: TouchEvent) {
      e.preventDefault();
      const dx = e.touches[0].clientX - lastMouse.x;
      const dy = e.touches[0].clientY - lastMouse.y;
      lastDX = dx; lastDY = dy;
      dragX += dx * 0.007;
      dragY += dy * 0.004;
      lastMouse = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    function onTouchEnd() {
      isDragging = false;
      inertiaX = lastDX;
      inertiaY = lastDY;
    }

    targetCanvas.addEventListener("mousemove",  onMouseMove);
    targetCanvas.addEventListener("mousedown",  onMouseDown);
    targetCanvas.addEventListener("mouseup",    onMouseUp);
    targetCanvas.addEventListener("mouseleave", onMouseLeave);
    targetCanvas.addEventListener("touchstart", onTouchStart, { passive: true });
    targetCanvas.addEventListener("touchmove",  onTouchMove,  { passive: false });
    targetCanvas.addEventListener("touchend",   onTouchEnd);

    const ro = new ResizeObserver(() => {
      targetCtx.resetTransform();
      resize();
    });
    ro.observe(targetWrapper);
    resize();

    rafId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
      targetCanvas.removeEventListener("mousemove",  onMouseMove);
      targetCanvas.removeEventListener("mousedown",  onMouseDown);
      targetCanvas.removeEventListener("mouseup",    onMouseUp);
      targetCanvas.removeEventListener("mouseleave", onMouseLeave);
      targetCanvas.removeEventListener("touchstart", onTouchStart);
      targetCanvas.removeEventListener("touchmove",  onTouchMove);
      targetCanvas.removeEventListener("touchend",   onTouchEnd);
    };
  }, []);

  return (
    <div
      ref={wrapperRef}
      className={cn("relative w-full h-full select-none", className)}
    >
      <canvas
        ref={canvasRef}
        style={{ cursor: "grab", display: "block" }}
      />
    </div>
  );
}
