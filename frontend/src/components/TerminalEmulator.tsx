"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { Terminal } from "@xterm/xterm";
import { AttachAddon } from "@xterm/addon-attach";
import { FitAddon } from "@xterm/addon-fit";
import { WebglAddon } from "@xterm/addon-webgl";

import "@xterm/xterm/css/xterm.css";

interface TerminalEmulatorProps {
  sessionId?: string;
  wsUrl: string;
  theme?: "dark" | "light";
  onDisconnect?: () => void;
  onConnect?: () => void;
}

export const TerminalEmulator: React.FC<TerminalEmulatorProps> = ({
  wsUrl,
  theme = "dark",
  onDisconnect,
  onConnect,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  
  const [connectionStatus, setConnectionStatus] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("connecting");
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);

  // Constants for exponential backoff connection retries
  const MAX_RECONNECT_ATTEMPTS = 5;
  const BACKOFF_BASE_MS = 1000;

  // Resolve visual color tokens dynamically depending on theme configuration
  const terminalTheme = {
    background: theme === "dark" ? "#090B0F" : "#FFFFFF",
    foreground: theme === "dark" ? "#F5F7FA" : "#0F172A",
    cursor: "#22D3EE",
    black: theme === "dark" ? "#090B0F" : "#000000",
    red: "#EF4444",
    green: "#10B981",
    yellow: "#F59E0B",
    blue: "#3B82F6",
    magenta: "#EC4899",
    cyan: "#22D3EE",
    white: theme === "dark" ? "#F5F7FA" : "#0F172A",
  };

  const handleResize = useCallback(() => {
    if (!fitAddonRef.current || !websocketRef.current || !terminalRef.current) return;
    try {
      fitAddonRef.current.fit();
      const cols = terminalRef.current.cols;
      const rows = terminalRef.current.rows;
      if (websocketRef.current.readyState === WebSocket.OPEN) {
        websocketRef.current.send(
          JSON.stringify({
            type: "resize",
            cols: cols,
            rows: rows,
          })
        );
      }
    } catch (err) {
      console.error("Failed to fit/resize terminal window:", err);
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    if (!containerRef.current) return;

    setConnectionStatus("connecting");

    // 1. Initialize Xterm.js Terminal Instance if not created
    let term = terminalRef.current;
    if (!term) {
      term = new Terminal({
        cursorBlink: true,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        fontSize: 13,
        theme: terminalTheme,
      });
      terminalRef.current = term;
    } else {
      term.options.theme = terminalTheme;
    }

    // 2. Establish WebSocket socket connection
    const socket = new WebSocket(wsUrl);
    websocketRef.current = socket;

    // 3. Register Fit Addon
    let fitAddon = fitAddonRef.current;
    if (!fitAddon) {
      fitAddon = new FitAddon();
      fitAddonRef.current = fitAddon;
      term.loadAddon(fitAddon);
    }

    const attachAddon = new AttachAddon(socket);
    term.loadAddon(attachAddon);

    // 4. Open Terminal in View Container
    if (term.element === undefined) {
      term.open(containerRef.current);
    }
    fitAddon.fit();

    // 5. Try WebGL Renderer with DOM downgrade fallback
    let webglAddon: WebglAddon | null = null;
    try {
      webglAddon = new WebglAddon();
      term.loadAddon(webglAddon);
    } catch (e) {
      console.warn("WebGL terminal renderer addon unavailable, falling back to standard DOM renderer", e);
    }

    // 6. Connect Handlers
    socket.onopen = () => {
      setConnectionStatus("connected");
      setReconnectAttempt(0);
      onConnect?.();
      
      // Initial geometry resize
      const dims = (fitAddon as unknown as { proportionalDimensions: { cols: number; rows: number } | undefined })?.proportionalDimensions;
      if (dims && dims.cols && dims.rows && socket.readyState === WebSocket.OPEN) {
        socket.send(
          JSON.stringify({
            type: "resize",
            cols: dims.cols,
            rows: dims.rows,
          })
        );
      }
    };

    socket.onerror = () => {
      setConnectionStatus("error");
    };

    socket.onclose = () => {
      setConnectionStatus("disconnected");
      onDisconnect?.();

      // Trigger exponential backoff retry flow
      if (reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
        const delay = BACKOFF_BASE_MS * Math.pow(2, reconnectAttempt);
        console.log(`WebSocket disconnected. Retrying connection in ${delay}ms (Attempt ${reconnectAttempt + 1}/${MAX_RECONNECT_ATTEMPTS})`);
        
        setTimeout(() => {
          setReconnectAttempt((prev) => prev + 1);
        }, delay);
      }
    };

    // 7. Auto-Resize Geometry Handling via ResizeObserver
    let resizeFrameId: number;
    const resizeObserver = new ResizeObserver(() => {
      if (resizeFrameId) {
        cancelAnimationFrame(resizeFrameId);
      }
      resizeFrameId = requestAnimationFrame(handleResize);
    });
    resizeObserver.observe(containerRef.current);

    // 8. Backpressure Monitoring Flow Control (XON/XOFF)
    let isFlowPaused = false;
    const checkBackpressureInterval = setInterval(() => {
      if (socket.readyState !== WebSocket.OPEN) return;

      const pendingQueueLength = term.buffer.active.length;
      
      if (!isFlowPaused && pendingQueueLength > 1000) {
        isFlowPaused = true;
        socket.send(JSON.stringify({ type: "pause" }));
      } else if (isFlowPaused && pendingQueueLength < 200) {
        isFlowPaused = false;
        socket.send(JSON.stringify({ type: "resume" }));
      }
    }, 100);

    // Cleanup resources on disconnect
    return () => {
      clearInterval(checkBackpressureInterval);
      resizeObserver.disconnect();
      if (resizeFrameId) {
        cancelAnimationFrame(resizeFrameId);
      }
      if (webglAddon) {
        try {
          webglAddon.dispose();
        } catch {
          // already disposed
        }
      }
      attachAddon.dispose();
      socket.close();
    };
  }, [wsUrl, reconnectAttempt, onConnect, onDisconnect, terminalTheme, handleResize]);

  // Trigger WebSocket connection setup
  useEffect(() => {
    const cleanup = connectWebSocket();
    return () => {
      cleanup?.();
    };
  }, [connectWebSocket]);

  // Clean up the terminal instance fully on unmount
  useEffect(() => {
    return () => {
      if (terminalRef.current) {
        terminalRef.current.dispose();
        terminalRef.current = null;
      }
      if (fitAddonRef.current) {
        fitAddonRef.current.dispose();
        fitAddonRef.current = null;
      }
    };
  }, []);

  return (
    <div className={`flex flex-col h-full w-full border border-border/50 rounded-lg overflow-hidden relative min-h-[350px] ${
      theme === "dark" ? "bg-[#090B0F]" : "bg-white"
    }`}>
      {/* Status Indicators overlay */}
      <div className="absolute top-2 right-4 z-10 flex items-center gap-2">
        <span className="flex h-2 w-2 relative">
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              connectionStatus === "connected" ? "bg-emerald-400" : "bg-amber-400"
            }`}
          />
          <span
            className={`relative inline-flex rounded-full h-2 w-2 ${
              connectionStatus === "connected" ? "bg-emerald-500" : "bg-amber-500"
            }`}
          />
        </span>
        <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">
          {connectionStatus === "connecting" && reconnectAttempt > 0
            ? `retrying (${reconnectAttempt}/${MAX_RECONNECT_ATTEMPTS})`
            : connectionStatus}
        </span>
      </div>

      {/* Terminal mount target */}
      <div ref={containerRef} className="flex-1 w-full h-full p-2" />

      {/* Non-interactive disconnected overlay */}
      {connectionStatus !== "connected" && connectionStatus !== "connecting" && (
        <div className={`absolute inset-0 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center ${
          theme === "dark" ? "bg-[#090B0F]/90" : "bg-white/90"
        }`}>
          <div className="h-8 w-8 rounded-full border-2 border-primary/30 border-t-primary animate-spin mb-3" />
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
            {connectionStatus === "disconnected" && "Websocket stream disconnected"}
            {connectionStatus === "error" && "Failed to connect to terminal socket"}
          </p>
        </div>
      )}
    </div>
  );
};
