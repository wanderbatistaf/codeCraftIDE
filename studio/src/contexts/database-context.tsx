"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient, type DatabaseConfig } from "@/lib/api-client";
import { useToast } from "@/hooks/use-toast";

type DatabaseContextType = {
  // State
  availableConfigs: DatabaseConfig[];
  activeConfig: DatabaseConfig | null;
  isConnected: boolean;
  isLoading: boolean;

  // Operations
  loadConfigs: () => Promise<void>;
  loadConfigWithPassword: (name: string) => Promise<DatabaseConfig>;
  testConnection: (config: DatabaseConfig) => Promise<boolean>;
  saveConfig: (config: DatabaseConfig) => Promise<void>;
  deleteConfig: (name: string) => Promise<void>;
  setActiveConfig: (config: DatabaseConfig | null) => void;
};

const DatabaseContext = createContext<DatabaseContextType | undefined>(undefined);

// Session storage keys (per-tab isolation)
const ACTIVE_CONFIG_KEY = "studio-ide-active-db-config";

// Helper to safely access sessionStorage (for SSR compatibility)
const getStorage = () => {
  if (typeof window !== "undefined") {
    return sessionStorage;
  }
  return null;
};

export function DatabaseProvider({ children }: { children: React.ReactNode }) {
  const [availableConfigs, setAvailableConfigs] = useState<DatabaseConfig[]>([]);
  const [activeConfig, setActiveConfigState] = useState<DatabaseConfig | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // Load configurations from backend on mount
  const loadConfigs = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.getDatabaseConfigs();
      setAvailableConfigs(response.configs);
    } catch (error) {
      console.error("Failed to load database configurations:", error);
      toast({
        title: "Error",
        description: "Failed to load database configurations",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  // Load a specific configuration with password from backend
  const loadConfigWithPassword = useCallback(async (name: string): Promise<DatabaseConfig> => {
    try {
      const config = await apiClient.getDatabaseConfig(name);
      return config;
    } catch (error) {
      console.error("Failed to load database configuration with password:", error);
      toast({
        title: "Error",
        description: "Failed to load database configuration",
        variant: "destructive",
      });
      throw error;
    }
  }, [toast]);

  // Load active config from localStorage on mount
  useEffect(() => {
    const initializeState = async () => {
      // Load configs from backend
      await loadConfigs();

      // Load active config from sessionStorage (per-tab isolation)
      const storage = getStorage();
      try {
        const savedConfig = storage?.getItem(ACTIVE_CONFIG_KEY);
        if (savedConfig) {
          const config = JSON.parse(savedConfig);

          // If the config has a masked password, fetch the full config from backend
          if (config.name && config.password === "***") {
            try {
              const fullConfig = await loadConfigWithPassword(config.name);
              setActiveConfigState(fullConfig);
            } catch (error) {
              console.error("Failed to load full config from backend, using cached version:", error);
              // Fall back to cached config (even with masked password)
              setActiveConfigState(config);
            }
          } else {
            setActiveConfigState(config);
          }
        }
      } catch (error) {
        console.error("Failed to load active database config from sessionStorage:", error);
      }
    };

    initializeState();
  }, [loadConfigs, loadConfigWithPassword]);

  // Save active config to sessionStorage whenever it changes (per-tab isolation)
  useEffect(() => {
    const storage = getStorage();
    try {
      if (activeConfig) {
        storage?.setItem(ACTIVE_CONFIG_KEY, JSON.stringify(activeConfig));
      } else {
        storage?.removeItem(ACTIVE_CONFIG_KEY);
      }
    } catch (error) {
      console.error("Failed to save active config to sessionStorage:", error);
    }
  }, [activeConfig]);

  const testConnection = useCallback(async (config: DatabaseConfig): Promise<boolean> => {
    try {
      setIsLoading(true);
      const response = await apiClient.testDatabaseConnection(config);

      if (response.success) {
        toast({
          title: "Connection Successful",
          description: response.message,
        });
        setIsConnected(true);
        return true;
      } else {
        toast({
          title: "Connection Failed",
          description: response.error || response.message,
          variant: "destructive",
        });
        setIsConnected(false);
        return false;
      }
    } catch (error) {
      toast({
        title: "Connection Error",
        description: `Failed to test connection: ${error}`,
        variant: "destructive",
      });
      setIsConnected(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const saveConfig = useCallback(async (config: DatabaseConfig) => {
    try {
      setIsLoading(true);
      const response = await apiClient.saveDatabaseConfig(config);

      if (response.success) {
        toast({
          title: "Saved",
          description: response.message,
        });
        await loadConfigs();
      } else {
        throw new Error("Failed to save configuration");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to save configuration: ${error}`,
        variant: "destructive",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [toast, loadConfigs]);

  const deleteConfig = useCallback(async (name: string) => {
    try {
      setIsLoading(true);
      const response = await apiClient.deleteDatabaseConfig(name);

      if (response.success) {
        toast({
          title: "Deleted",
          description: response.message,
        });

        // If the deleted config was active, clear it
        if (activeConfig?.name === name) {
          setActiveConfigState(null);
          setIsConnected(false);
        }

        await loadConfigs();
      } else {
        throw new Error("Failed to delete configuration");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to delete configuration: ${error}`,
        variant: "destructive",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [toast, loadConfigs, activeConfig]);

  const setActiveConfig = useCallback((config: DatabaseConfig | null) => {
    setActiveConfigState(config);
    if (!config) {
      setIsConnected(false);
    }
  }, []);

  const value: DatabaseContextType = {
    availableConfigs,
    activeConfig,
    isConnected,
    isLoading,
    loadConfigs,
    loadConfigWithPassword,
    testConnection,
    saveConfig,
    deleteConfig,
    setActiveConfig,
  };

  return (
    <DatabaseContext.Provider value={value}>
      {children}
    </DatabaseContext.Provider>
  );
}

export function useDatabase() {
  const context = useContext(DatabaseContext);
  if (context === undefined) {
    throw new Error("useDatabase must be used within a DatabaseProvider");
  }
  return context;
}
