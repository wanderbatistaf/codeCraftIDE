"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  type FileTreeNode,
  initialFileTree,
  findNodeByPath,
  findNodeById,
  generateId,
  getParentPath,
} from "@/lib/file-tree";
import { apiClient, type DatabaseConfig } from "@/lib/api-client";

export type FileSystemMode = "local" | "remote";

export type EditorTab = {
  id: string;
  path: string;
  name: string;
  content: string;
  isDirty: boolean;
  isExternal?: boolean; // True for files outside workspace (absolute paths)
};

type FileSystemContextType = {
  fileTree: FileTreeNode;
  openTabs: EditorTab[];
  activeTabId: string | null;
  expandedFolders: Set<string>;
  isLoading: boolean;

  // Mode state
  mode: FileSystemMode;
  remoteConfigName: string | null;
  remoteConfig: DatabaseConfig | null;
  setMode: (mode: FileSystemMode, configName?: string, config?: DatabaseConfig) => Promise<void>;

  // File operations
  createFile: (parentPath: string, fileName: string) => Promise<void>;
  createFolder: (parentPath: string, folderName: string) => Promise<void>;
  deleteNode: (nodeId: string) => Promise<void>;
  renameNode: (nodeId: string, newName: string) => Promise<void>;

  // Editor operations
  openFile: (path: string) => Promise<void>;
  closeTab: (tabId: string) => void;
  setActiveTab: (tabId: string) => void;
  updateFileContent: (path: string, content: string) => void;
  saveFile: (path: string) => Promise<void>;
  saveAllFiles: () => Promise<void>;

  // Folder operations
  toggleFolder: (folderId: string) => void;
  expandFolder: (folderId: string) => void;
  collapseFolder: (folderId: string) => void;

  // Utility
  refreshFileTree: () => Promise<void>;
  setProjectRoot: (projectName: string) => Promise<void>;
};

const FileSystemContext = createContext<FileSystemContextType | undefined>(undefined);

// Session storage keys for per-tab state (sessionStorage is automatically isolated per browser tab)
const TABS_STORAGE_KEY = "studio-ide-open-tabs";
const EXPANDED_FOLDERS_KEY = "studio-ide-expanded-folders";
const MODE_STORAGE_KEY = "studio-file-system-mode";
const REMOTE_CONFIG_NAME_KEY = "studio-remote-config-name";
const REMOTE_CONFIG_KEY = "studio-remote-config";

// Helper to safely access sessionStorage (for SSR compatibility)
const getStorage = () => {
  if (typeof window !== "undefined") {
    return sessionStorage;
  }
  return null;
};

