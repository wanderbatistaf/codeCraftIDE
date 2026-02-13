'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import { useFileSystem } from './file-system-context';
import { useToast } from '@/hooks/use-toast';
import { apiClient, API_BASE_URL } from '@/lib/api-client';

interface ProjectMetadata {
  name: string;
  version: string;
  description: string;
  created: string;
  modified: string;
}

interface ProjectContextType {
  currentProject: ProjectMetadata | null;
  isProjectLoaded: boolean;

  // Project operations
  createNewProject: (name: string, description: string) => Promise<void>;
  loadProject: (file: File) => Promise<void>;
  saveProject: () => Promise<void>;
  closeProject: () => void;

  // File operations
  importFiles: (files: File[]) => Promise<void>;
  importFolder: (files: File[]) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const { toast } = useToast();
  const fileSystem = useFileSystem();
  const [currentProject, setCurrentProject] = useState<ProjectMetadata | null>(null);

  const createNewProject = useCallback(
    async (name: string, description: string) => {
      try {
        const mode = fileSystem.mode;
        const remoteConfigName = fileSystem.remoteConfigName;
        const remoteConfig = fileSystem.remoteConfig;

        // Call API to create project with mode information
        const response = await fetch(`${API_BASE_URL}/api/project/create`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name,
            description,
            mode: mode,
            remote_config_name: remoteConfigName,
            remote_config: remoteConfig
          }),
        });

        const data = await response.json();

        if (data.status === 'error') {
          throw new Error(data.message);
        }

        setCurrentProject({
          name: data.project.name,
          version: data.project.version,
          description: data.project.description,
          created: data.project.created,
          modified: data.project.modified,
        });

        // Change workspace root to project folder
        console.log('Setting project root to:', name);
        await fileSystem.setProjectRoot(name);

        console.log('Project creation response:', data.project);
        console.log('IDE state:', data.project.ide_state);
        console.log('Open tabs:', data.project.ide_state?.open_tabs);

        // Open the main file
        if (data.project.ide_state?.open_tabs && data.project.ide_state.open_tabs.length > 0) {
          const mainFile = data.project.ide_state.open_tabs[0];
          console.log('Opening main file:', mainFile, 'Mode:', mode);

          // After setting project root, paths are now relative to project
          // Both remote and local: extract just the filename since root is now the project folder
          const fileName = mainFile.split('/').pop();
          const fileToOpen = `/${fileName}`;

          console.log('Adjusted file path:', fileToOpen);

          try {
            await fileSystem.openFile(fileToOpen, false);
            console.log('File opened successfully');
          } catch (error) {
            console.error('Error opening file:', error);
            toast({
              title: 'Warning',
              description: `Project created but failed to open main file: ${error instanceof Error ? error.message : String(error)}`,
              variant: 'default',
            });
          }
        }

