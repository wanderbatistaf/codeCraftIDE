"use client";

import { useState, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Terminal, Shell, Bug, X, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useExecution } from "@/contexts/execution-context";
import { useDatabase } from "@/contexts/database-context";
import { SQLQueryPanel } from "@/components/sql-query-panel";

// Dynamically import SSHTerminal to avoid SSR issues
const SSHTerminal = dynamic(
  () => import("@/components/terminal/ssh-terminal").then((mod) => ({ default: mod.SSHTerminal })),
  { ssr: false, loading: () => <div className="p-4 text-muted-foreground">Loading terminal...</div> }
);

const MIN_HEIGHT = 100;
const MAX_HEIGHT = 600;
const DEFAULT_HEIGHT = 192; // 48 * 4 = 192px (h-48)

export function BottomPanel() {
  const { currentResult, isExecuting, clearOutput } = useExecution();
  const { activeConfig } = useDatabase();
  const [isTerminalConnected, setIsTerminalConnected] = useState(false);
  const [height, setHeight] = useState(DEFAULT_HEIGHT);
  const [isResizing, setIsResizing] = useState(false);
  const startYRef = useRef<number>(0);
  const startHeightRef = useRef<number>(0);

  // Load saved height from sessionStorage (per-tab isolation)
  useEffect(() => {
    const savedHeight = sessionStorage.getItem('bottom-panel-height');
    if (savedHeight) {
      const parsedHeight = parseInt(savedHeight, 10);
      if (parsedHeight >= MIN_HEIGHT && parsedHeight <= MAX_HEIGHT) {
        setHeight(parsedHeight);
      }
    }
  }, []);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsResizing(true);
    startYRef.current = e.clientY;
    startHeightRef.current = height;
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const deltaY = startYRef.current - e.clientY;
      const newHeight = Math.min(
        Math.max(startHeightRef.current + deltaY, MIN_HEIGHT),
        MAX_HEIGHT
      );

      setHeight(newHeight);
    };

    const handleMouseUp = () => {
      if (isResizing) {
        setIsResizing(false);
        sessionStorage.setItem('bottom-panel-height', height.toString());
      }
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ns-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, height]);

  return (
    <div
      className="flex flex-shrink-0 flex-col border-t bg-[hsl(var(--background))]"
      style={{ height: `${height}px` }}
    >
      {/* Resize Handle */}
      <div
        className="h-1 cursor-ns-resize bg-border hover:bg-primary transition-colors relative group"
        onMouseDown={handleMouseDown}
      >
        <div className="absolute inset-x-0 -top-1 h-3 group-hover:bg-primary/10" />
      </div>
      <Tabs defaultValue="output" className="flex h-full flex-col">
        <TabsList className="flex-shrink-0 justify-start rounded-none border-b bg-transparent p-0">
          <TabsTrigger
            value="output"
            className="h-10 rounded-none border-b-2 border-b-transparent data-[state=active]:border-b-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            <Shell className="mr-2 h-4 w-4" />
            Console
            {currentResult && (
              <span className={`ml-2 h-2 w-2 rounded-full ${currentResult.error ? 'bg-red-500' : 'bg-green-500'}`} />
            )}
          </TabsTrigger>
          <TabsTrigger
            value="terminal"
            className="h-10 rounded-none border-b-2 border-b-transparent data-[state=active]:border-b-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            <Terminal className="mr-2 h-4 w-4" />
            Terminal
            {activeConfig && (
              <span className={`ml-2 h-2 w-2 rounded-full ${isTerminalConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            )}
          </TabsTrigger>
          <TabsTrigger
            value="debug"
            className="h-10 rounded-none border-b-2 border-b-transparent data-[state=active]:border-b-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            <Bug className="mr-2 h-4 w-4" />
            Debug
          </TabsTrigger>
          <TabsTrigger
            value="sql"
            className="h-10 rounded-none border-b-2 border-b-transparent data-[state=active]:border-b-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none"
          >
            <Database className="mr-2 h-4 w-4" />
            SQL Query
            {activeConfig && (
              <span className="ml-2 h-2 w-2 rounded-full bg-green-500" />
            )}
          </TabsTrigger>
          <div className="ml-auto flex items-center px-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={clearOutput}
              title="Clear Output"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </TabsList>
        <div className="flex-1 overflow-hidden">
          <TabsContent value="output" className="mt-0 h-full">
            <ScrollArea className="h-full">
              <div className="p-4 font-code text-sm">
                {isExecuting && (
                  <div className="text-muted-foreground animate-pulse">
                    <p>Executing code...</p>
                  </div>
                )}
                {!isExecuting && !currentResult && (
                  <div className="text-muted-foreground">
                    <p>Ready to execute. Click the Run button to execute your 4GL code.</p>
                  </div>
                )}
                {!isExecuting && currentResult && (
                  <div>
                    {currentResult.error ? (
                      <div className="text-red-400">
                        <p className="font-semibold mb-2">❌ Execution Error:</p>
                        <pre className="whitespace-pre-wrap">{currentResult.error}</pre>
                      </div>
                    ) : (
                      <div>
                        <div className="text-green-400 mb-2">
                          <p className="font-semibold">✓ Execution Successful</p>
                          {currentResult.executionTime && (
                            <p className="text-xs text-muted-foreground">
                              Completed in {(currentResult.executionTime * 1000).toFixed(2)}ms
                            </p>
                          )}
                        </div>
                        {currentResult.output && (
                          <div className="mt-2">
                            <p className="text-muted-foreground text-xs mb-1">Output:</p>
                            <pre className="whitespace-pre-wrap text-foreground">{currentResult.output}</pre>
                          </div>
                        )}
                        {!currentResult.output && (
                          <p className="text-muted-foreground mt-2">No output produced.</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="terminal" className="mt-0 h-full p-0 data-[state=inactive]:hidden" forceMount>
            {activeConfig ? (
              <SSHTerminal config={activeConfig} onConnectionChange={setIsTerminalConnected} />
            ) : (
              <div className="p-4">
                <p className="text-muted-foreground">No database connection configured.</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Configure a database connection to use the terminal.
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Go to <span className="font-semibold">Database → Configure Connection</span> to set up your SSH credentials.
                </p>
              </div>
            )}
          </TabsContent>
          <TabsContent value="debug" className="mt-0 h-full">
            <ScrollArea className="h-full">
              <div className="p-4 font-code text-sm">
                <p className="text-muted-foreground">Debug session ready.</p>
                <p className="text-xs text-muted-foreground mt-2">Debugging features coming soon...</p>
              </div>
            </ScrollArea>
          </TabsContent>
          <TabsContent value="sql" className="mt-0 h-full p-0">
            <SQLQueryPanel />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
