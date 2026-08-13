"use client";

import { useEffect, useRef, useCallback } from "react";
import createGlobe, { type COBEOptions } from "cobe";
import { useSpring } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlobeRenderState {
  phi: number;
  width: number;
  height: number;
  [key: string]: unknown;
}

type ExtendedCOBEOptions = Omit<COBEOptions, "width" | "height"> & {
  width: number;
  height: number;
  onRender?: (state: GlobeRenderState) => void;
};

const MARKERS: COBEOptions["markers"] = [
  { location: [37.7749, -122.4194], size: 0.09 },  // San Francisco
  { location: [40.7128, -74.006],   size: 0.07 },  // New York
  { location: [51.5074, -0.1278],   size: 0.07 },  // London
  { location: [35.6762, 139.6503],  size: 0.08 },  // Tokyo
  { location: [1.3521, 103.8198],   size: 0.07 },  // Singapore
  { location: [12.9716, 77.5946],   size: 0.07 },  // Bangalore
  { location: [-33.8688, 151.2093], size: 0.06 },  // Sydney
  { location: [-23.5505, -46.6333], size: 0.06 },  // São Paulo
  { location: [50.1109, 8.6821],    size: 0.07 },  // Frankfurt
  { location: [48.8566, 2.3522],    size: 0.06 },  // Paris
];

export function Globe({ className }: { className?: string }) {
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Drag interaction state — plain refs, no React re-renders in RAF
  const dragging       = useRef(false);
  const lastX          = useRef(0);
  const phi            = useRef(0);               // current rotation angle
  const phiVelocity    = useRef(0);               // inertia

  // Framer spring for smooth drag → only drives phiSpring.current
  const springTarget   = useRef(0);
  const phiSpring      = useSpring(0, { mass: 1, damping: 28, stiffness: 90 });

  // Sync spring value into our ref so RAF can read it
  useEffect(() => {
    return phiSpring.on("change", (v) => {
      springTarget.current = v;
    });
  }, [phiSpring]);

  const startGlobe = useCallback((size: number) => {
    if (!canvasRef.current || size < 10) return () => {};

    const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 2, 2);

    const options: ExtendedCOBEOptions = {
      devicePixelRatio: dpr,
      width:  size * dpr,
      height: size * dpr,
      phi:    phi.current,
      theta:  0.28,
      dark:   1,
      diffuse: 1.4,
      mapSamples:    20000,
      mapBrightness: 8,
      baseColor:   [0.03, 0.05, 0.09],
      markerColor: [0.13, 0.83, 0.93],   // #22D3EE
      glowColor:   [0.04, 0.28, 0.38],
      markers: MARKERS,
      onRender: (state: GlobeRenderState) => {
        if (!dragging.current) {
          // Auto-rotate + decay inertia
          phi.current += 0.0025 + phiVelocity.current;
          phiVelocity.current *= 0.92;           // friction
        } else {
          // While dragging, blend spring into phi
          phi.current = springTarget.current;
        }
        state.phi = phi.current;
        state.width  = size * dpr;
        state.height = size * dpr;
      },
    };

    const globe = createGlobe(canvasRef.current, options as unknown as COBEOptions);

    // Fade in
    requestAnimationFrame(() => {
      if (canvasRef.current) canvasRef.current.style.opacity = "1";
    });

    return () => globe.destroy();
  }, []);

  useEffect(() => {
    if (!wrapperRef.current) return;

    let cleanup: (() => void) | undefined;
    let initialized = false;

    const init = (size: number) => {
      if (initialized || size < 10 || !canvasRef.current) return;
      initialized = true;
      const dpr = Math.min(typeof window !== "undefined" ? window.devicePixelRatio : 2, 2);
      canvasRef.current.width  = size * dpr;
      canvasRef.current.height = size * dpr;
      canvasRef.current.style.width  = `${size}px`;
      canvasRef.current.style.height = `${size}px`;
      cleanup = startGlobe(size);
    };

    // Try immediately with current size
    const immediateSize = wrapperRef.current.clientWidth;
    if (immediateSize > 10) {
      init(immediateSize);
    }

    // Fallback: ResizeObserver fires whenever the element gains a real size
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        if (w > 10) {
          init(w);
          ro.disconnect();
          break;
        }
      }
    });
    ro.observe(wrapperRef.current);

    return () => {
      ro.disconnect();
      cleanup?.();
    };
  }, [startGlobe]);

  // ── Pointer handlers ────────────────────────────────────────────────────
  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    dragging.current = true;
    lastX.current    = e.clientX;
    phiSpring.set(phi.current);
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!dragging.current) return;
    const dx = e.clientX - lastX.current;
    lastX.current = e.clientX;
    phiVelocity.current = dx * 0.004;          // feed inertia
    phiSpring.set(phi.current + dx * 0.006);   // spring target
  };

  const onPointerUp = (e: React.PointerEvent<HTMLCanvasElement>) => {
    dragging.current = false;
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
  };

  return (
    <div
      ref={wrapperRef}
      className={cn("relative w-full aspect-square select-none", className)}
    >
      <canvas
        ref={canvasRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        style={{
          width:      "100%",
          height:     "100%",
          opacity:    0,
          transition: "opacity 0.8s ease",
          cursor:     "grab",
          contain:    "layout paint size",
        }}
      />
    </div>
  );
}
