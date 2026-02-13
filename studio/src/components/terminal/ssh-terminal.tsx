'use client';

import { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import { type DatabaseConfig, WS_BASE_URL } from '@/lib/api-client';

interface SSHTerminalProps {
  config: DatabaseConfig;
  onDisconnect?: () => void;
  onConnectionChange?: (connected: boolean) => void;
}

export function SSHTerminal({ config, onDisconnect, onConnectionChange }: SSHTerminalProps) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const configRef = useRef(config);
  const isInitializedRef = useRef(false);

  // Update config ref when it changes
  useEffect(() => {
    configRef.current = config;
  }, [config]);
  // Notify parent of connection state changes
  useEffect(() => {
    onConnectionChange?.(isConnected);
  }, [isConnected, onConnectionChange]);

  useEffect(() => {
    // Only initialize once
    if (isInitializedRef.current) return;
    isInitializedRef.current = true;

    if (!terminalRef.current) return;

    // Create xterm instance
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Consolas, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#ffffff',
        selectionBackground: '#264f78',
      },
      // Don't set fixed rows/cols - let FitAddon calculate based on container size
    });

    // Load addons
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();

    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);

    // Open terminal in DOM
    term.open(terminalRef.current);

    xtermRef.current = term;
    fitAddonRef.current = fitAddon;

    // Fit after terminal is fully rendered - multiple attempts to ensure proper sizing
    const fitTerminal = () => {
      try {
        fitAddon.fit();
      } catch (e) {
        console.warn('Failed to fit terminal:', e);
      }
    };

    // Initial fit attempts
    setTimeout(fitTerminal, 50);
    setTimeout(fitTerminal, 150);
    setTimeout(fitTerminal, 300);

    // Observe container size changes
    const resizeObserver = new ResizeObserver(() => {
      fitTerminal();
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'resize',
          cols: term.cols,
          rows: term.rows,
        }));
      }
    });

    if (terminalRef.current) {
      resizeObserver.observe(terminalRef.current);
    }

    // Connect WebSocket
    const wsUrl = `${WS_BASE_URL}/api/terminal/connect`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    term.writeln('\x1b[33mConnecting to SSH server...\x1b[0m');

    ws.onopen = () => {
      // Send SSH connection configuration
      // Use SSH-specific fields if provided, otherwise fallback to database fields
      ws.send(JSON.stringify({
        host: config.ssh_host || config.host,
        port: config.ssh_port || 22,
        username: config.ssh_username || config.username || 'informix',
        password: config.ssh_password || config.password || 'in4mix',
        database: config.database,
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'connected') {
        setIsConnected(true);
        term.writeln(`\x1b[32m✓ ${message.message}\x1b[0m`);
        term.writeln('');
      } else if (message.type === 'output') {
        term.write(message.data);
      } else if (message.type === 'error') {
        term.writeln(`\x1b[31m✗ Error: ${message.message}\x1b[0m`);
      }
    };

    ws.onerror = () => {
      term.writeln('\x1b[31m✗ WebSocket connection error\x1b[0m');
      term.writeln('\x1b[33mPlease check your network connection and try again.\x1b[0m');
    };

    ws.onclose = () => {
      setIsConnected(false);
      term.writeln('');
      term.writeln('\x1b[33mConnection closed\x1b[0m');
      onDisconnect?.();
    };

    // Send terminal input to WebSocket
    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'input',
          data: data,
        }));
      }
    });

    // Cleanup only on component unmount
    return () => {
      resizeObserver.disconnect();
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'disconnect' }));
        ws.close();
      }
      term.dispose();
      isInitializedRef.current = false;
    };
  }, []); // Empty deps - only run once on mount

  return (
    <div className="h-full w-full bg-[#1e1e1e]">
      <div ref={terminalRef} className="h-full w-full p-2" />
    </div>
  );
}
