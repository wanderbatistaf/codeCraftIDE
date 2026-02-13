"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { apiClient, type ExecuteResponse } from "@/lib/api-client";
import { useDatabase } from "@/contexts/database-context";

export type ExecutionResult = {
  output: string;
  executionTime?: number;
  error?: string;
  timestamp: number;
};

type ExecutionContextType = {
  isExecuting: boolean;
  currentResult: ExecutionResult | null;
  executionHistory: ExecutionResult[];
  executeCode: (code: string) => Promise<void>;
  clearOutput: () => void;
};

const ExecutionContext = createContext<ExecutionContextType | undefined>(undefined);

export function ExecutionProvider({ children }: { children: React.ReactNode }) {
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentResult, setCurrentResult] = useState<ExecutionResult | null>(null);
  const [executionHistory, setExecutionHistory] = useState<ExecutionResult[]>([]);
  const { activeConfig } = useDatabase();

  const executeCode = useCallback(async (code: string) => {
    setIsExecuting(true);
    const startTime = Date.now();

    try {
      const response: ExecuteResponse = await apiClient.executeCode({
        code,
        database_config: activeConfig || undefined,
        enable_profiling: false,
      });

      const result: ExecutionResult = {
        output: response.output || "",
        executionTime: response.execution_time,
        error: response.status === "error" ? response.message : undefined,
        timestamp: Date.now(),
      };

      setCurrentResult(result);
      setExecutionHistory((prev) => [result, ...prev].slice(0, 50)); // Keep last 50 executions
    } catch (error) {
      const result: ExecutionResult = {
        output: "",
        error: error instanceof Error ? error.message : "Unknown error occurred",
        timestamp: Date.now(),
      };
      setCurrentResult(result);
      setExecutionHistory((prev) => [result, ...prev].slice(0, 50));
    } finally {
      setIsExecuting(false);
    }
  }, [activeConfig]);

  const clearOutput = useCallback(() => {
    setCurrentResult(null);
  }, []);

  const value: ExecutionContextType = {
    isExecuting,
    currentResult,
    executionHistory,
    executeCode,
    clearOutput,
  };

  return (
    <ExecutionContext.Provider value={value}>
      {children}
    </ExecutionContext.Provider>
  );
}

export function useExecution() {
  const context = useContext(ExecutionContext);
  if (context === undefined) {
    throw new Error("useExecution must be used within an ExecutionProvider");
  }
  return context;
}