        toast({
          title: 'Project Created',
          description: `Successfully created "${name}"`,
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: `Failed to create project: ${error instanceof Error ? error.message : String(error)}`,
          variant: 'destructive',
        });
        throw error;
      }
    },
    [fileSystem, toast]
  );

  const loadProject = useCallback(
    async (file: File) => {
      try {
        // Read file as ArrayBuffer for binary handling
        const arrayBuffer = await file.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);

        // Convert to base64 for API transmission
        let base64Content = '';
        const chunkSize = 0x8000; // Process in chunks to avoid call stack size issues
        for (let i = 0; i < bytes.length; i += chunkSize) {
          const chunk = bytes.subarray(i, i + chunkSize);
          base64Content += String.fromCharCode.apply(null, Array.from(chunk));
        }
        base64Content = btoa(base64Content);

        // Call API to load project
        const response = await fetch(`${API_BASE_URL}/api/project/load`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: base64Content }),
        });

        const data = await response.json();

        if (data.status === 'error') {
          throw new Error(data.message);
        }

        const project = data.project;

        // Clear current workspace
        // (In a real implementation, you'd want to confirm with user first)

        // Load files into workspace
        for (const file of project.files) {
          // Create file in workspace via file system API
          await fetch(`${API_BASE_URL}/api/files/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              path: file.path,
              content: file.content,
              is_file: true,
            }),
          });
        }

        // Open tabs from IDE state
        if (project.ide_state?.open_tabs) {
          for (const tabPath of project.ide_state.open_tabs) {
            await fileSystem.openFile(tabPath);
          }
        }

        // Set active tab
        if (project.ide_state?.active_tab) {
          const activeTab = fileSystem.openTabs.find(
            (t) => t.path === project.ide_state.active_tab
          );
          if (activeTab) {
            fileSystem.setActiveTab(activeTab.id);
          }
        }

        setCurrentProject({
          name: project.name,
          version: project.version,
          description: project.description,
          created: project.created,
          modified: project.modified,
        });

        // Refresh file tree
        await fileSystem.refreshFileTree();

        toast({
          title: 'Project Loaded',
          description: `Successfully loaded "${project.name}"`,
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: `Failed to load project: ${error instanceof Error ? error.message : String(error)}`,
          variant: 'destructive',
        });
        throw error;
      }
    },
    [fileSystem, toast]
  );

  const saveProject = useCallback(async () => {
    if (!currentProject) {
      toast({
        title: 'Error',
        description: 'No project loaded',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Collect all files from workspace
      const filesResponse = await fetch(`${API_BASE_URL}/api/files/tree`);
      const filesData = await filesResponse.json();

      // Build project data
      const projectData = {
        name: currentProject.name,
        version: currentProject.version,
        description: currentProject.description,
        created: currentProject.created,
        modified: new Date().toISOString(),
        files: await collectFilesFromTree(filesData.tree),
        ide_state: {
          open_tabs: fileSystem.openTabs.map((t) => t.path),
          active_tab: fileSystem.openTabs.find((t) => t.id === fileSystem.activeTabId)
            ?.path,
          expanded_folders: Array.from(fileSystem.expandedFolders),
        },
      };

      // Call API to get .ccp content
      const response = await fetch(`${API_BASE_URL}/api/project/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project: projectData }),
      });

      const data = await response.json();

      if (data.status === 'error') {
        throw new Error(data.message);
      }

      // Convert base64 content to binary for download
      const base64Content = data.content;
      const binaryString = atob(base64Content);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      // Download .ccp file as binary
      const blob = new Blob([bytes], { type: 'application/octet-stream' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: 'Project Saved',
        description: `Project saved as ${data.filename}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to save project: ${error instanceof Error ? error.message : String(error)}`,
        variant: 'destructive',
      });
      throw error;
    }
  }, [currentProject, fileSystem, toast]);

  const closeProject = useCallback(() => {
    setCurrentProject(null);
  }, []);

  const importFiles = useCallback(
    async (files: File[]) => {
      try {
        const mode = fileSystem.mode;
        const remoteConfigName = fileSystem.remoteConfigName;
        const remoteConfig = fileSystem.remoteConfig;
        const createdFolders = new Set<string>();
        const createdFiles = new Set<string>();

        const normalizeRelativePath = (file: File) =>
          (file as File).webkitRelativePath || file.name;

        const shouldIgnoreCreateError = (error: unknown) => {
          if (!(error instanceof Error)) return false;
          return error.message.includes("already exists") || error.message.includes("409");
        };

        for (const file of files) {
          const content = await file.text();
          const relativePath = normalizeRelativePath(file).replace(/^[\\/]+/, "");
          const parts = relativePath.split(/[\\/]/).filter(Boolean);
          if (parts.length === 0) {
            continue;
          }
          const fileName = parts[parts.length - 1];
          const folders = parts.slice(0, -1);

          let parentPath = "/";
          for (const folderName of folders) {
            const folderPath = parentPath === "/" ? `/${folderName}` : `${parentPath}/${folderName}`;
            if (!createdFolders.has(folderPath)) {
              try {
                if (mode === "remote" && remoteConfigName && remoteConfig) {
                  await apiClient.createSFTPNode(remoteConfigName, remoteConfig, parentPath, folderName, "folder");
                } else {
                  await apiClient.createNode(parentPath, folderName, "folder");
                }
              } catch (error) {
                if (!shouldIgnoreCreateError(error)) {
                  throw error;
                }
              }
              createdFolders.add(folderPath);
            }
            parentPath = folderPath;
          }

          const filePath = parentPath === "/" ? `/${fileName}` : `${parentPath}/${fileName}`;

          // Create file with content (route based on mode)
          if (mode === 'remote' && remoteConfigName && remoteConfig) {
            // Create file on remote server
            if (!createdFiles.has(filePath)) {
              try {
                await apiClient.createSFTPNode(remoteConfigName, remoteConfig, parentPath, fileName, 'file');
              } catch (error) {
                if (!shouldIgnoreCreateError(error)) {
                  throw error;
                }
              }
              createdFiles.add(filePath);
            }
            // Write content to file
            await apiClient.saveSFTPFileContent(remoteConfigName, remoteConfig, filePath, content);
          } else {
            // Create file locally
            if (!createdFiles.has(filePath)) {
              try {
                await apiClient.createNode(parentPath, fileName, 'file');
              } catch (error) {
                if (!shouldIgnoreCreateError(error)) {
                  throw error;
                }
              }
              createdFiles.add(filePath);
            }
            // Write content to file
            await apiClient.saveFileContent(filePath, content);
          }
        }

        // Refresh file tree
        await fileSystem.refreshFileTree();

        // Open the first imported file
        if (files.length > 0) {
          const firstFilePath = normalizeRelativePath(files[0]).replace(/^[\\/]+/, "");
          await fileSystem.openFile(`/${firstFilePath}`);
        }

        toast({
          title: 'Files Imported',
          description: `Successfully imported ${files.length} file(s)`,
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: `Failed to import files: ${error instanceof Error ? error.message : String(error)}`,
          variant: 'destructive',
        });
        throw error;
      }
    },
    [fileSystem, toast]
  );

  const importFolder = useCallback(
    async (files: File[]) => {
      await importFiles(files);
    },
    [importFiles]
  );

  return (
    <ProjectContext.Provider
      value={{
        currentProject,
        isProjectLoaded: currentProject !== null,
        createNewProject,
        loadProject,
        saveProject,
        closeProject,
        importFiles,
        importFolder,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider');
  }
  return context;
}

/**
 * Recursively collect files from file tree
 */
async function collectFilesFromTree(node: any): Promise<any[]> {
  const files = [];

  if (node.type === 'file') {
    // Fetch file content
    const response = await fetch(
      `${API_BASE_URL}/api/files/content?path=${encodeURIComponent(node.path)}`
    );
    const data = await response.json();

    files.push({
      path: node.path,
      content: data.content,
      type: getFileType(node.name),
    });
  } else if (node.type === 'folder' && node.children) {
    for (const child of node.children) {
      const childFiles = await collectFilesFromTree(child);
      files.push(...childFiles);
    }
  }

  return files;
}

function getFileType(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  const typeMap: Record<string, string> = {
    '4gl': '4gl',
    'per': 'per',
    'def': 'def',
    'sql': 'sql',
  };
  return typeMap[ext || ''] || 'text';
}
