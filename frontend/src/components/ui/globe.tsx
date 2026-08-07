"use client";

import { useEffect, useRef } from "react";
import createGlobe from "cobe";

export function Globe() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let currentPhi = 0;
    if (!canvasRef.current) return;

    const resizeCanvas = () => {
      if (canvasRef.current) {
        const width = canvasRef.current.parentElement?.clientWidth || 500;
        canvasRef.current.style.width = `${width}px`;
        canvasRef.current.style.height = `${width}px`;
      }
    };

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

    const config = {
      devicePixelRatio: 2,
      width: 500 * 2,
      height: 500 * 2,
      phi: 0,
      theta: 0.3,
      dark: 1,
      diffuse: 1.2,
      mapSamples: 12000,
      mapBrightness: 6,
      baseColor: [0.03, 0.05, 0.08] as [number, number, number],
      markerColor: [0.13, 0.83, 0.93] as [number, number, number],
      glowColor: [0.05, 0.3, 0.4] as [number, number, number],
      markers: [
        { location: [37.7595, -122.4367] as [number, number], size: 0.04 },
        { location: [40.7128, -74.006] as [number, number], size: 0.04 },
        { location: [51.5074, -0.1278] as [number, number], size: 0.04 },
        { location: [35.6762, 139.6503] as [number, number], size: 0.04 },
        { location: [1.3521, 103.8198] as [number, number], size: 0.04 },
      ],
      onRender: (state: Record<string, number>) => {
        state.phi = currentPhi;
        currentPhi += 0.003;
      },
    };

    const globe = createGlobe(canvasRef.current, config as unknown as Parameters<typeof createGlobe>[1]);

    return () => {
      globe.destroy();
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  return (
    <div className="relative flex items-center justify-center w-full max-w-[500px] mx-auto aspect-square overflow-hidden">
      <canvas
        ref={canvasRef}
        className="opacity-80 hover:opacity-100 transition-opacity duration-500"
        style={{ width: 500, height: 500, maxWidth: "100%", aspectRatio: "1/1" }}
      />
    </div>
  );
}