export function FileSystemProvider({ children }: { children: React.ReactNode }) {
  const [fileTree, setFileTree] = useState<FileTreeNode>(initialFileTree);
  const [openTabs, setOpenTabs] = useState<EditorTab[]>([]);
  const [activeTabId, setActiveTabId] = useState<string | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["root", "examples"]));
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Mode state
  const [mode, setModeState] = useState<FileSystemMode>("local");
  const [remoteConfigName, setRemoteConfigName] = useState<string | null>(null);
  const [remoteConfig, setRemoteConfig] = useState<DatabaseConfig | null>(null);

  // Load file tree from backend on mount (routes based on mode)
  const loadFileTree = useCallback(async () => {
    try {
      setIsLoading(true);

      if (mode === "remote" && remoteConfigName && remoteConfig) {
        // Load from SFTP server
        const response = await apiClient.getSFTPTree(remoteConfigName, remoteConfig);
        setFileTree(response.tree);
      } else {
        // Load from local backend
        const response = await apiClient.getFileTree();
        setFileTree(response.tree);
      }
    } catch (error) {
      console.error("Failed to load file tree:", error);
      // Fall back to initial tree in local mode
      if (mode === "local") {
        setFileTree(initialFileTree);
      }
    } finally {
      setIsLoading(false);
    }
  }, [mode, remoteConfigName, remoteConfig]);

  // Load UI state from localStorage and file tree from backend on mount
  useEffect(() => {
    const initializeState = async () => {
      let currentMode: FileSystemMode = "local";
      let currentConfigName: string | null = null;
      let currentConfig: DatabaseConfig | null = null;

      // Load mode from sessionStorage FIRST (before loading file tree)
      // Using sessionStorage ensures each browser tab has its own session
      const storage = getStorage();
      try {
        const savedMode = storage?.getItem(MODE_STORAGE_KEY) as FileSystemMode;
        const savedConfigName = storage?.getItem(REMOTE_CONFIG_NAME_KEY);
        const savedConfig = storage?.getItem(REMOTE_CONFIG_KEY);

        if (savedMode === "remote" && savedConfigName && savedConfig) {
          const config = JSON.parse(savedConfig) as DatabaseConfig;
          currentMode = "remote";
          currentConfigName = savedConfigName;
          currentConfig = config;
          setModeState("remote");
          setRemoteConfigName(savedConfigName);
          setRemoteConfig(config);
        }
      } catch (error) {
        console.error("Failed to load mode from localStorage:", error);
      }

      // Load file tree from backend (inline logic to avoid dependency)
      let loadedTree = initialFileTree;
      try {
        setIsLoading(true);

        if (currentMode === "remote" && currentConfigName && currentConfig) {
          // Try to load from SFTP server
          try {
            const response = await apiClient.getSFTPTree(currentConfigName, currentConfig);
            loadedTree = response.tree;
            setFileTree(response.tree);
          } catch (sftpError) {
            console.error("Failed to connect via SFTP, falling back to local mode:", sftpError);
            // Fall back to local mode if SFTP fails
            currentMode = "local";
            setModeState("local");
            setRemoteConfigName(null);
            setRemoteConfig(null);
            // Clear from sessionStorage
            storage?.removeItem(MODE_STORAGE_KEY);
            storage?.removeItem(REMOTE_CONFIG_NAME_KEY);
            storage?.removeItem(REMOTE_CONFIG_KEY);
            // Load local tree
            const response = await apiClient.getFileTree();
            loadedTree = response.tree;
            setFileTree(response.tree);
          }
        } else {
          // Load from local backend
          const response = await apiClient.getFileTree();
          loadedTree = response.tree;
          setFileTree(response.tree);
        }
      } catch (error) {
        console.error("Failed to load file tree:", error);
        // Fall back to initial tree
        loadedTree = initialFileTree;
        setFileTree(initialFileTree);
      } finally {
        setIsLoading(false);
      }

      // Load UI state from sessionStorage (per-tab state)
      let hasOpenTabs = false;
      try {
        const savedTabs = storage?.getItem(TABS_STORAGE_KEY);
        if (savedTabs) {
          const tabs = JSON.parse(savedTabs);
          // Validate tabs still exist in file tree
          if (tabs.length > 0) {
            setOpenTabs(tabs);
            setActiveTabId(tabs[0].id);
            hasOpenTabs = true;
          }
        }

        const savedExpanded = storage?.getItem(EXPANDED_FOLDERS_KEY);
        if (savedExpanded) {
          setExpandedFolders(new Set(JSON.parse(savedExpanded)));
        }
      } catch (error) {
        console.error("Failed to load UI state from sessionStorage:", error);
      }

      // If no tabs are open, try to auto-open the hello.4gl example (if it exists)
      if (!hasOpenTabs) {
        try {
          // Only try to open if the file exists in the tree
          const findNode = (node: FileTreeNode, path: string): FileTreeNode | null => {
            if (node.path === path) return node;
            if (node.children) {
              for (const child of node.children) {
                const found = findNode(child, path);
                if (found) return found;
              }
            }
            return null;
          };

          const exampleFile = loadedTree ? findNode(loadedTree, "/examples/hello.4gl") : null;
          if (exampleFile) {
            // Use appropriate API based on mode
            let content: string;
            if (currentMode === "remote" && currentConfigName && currentConfig) {
              const response = await apiClient.getSFTPFileContent(currentConfigName, currentConfig, "/examples/hello.4gl");
              content = response.content || "";
            } else {
              const response = await apiClient.getFileContent("/examples/hello.4gl");
              content = response.content || "";
            }
            const newTab: EditorTab = {
              id: "examples/hello.4gl",
              path: "/examples/hello.4gl",
              name: "hello.4gl",
              content,
              isDirty: false,
            };
            setOpenTabs([newTab]);
            setActiveTabId(newTab.id);
            // Auto-expand examples folder
            setExpandedFolders((prev) => new Set([...prev, "examples"]));
          }
        } catch (error) {
          // Silently ignore - file may not exist in clean workspace
          console.debug("Example file not available:", error);
        }
      }

      setIsInitialized(true);
    };

    initializeState();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  // Save open tabs to sessionStorage whenever they change (per-tab state)
  useEffect(() => {
    if (isInitialized) {
      const storage = getStorage();
      try {
        storage?.setItem(TABS_STORAGE_KEY, JSON.stringify(openTabs));
      } catch (error) {
        console.error("Failed to save tabs to sessionStorage:", error);
      }
    }
  }, [openTabs, isInitialized]);

  // Save expanded folders to sessionStorage (per-tab state)
  useEffect(() => {
    if (isInitialized) {
      const storage = getStorage();
      try {
        storage?.setItem(
          EXPANDED_FOLDERS_KEY,
          JSON.stringify(Array.from(expandedFolders))
        );
      } catch (error) {
        console.error("Failed to save expanded folders to sessionStorage:", error);
      }
    }
  }, [expandedFolders, isInitialized]);

  const setMode = useCallback(async (newMode: FileSystemMode, configName?: string, config?: DatabaseConfig) => {
    // Validate no unsaved changes
    const dirtyTabs = openTabs.filter(t => t.isDirty);
    if (dirtyTabs.length > 0) {
      throw new Error(`You have ${dirtyTabs.length} unsaved file(s). Save or discard changes before switching modes.`);
    }

    // Update mode state
    setModeState(newMode);
    setRemoteConfigName(newMode === "remote" ? configName || null : null);
    setRemoteConfig(newMode === "remote" ? config || null : null);

    // Persist to sessionStorage (per-tab state)
    const storage = getStorage();
    try {
      storage?.setItem(MODE_STORAGE_KEY, newMode);
      if (newMode === "remote" && configName && config) {
        storage?.setItem(REMOTE_CONFIG_NAME_KEY, configName);
        storage?.setItem(REMOTE_CONFIG_KEY, JSON.stringify(config));
      } else {
        storage?.removeItem(REMOTE_CONFIG_NAME_KEY);
        storage?.removeItem(REMOTE_CONFIG_KEY);
      }
    } catch (error) {
      console.error("Failed to save mode to sessionStorage:", error);
    }

    // Close all tabs
    setOpenTabs([]);
    setActiveTabId(null);

    // Reload file tree with NEW mode values (not from state)
    try {
      setIsLoading(true);

      if (newMode === "remote" && configName && config) {
        // Load from SFTP server
        const response = await apiClient.getSFTPTree(configName, config);
        setFileTree(response.tree);
      } else {
        // Load from local backend
        const response = await apiClient.getFileTree();
        setFileTree(response.tree);
      }
    } catch (error) {
      console.error("Failed to load file tree:", error);
      // Fall back to initial tree in local mode
      if (newMode === "local") {
        setFileTree(initialFileTree);
      }
    } finally {
      setIsLoading(false);
    }
  }, [openTabs]);

  const createFile = useCallback(async (parentPath: string, fileName: string) => {
    try {
      setIsLoading(true);

      if (mode === "remote" && remoteConfigName && remoteConfig) {
        await apiClient.createSFTPNode(remoteConfigName, remoteConfig, parentPath, fileName, "file");
      } else {
        await apiClient.createNode(parentPath, fileName, "file");
      }

      await loadFileTree();
    } catch (error) {
      console.error("Failed to create file:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [mode, remoteConfigName, remoteConfig, loadFileTree]);

  const createFolder = useCallback(async (parentPath: string, folderName: string) => {
    try {
      setIsLoading(true);

      let response;
      if (mode === "remote" && remoteConfigName && remoteConfig) {
        response = await apiClient.createSFTPNode(remoteConfigName, remoteConfig, parentPath, folderName, "folder");
      } else {
        response = await apiClient.createNode(parentPath, folderName, "folder");
      }

      await loadFileTree();
      // Auto-expand the newly created folder
      if (response.node) {
        setExpandedFolders((prev) => new Set([...prev, response.node.id]));
      }
    } catch (error) {
      console.error("Failed to create folder:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [mode, remoteConfigName, remoteConfig, loadFileTree]);

  const deleteNode = useCallback(async (nodeId: string) => {
    try {
      setIsLoading(true);
      const node = findNodeById(fileTree, nodeId);
      if (!node) throw new Error("Node not found");

      // Close any open tabs for files in this node
      setOpenTabs((prev) => {
        const pathsToClose = new Set<string>();
        const collectPaths = (n: FileTreeNode) => {
          if (n.type === "file") {
            pathsToClose.add(n.path);
          }
          n.children?.forEach(collectPaths);
        };
        collectPaths(node);

        const remainingTabs = prev.filter((tab) => !pathsToClose.has(tab.path));

        // Update active tab if needed
        if (activeTabId && prev.find(t => t.id === activeTabId) && !remainingTabs.find(t => t.id === activeTabId)) {
          setActiveTabId(remainingTabs.length > 0 ? remainingTabs[0].id : null);
        }

        return remainingTabs;
      });

      if (mode === "remote" && remoteConfigName && remoteConfig) {
        await apiClient.deleteSFTPNode(remoteConfigName, remoteConfig, node.path, node.type === "folder");
      } else {
        await apiClient.deleteNode(node.path);
      }

      await loadFileTree();
    } catch (error) {
      console.error("Failed to delete node:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [fileTree, activeTabId, mode, remoteConfigName, remoteConfig, loadFileTree]);

  const renameNode = useCallback(async (nodeId: string, newName: string) => {
    try {
      setIsLoading(true);
      const node = findNodeById(fileTree, nodeId);
      if (!node) throw new Error("Node not found");

      const parentPath = getParentPath(node.path);
      const newPath = `${parentPath === "/" ? "" : parentPath}/${newName}`;
      const newId = generateId(newPath);

      if (mode === "remote" && remoteConfigName && remoteConfig) {
        await apiClient.renameSFTPNode(remoteConfigName, remoteConfig, node.path, newName);
      } else {
        await apiClient.renameNode(node.path, newName);
      }

      await loadFileTree();

      // Update any open tabs with the old path
      setOpenTabs((prev) =>
        prev.map((tab) =>
          tab.path === node.path
            ? { ...tab, path: newPath, name: newName, id: newId }
            : tab
        )
      );
    } catch (error) {
      console.error("Failed to rename node:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [fileTree, mode, remoteConfigName, remoteConfig, loadFileTree]);

  const openFile = useCallback(async (path: string, isExternal: boolean = false) => {
    // Check if already open
    const existingTab = openTabs.find((tab) => tab.path === path);
    if (existingTab) {
      setActiveTabId(existingTab.id);
      return;
    }

    try {
      setIsLoading(true);

      let content: string;
      let fileName: string;
      let fileId: string;

      if (isExternal) {
        // External file (absolute path, not in tree)
        if (mode === "remote" && remoteConfigName && remoteConfig) {
          const response = await apiClient.getSFTPFileContentAbsolute(remoteConfigName, remoteConfig, path);
          content = response.content || "";
        } else {
          throw new Error("External files only supported in remote mode");
        }

        // Extract filename from absolute path
        const parts = path.split("/");
        fileName = parts[parts.length - 1];
        fileId = `external-${path.replace(/[^a-zA-Z0-9]/g, "-")}`;
      } else {
        // File in tree
        const node = findNodeByPath(fileTree, path);
        if (!node || node.type !== "file") return;

        // Fetch content from backend (route based on mode)
        if (mode === "remote" && remoteConfigName && remoteConfig) {
          const response = await apiClient.getSFTPFileContent(remoteConfigName, remoteConfig, path);
          content = response.content || "";
        } else {
          const response = await apiClient.getFileContent(path);
          content = response.content || "";
        }

        fileName = node.name;
        fileId = node.id;
      }

      // Create new tab
      const newTab: EditorTab = {
        id: fileId,
        path: path,
        name: fileName,
        content,
        isDirty: false,
        isExternal,
      };

      setOpenTabs((prev) => [...prev, newTab]);
      setActiveTabId(newTab.id);
    } catch (error) {
      console.error("Failed to open file:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [fileTree, openTabs, mode, remoteConfigName, remoteConfig]);

  const closeTab = useCallback((tabId: string) => {
    setOpenTabs((prev) => {
      const newTabs = prev.filter((tab) => tab.id !== tabId);

      // If closing the active tab, switch to another
      if (activeTabId === tabId) {
        const closedIndex = prev.findIndex((tab) => tab.id === tabId);
        if (newTabs.length > 0) {
          // Try to activate the tab to the right, or the one to the left
          const newActiveTab = newTabs[closedIndex] || newTabs[closedIndex - 1];
          setActiveTabId(newActiveTab.id);
        } else {
          setActiveTabId(null);
        }
      }

      return newTabs;
    });
  }, [activeTabId]);

  const updateFileContent = useCallback((path: string, content: string) => {
    // Update tab content and mark as dirty
    setOpenTabs((prev) =>
      prev.map((tab) =>
        tab.path === path ? { ...tab, content, isDirty: true } : tab
      )
    );
  }, []);

  const saveFile = useCallback(async (path: string) => {
    const tab = openTabs.find((t) => t.path === path);
    if (!tab) return;

    try {
      setIsLoading(true);

      // Save to backend (route based on mode and whether file is external)
      if (mode === "remote" && remoteConfigName && remoteConfig) {
        if (tab.isExternal) {
          // External file: use absolute path endpoint
          await apiClient.saveSFTPFileContentAbsolute(remoteConfigName, remoteConfig, path, tab.content);
        } else {
          // Workspace file: use relative path endpoint
          await apiClient.saveSFTPFileContent(remoteConfigName, remoteConfig, path, tab.content);
        }
      } else {
        await apiClient.saveFileContent(path, tab.content);
      }

      // Mark tab as clean
      setOpenTabs((prev) =>
        prev.map((t) => (t.path === path ? { ...t, isDirty: false } : t))
      );

      // Refresh file tree only for workspace files (external files aren't in tree)
      if (!tab.isExternal) {
        await loadFileTree();
      }
    } catch (error) {
      console.error("Failed to save file:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [openTabs, mode, remoteConfigName, remoteConfig, loadFileTree]);

  const saveAllFiles = useCallback(async () => {
    const dirtyTabs = openTabs.filter(tab => tab.isDirty);

    try {
      setIsLoading(true);

      // Save all dirty files in parallel (route based on mode and external status)
      if (mode === "remote" && remoteConfigName && remoteConfig) {
        await Promise.all(
          dirtyTabs.map(tab =>
            tab.isExternal
              ? apiClient.saveSFTPFileContentAbsolute(remoteConfigName, remoteConfig, tab.path, tab.content)
              : apiClient.saveSFTPFileContent(remoteConfigName, remoteConfig, tab.path, tab.content)
          )
        );
      } else {
        await Promise.all(
          dirtyTabs.map(tab => apiClient.saveFileContent(tab.path, tab.content))
        );
      }

      // Mark all tabs as clean
      setOpenTabs((prev) =>
        prev.map((t) => ({ ...t, isDirty: false }))
      );

      // Refresh file tree
      await loadFileTree();
    } catch (error) {
      console.error("Failed to save all files:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [openTabs, mode, remoteConfigName, remoteConfig, loadFileTree]);

  const toggleFolder = useCallback((folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  }, []);

  const expandFolder = useCallback((folderId: string) => {
    setExpandedFolders((prev) => new Set([...prev, folderId]));
  }, []);

  const collapseFolder = useCallback((folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      next.delete(folderId);
      return next;
    });
  }, []);

  const setProjectRoot = useCallback(async (projectName: string) => {
    try {
      setIsLoading(true);

      if (mode === "remote" && remoteConfigName && remoteConfig) {
        // Update workspace path to project folder
        const currentWorkspace = remoteConfig.remote_workspace_path || "~/fgl-projects";
        const newWorkspacePath = `${currentWorkspace}/${projectName}`;

        const updatedConfig = {
          ...remoteConfig,
          remote_workspace_path: newWorkspacePath
        };

        // Update config and reload tree
        setRemoteConfig(updatedConfig);

        // Save to sessionStorage (per-tab state)
        const storage = getStorage();
        try {
          storage?.setItem(REMOTE_CONFIG_KEY, JSON.stringify(updatedConfig));
        } catch (error) {
          console.error("Failed to save updated config:", error);
        }

        // Reload file tree with new workspace
        const response = await apiClient.getSFTPTree(remoteConfigName, updatedConfig);
        setFileTree(response.tree);

      } else {
        // Local mode: extract project subtree and make it root
        const projectNode = findNodeByPath(fileTree, `/${projectName}`);

        if (projectNode && projectNode.type === "folder") {
          // Helper to adjust paths recursively
          const adjustPaths = (node: FileTreeNode, parentPath: string): FileTreeNode => {
            const newPath = parentPath === "/" ? `/${node.name}` : `${parentPath}/${node.name}`;
            return {
              ...node,
              path: newPath,
              children: node.children?.map(child => adjustPaths(child, newPath))
            };
          };

          // Make the project folder the new root with adjusted paths
          const newRoot: FileTreeNode = {
            ...projectNode,
            id: "root",
            path: "/",
            name: projectName,
            children: projectNode.children?.map(child => adjustPaths(child, ""))
          };

          console.log('New file tree root:', newRoot);
          setFileTree(newRoot);
        } else {
          console.error('Project node not found:', projectName, 'in tree:', fileTree);
        }
      }

      // Reset expanded folders
      setExpandedFolders(new Set(["root"]));

    } catch (error) {
      console.error("Failed to set project root:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [mode, remoteConfigName, remoteConfig, fileTree]);

  const value: FileSystemContextType = {
    fileTree,
    openTabs,
    activeTabId,
    expandedFolders,
    isLoading,
    mode,
    remoteConfigName,
    remoteConfig,
    setMode,
    createFile,
    createFolder,
    deleteNode,
    renameNode,
    openFile,
    closeTab,
    setActiveTab: setActiveTabId,
    updateFileContent,
    saveFile,
    saveAllFiles,
    toggleFolder,
    expandFolder,
    collapseFolder,
    refreshFileTree: loadFileTree,
    setProjectRoot,
  };

  return (
    <FileSystemContext.Provider value={value}>
      {children}
    </FileSystemContext.Provider>
  );
}

export function useFileSystem() {
  const context = useContext(FileSystemContext);
  if (context === undefined) {
    throw new Error("useFileSystem must be used within a FileSystemProvider");
  }
  return context;
}
