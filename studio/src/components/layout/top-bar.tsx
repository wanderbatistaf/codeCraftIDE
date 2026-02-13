"use client";

import { useState, useRef, useEffect } from "react";
import {
  Menubar,
  MenubarContent,
  MenubarItem,
  MenubarMenu,
  MenubarSeparator,
  MenubarShortcut,
  MenubarTrigger,
} from "@/components/ui/menubar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { LogoIcon } from "@/components/icons/logo";
import { useFileSystem } from "@/contexts/file-system-context";
import { useDatabase } from "@/contexts/database-context";
import { useProject } from "@/contexts/project-context";
import { useToast } from "@/hooks/use-toast";
import { DatabaseConfigDialog } from "@/components/database-config-dialog";
import { RemoteFileBrowser } from "@/components/remote-file-browser";
import { CommandPalette } from "@/components/command-palette";
import { DocumentationDialog } from "@/components/documentation-dialog";
import { Badge } from "@/components/ui/badge";
import { Wand2, Server, HardDrive } from "lucide-react";
import { useEditor } from '@/contexts/editor-context';
import { apiClient } from "@/lib/api-client";
import { UserMenu } from "@/components/auth/user-menu";
import { useSession } from "@/contexts/session-context";

export function TopBar() {
  const { createFile, createFolder, saveFile, saveAllFiles, openTabs, activeTabId, refreshFileTree, openFile, updateFileContent, mode, remoteConfigName, remoteConfig, setMode } = useFileSystem();
  const { activeConfig, setActiveConfig } = useDatabase();
  const { sessionId } = useSession();
  const project = useProject();
  const { editorRef } = useEditor();
  const { toast } = useToast();
  const [showDatabaseDialog, setShowDatabaseDialog] = useState(false);
  const [showNewProjectDialog, setShowNewProjectDialog] = useState(false);
  const [showAboutDialog, setShowAboutDialog] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const projectInputRef = useRef<HTMLInputElement>(null);
  const [showRemoteFileBrowser, setShowRemoteFileBrowser] = useState(false);
  const [showRemoteFolderBrowser, setShowRemoteFolderBrowser] = useState(false);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showDocumentation, setShowDocumentation] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      // Ctrl+P / Cmd+P - Command Palette
      if (e.key === "p" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setShowCommandPalette((open) => !open);
      }
      // Ctrl+Shift+H - Documentation (Help)
      if (e.key === "H" && (e.metaKey || e.ctrlKey) && e.shiftKey) {
        e.preventDefault();
        setShowDocumentation((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleNewFile = async () => {
    const fileName = prompt("Enter file name:");
    if (fileName) {
      try {
        await createFile("/", fileName);
        toast({
          title: "Created",
          description: `File ${fileName} created.`,
        });
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to create file`,
          variant: "destructive",
        });
      }
    }
  };

  const handleNewFolder = async () => {
    const folderName = prompt("Enter folder name:");
    if (folderName) {
      try {
        await createFolder("/", folderName);
        toast({
          title: "Created",
          description: `Folder ${folderName} created.`,
        });
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to create folder`,
          variant: "destructive",
        });
      }
    }
  };

  const handleSave = async () => {
    const activeTab = openTabs.find(t => t.id === activeTabId);
    if (activeTab) {
      try {
        await saveFile(activeTab.path);
        toast({
          title: "Saved",
          description: `${activeTab.name} has been saved.`,
        });
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to save file`,
          variant: "destructive",
        });
      }
    }
  };

  const handleSaveAll = async () => {
    try {
      await saveAllFiles();
      toast({
        title: "Saved All",
        description: "All files have been saved.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to save files`,
        variant: "destructive",
      });
    }
  };

  const handleNewProject = async () => {
    if (!newProjectName.trim()) {
      toast({
        title: 'Error',
        description: 'Project name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      await project.createNewProject(newProjectName, newProjectDescription);
      setShowNewProjectDialog(false);
      setNewProjectName('');
      setNewProjectDescription('');
      toast({
        title: 'Project Created',
        description: `New project "${newProjectName}" created successfully`,
      });
    } catch (error) {
      // Error already handled by context
    }
  };

  const handleOpenProject = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.ccp')) {
        try {
          await project.loadProject(file);
        } catch (error) {
          // Error already handled by context
        }
      } else {
        toast({
          title: 'Invalid File',
          description: 'Please select a .ccp (CodeCraft Project) file',
          variant: 'destructive',
        });
      }
    }
    // Reset input
    if (projectInputRef.current) {
      projectInputRef.current.value = '';
    }
  };

  const handleOpenFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      try {
        await project.importFiles(Array.from(files));
      } catch (error) {
        // Error already handled by context
      }
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleOpenFolder = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      try {
        await project.importFolder(Array.from(files));
      } catch (error) {
        // Error already handled by context
      }
    }
    // Reset input
    if (folderInputRef.current) {
      folderInputRef.current.value = '';
    }
  };

  const handleOpenFileClick = () => {
    if (mode === "remote" && remoteConfigName && remoteConfig) {
      // Open remote file browser
      setShowRemoteFileBrowser(true);
    } else {
      // Use native file picker
      fileInputRef.current?.click();
    }
  };

  const handleOpenFolderClick = () => {
    if (mode === "remote" && remoteConfigName && remoteConfig) {
      // Open remote folder browser
      setShowRemoteFolderBrowser(true);
    } else {
      // Use native folder picker
      folderInputRef.current?.click();
    }
  };

  const handleRemoteFilesSelect = async (selections: string[]) => {
    try {
      // Open each selected file as external (absolute path)
      for (const filePath of selections) {
        await openFile(filePath, true); // isExternal = true
      }
      toast({
        title: "Files Opened",
        description: `Opened ${selections.length} file(s) from server`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to open files",
        variant: "destructive",
      });
    }
  };

  const handleRemoteFolderSelect = async (selections: string[]) => {
    if (selections.length === 0) return;
    if (!remoteConfigName || !remoteConfig) return;

    const folderPath = selections[0];
    try {
      // Navigate to the selected folder
      toast({
        title: "Navigating...",
        description: `Opening ${folderPath}`,
      });

      // Update workspace path to the selected folder and reload tree
      const updatedConfig = {
        ...remoteConfig,
        remote_workspace_path: folderPath
      };

      // Update mode with new config (this will reload the tree)
      await setMode("remote", remoteConfigName, updatedConfig);

      toast({
        title: "Folder Opened",
        description: `Now browsing: ${folderPath}`,
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error?.message || "Failed to open folder",
        variant: "destructive",
      });
    }
  };

  const handleCompile = async () => {
    const activeTab = openTabs.find(t => t.id === activeTabId);
    if (!activeTab) {
      toast({
        title: "No file selected",
        description: "Please open a file to compile",
        variant: "destructive",
      });
      return;
    }

    // Check if file is .4gl
    if (!activeTab.path.endsWith('.4gl')) {
      toast({
        title: "Invalid file type",
        description: "Only .4gl files can be compiled",
        variant: "destructive",
      });
      return;
    }

    setIsCompiling(true);
    try {
      const response: any = await apiClient.compileCode({
        code: activeTab.content,
        target_name: activeTab.name.replace('.4gl', ''),
      });

      // Check if backend returned an error response
      if (response.status === "error") {
        toast({
          title: "Compilation error",
          description: response.message || "Compilation failed",
          variant: "destructive",
        });
        return;
      }

      // Handle successful compilation response
      if (response.success) {
        toast({
          title: "Compilation successful",
          description: `${response.target} compiled in ${response.compilation_time.toFixed(2)}s`,
        });

        if (response.warnings && response.warnings.length > 0) {
          console.log('Compilation warnings:', response.warnings);
        }
      } else {
        const errorMsg = response.errors && response.errors.length > 0
          ? response.errors.map((e: any) => `${e.file}:${e.line || '?'} - ${e.message}`).join('\n')
          : `${response.error_count || 0} error(s) found`;

        toast({
          title: "Compilation failed",
          description: errorMsg,
          variant: "destructive",
        });

        if (response.errors && response.errors.length > 0) {
          console.log('Compilation errors:', response.errors);
        }
      }
    } catch (error: any) {
      // Handle network errors or unexpected responses
      const errorMessage = error?.message || "Unknown error occurred";

      toast({
        title: "Compilation error",
        description: errorMessage,
        variant: "destructive",
      });

      console.log('Compilation error details:', error);
    } finally {
      setIsCompiling(false);
    }
  };

  const handleConvertToPython = async () => {
    const activeTab = openTabs.find(t => t.id === activeTabId);
    if (!activeTab) {
      toast({
        title: "No file selected",
        description: "Please open a file to convert",
        variant: "destructive",
      });
      return;
    }

    // Check if file is .4gl
    if (!activeTab.path.endsWith('.4gl')) {
      toast({
        title: "Invalid file type",
        description: "Only .4gl files can be converted to Python",
        variant: "destructive",
      });
      return;
    }

    setIsConverting(true);
    try {
      const response = await apiClient.convertCode({
        source: activeTab.content,
      });

      // Create new Python file path
      const pythonFileName = activeTab.name.replace('.4gl', '.py');
      const pythonFilePath = activeTab.path.replace('.4gl', '.py');
      const parentPath = pythonFilePath.substring(0, pythonFilePath.lastIndexOf('/'));

      // Step 1: Create the file using context (which refreshes file tree automatically)
      // If file already exists, skip creation
      let fileAlreadyExists = false;
      try {
        await createFile(parentPath || '/', pythonFileName);
      } catch (createError: any) {
        // Silently ignore if file already exists (409 or "already exists" message)
        const errorMsg = String(createError?.message || createError || '');
        const is409Error = errorMsg.includes('409') || errorMsg.toLowerCase().includes('already exists') || errorMsg.toLowerCase().includes('conflict');

        if (is409Error) {
          // File exists, we'll just overwrite the content below
          fileAlreadyExists = true;
          console.log(`File ${pythonFileName} already exists, will update content`);
        } else {
          // Only throw if it's a different error
          throw createError;
        }
      }

      // Step 2: Update the file content and open it
      const normalizedPath = pythonFilePath.startsWith('/') ? pythonFilePath : `/${pythonFilePath}`;

      // Save content to backend
      await apiClient.saveFileContent(normalizedPath, response.python);

      // Refresh file tree and open the new file
      await refreshFileTree();
      await openFile(normalizedPath);

      toast({
        title: "Conversion successful",
        description: `Converted to ${pythonFileName}`,
      });

      if (response.warnings && response.warnings.length > 0) {
        console.log('Conversion warnings:', response.warnings);
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Conversion failed";

      toast({
        title: "Conversion error",
        description: errorMessage,
        variant: "destructive",
      });

      console.log('Conversion error details:', error);
    } finally {
      setIsConverting(false);
    }
  };

  const handleConvertTo4GL = async () => {
    const activeTab = openTabs.find(t => t.id === activeTabId);
    if (!activeTab) {
      toast({
        title: "No file selected",
        description: "Please open a file to convert",
        variant: "destructive",
      });
      return;
    }

    // Check if file is .py
    if (!activeTab.path.endsWith('.py')) {
      toast({
        title: "Invalid file type",
        description: "Only .py files can be converted to 4GL",
        variant: "destructive",
      });
      return;
    }

    setIsConverting(true);
    try {
      const response = await apiClient.convertPythonTo4GL(activeTab.content);

      // Create new 4GL file path
      const fglFileName = activeTab.name.replace('.py', '.4gl');
      const fglFilePath = activeTab.path.replace('.py', '.4gl');
      const parentPath = fglFilePath.substring(0, fglFilePath.lastIndexOf('/'));

      // Step 1: Create the file using context (which refreshes file tree automatically)
      // If file already exists, skip creation
      let fileAlreadyExists = false;
      try {
        await createFile(parentPath || '/', fglFileName);
      } catch (createError: any) {
        // Silently ignore if file already exists (409 or "already exists" message)
        const errorMsg = String(createError?.message || createError || '');
        const is409Error = errorMsg.includes('409') || errorMsg.toLowerCase().includes('already exists') || errorMsg.toLowerCase().includes('conflict');

        if (is409Error) {
          // File exists, we'll just overwrite the content below
          fileAlreadyExists = true;
          console.log(`File ${fglFileName} already exists, will update content`);
        } else {
          // Only throw if it's a different error
          throw createError;
        }
      }

      // Step 2: Update the file content and open it
      const normalizedPath = fglFilePath.startsWith('/') ? fglFilePath : `/${fglFilePath}`;

      // Save content to backend
      await apiClient.saveFileContent(normalizedPath, response.fgl_code);

      // Refresh file tree and open the new file
      await refreshFileTree();
      await openFile(normalizedPath);

      toast({
        title: "Conversion successful",
        description: `Converted to ${fglFileName}`,
      });

      if (response.warnings && response.warnings.length > 0) {
        console.log('Conversion warnings:', response.warnings);
        toast({
          title: "Conversion warnings",
          description: response.warnings.join(', '),
          variant: "default",
        });
      }
    } catch (error: any) {
      const errorMessage = error?.message || "Conversion failed";

      toast({
        title: "Conversion error",
        description: errorMessage,
        variant: "destructive",
      });

      console.log('Conversion error details:', error);
    } finally {
      setIsConverting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      // Switch back to local mode
      await setMode("local");
      // Clear active database config
      setActiveConfig(null);
      toast({
        title: "Disconnected",
        description: "Switched back to local file system",
      });
    } catch (error: any) {
      const errorMsg = error?.message || String(error);
      toast({
        title: "Error",
        description: `Failed to disconnect: ${errorMsg}`,
        variant: "destructive",
      });
    }
  };

  // Edit menu handlers
  const handleUndo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'undo', null);
    }
  };

  const handleRedo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'redo', null);
    }
  };

  const handleCut = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'editor.action.clipboardCutAction', null);
    }
  };

  const handleCopy = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'editor.action.clipboardCopyAction', null);
    }
  };

  const handlePaste = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'editor.action.clipboardPasteAction', null);
    }
  };


  return (
    <header className="flex h-12 flex-shrink-0 items-center gap-4 border-b bg-muted/20 px-4">
      <div className="flex items-center gap-2">
        <LogoIcon className="h-6 w-6 text-primary" />
        <h1 className="text-lg font-semibold">Codecraft IDE</h1>
        {project.currentProject && (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Wand2 className="h-3 w-3" />
            {project.currentProject.name}
          </Badge>
        )}
      </div>
      <Menubar className="h-8 border-0 bg-transparent shadow-none">
        <MenubarMenu>
          <MenubarTrigger>File</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={() => setShowNewProjectDialog(true)}>
              New Project...
            </MenubarItem>
            <MenubarItem onClick={() => projectInputRef.current?.click()}>
              Open Project...
            </MenubarItem>
            <MenubarItem onClick={project.saveProject} disabled={!project.currentProject}>
              Save Project
            </MenubarItem>
            <MenubarSeparator />
            {mode === "remote" ? (
              <>
                <MenubarItem onClick={handleOpenFileClick}>
                  Open File(s) from Server...
                </MenubarItem>
                <MenubarItem onClick={() => fileInputRef.current?.click()}>
                  Import File(s) from Local...
                </MenubarItem>
                <MenubarSeparator />
                <MenubarItem onClick={handleOpenFolderClick}>
                  Browse Server Folder...
                </MenubarItem>
                <MenubarItem onClick={() => folderInputRef.current?.click()}>
                  Import Folder from Local...
                </MenubarItem>
              </>
            ) : (
              <>
                <MenubarItem onClick={handleOpenFileClick}>
                  Open File(s)...
                </MenubarItem>
                <MenubarItem onClick={handleOpenFolderClick}>
                  Open Folder...
                </MenubarItem>
              </>
            )}
            <MenubarSeparator />
            <MenubarItem onClick={handleNewFile}>
              New File
              <MenubarShortcut>⌘N</MenubarShortcut>
            </MenubarItem>
            <MenubarItem onClick={handleNewFolder}>
              New Folder
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleSave} disabled={!activeTabId}>
              Save
              <MenubarShortcut>⌘S</MenubarShortcut>
            </MenubarItem>
            <MenubarItem onClick={handleSaveAll} disabled={openTabs.length === 0}>
              Save All
              <MenubarShortcut>⌘⇧S</MenubarShortcut>
            </MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>Edit</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={handleUndo}>
              Undo
              <MenubarShortcut>⌘Z</MenubarShortcut>
            </MenubarItem>
            <MenubarItem onClick={handleRedo}>
              Redo
              <MenubarShortcut>⇧⌘Z</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleCut}>Cut</MenubarItem>
            <MenubarItem onClick={handleCopy}>Copy</MenubarItem>
            <MenubarItem onClick={handlePaste}>Paste</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>View</MenubarTrigger>
          <MenubarContent>
            <MenubarItem disabled>Appearance</MenubarItem>
            <MenubarItem disabled>Editor Layout</MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={() => setShowCommandPalette(true)}>
              Command Palette...
              <MenubarShortcut>⌘P</MenubarShortcut>
            </MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>Run</MenubarTrigger>
          <MenubarContent>
            <MenubarItem disabled>Run without Debugging</MenubarItem>
            <MenubarItem disabled>Start Debugging</MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleCompile} disabled={!activeTabId || isCompiling}>
              {isCompiling ? "Compiling..." : "Compile with 4make"}
              <MenubarShortcut>⌘B</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={handleConvertToPython} disabled={!activeTabId || isConverting || !openTabs.find(t => t.id === activeTabId)?.path.endsWith('.4gl')}>
              {isConverting ? "Converting..." : "Convert to Python"}
              <MenubarShortcut>⌘⇧P</MenubarShortcut>
            </MenubarItem>
            <MenubarItem onClick={handleConvertTo4GL} disabled={!activeTabId || isConverting || !openTabs.find(t => t.id === activeTabId)?.path.endsWith('.py')}>
              {isConverting ? "Converting..." : "Convert to 4GL"}
              <MenubarShortcut>⌘⇧F</MenubarShortcut>
            </MenubarItem>
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger className="flex items-center gap-2">
            Database
            {activeConfig && (
              <Badge variant="secondary" className="text-xs px-1 py-0">
                {activeConfig.name}
              </Badge>
            )}
          </MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={() => setShowDatabaseDialog(true)}>
              Configure Connections...
            </MenubarItem>
            {activeConfig && (
              <>
                <MenubarSeparator />
                <MenubarItem onClick={handleDisconnect}>
                  Disconnect from {activeConfig.name}
                </MenubarItem>
              </>
            )}
          </MenubarContent>
        </MenubarMenu>
        <MenubarMenu>
          <MenubarTrigger>Help</MenubarTrigger>
          <MenubarContent>
            <MenubarItem onClick={() => setShowDocumentation(true)}>
              Documentation
              <MenubarShortcut>⌘⇧H</MenubarShortcut>
            </MenubarItem>
            <MenubarSeparator />
            <MenubarItem onClick={() => setShowAboutDialog(true)}>About</MenubarItem>
          </MenubarContent>
        </MenubarMenu>
      </Menubar>

      {/* User Menu, Session Indicator, and File System Mode Indicator */}
      <div className="flex items-center gap-2 ml-auto">
        <UserMenu />
        {/* Session Indicator - shows first 8 chars of session ID */}
        {sessionId && (
          <div
            className="flex items-center gap-1 px-2 py-1 bg-violet-500/10 text-violet-500 rounded-md text-xs font-mono cursor-help"
            title={`Session ID: ${sessionId}\nEach browser tab has its own independent session`}
          >
            <span className="opacity-60">Session:</span>
            <span>{sessionId.substring(0, 8)}</span>
          </div>
        )}
        {mode === "remote" && (
          <div className="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-md">
            <Server className="h-4 w-4" />
            <span className="text-sm font-medium">Remote: {remoteConfigName}</span>
          </div>
        )}
        {mode === "local" && (
          <div className="flex items-center gap-2 px-3 py-1 bg-muted rounded-md">
            <HardDrive className="h-4 w-4" />
            <span className="text-sm font-medium">Local</span>
          </div>
        )}
      </div>

      {/* Hidden file inputs */}
      <input
        ref={projectInputRef}
        type="file"
        accept=".ccp"
        onChange={handleOpenProject}
        className="hidden"
      />
      <input
        ref={fileInputRef}
        type="file"
        accept=".4gl,.per,.sql,.def"
        multiple
        onChange={handleOpenFiles}
        className="hidden"
      />
      <input
        ref={folderInputRef}
        type="file"
        // @ts-ignore - webkitdirectory is not in TypeScript types
        webkitdirectory="true"
        directory="true"
        onChange={handleOpenFolder}
        className="hidden"
      />

      <DatabaseConfigDialog open={showDatabaseDialog} onOpenChange={setShowDatabaseDialog} />

      {/* New Project Dialog */}
      <Dialog open={showNewProjectDialog} onOpenChange={setShowNewProjectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              <div className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-purple-500" />
                New CodeCraft Project
              </div>
            </DialogTitle>
            <DialogDescription>
              Create a new .ccp (CodeCraft Project) file
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="project-name">Project Name *</Label>
              <Input
                id="project-name"
                placeholder="my-4gl-project"
                value={newProjectName}
                onChange={(e) => setNewProjectName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleNewProject();
                  }
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-description">Description (optional)</Label>
              <Textarea
                id="project-description"
                placeholder="A brief description of your project..."
                value={newProjectDescription}
                onChange={(e) => setNewProjectDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewProjectDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleNewProject}>Create Project</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* About Dialog */}
      <Dialog open={showAboutDialog} onOpenChange={setShowAboutDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LogoIcon className="h-6 w-6 text-primary" />
              About Codecraft IDE
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <p className="text-sm text-muted-foreground mb-4">
                A modern IDE for Informix 4GL development with support for Querix forms,
                database integration, and project management.
              </p>
            </div>
            <div className="border-t pt-4">
              <h4 className="font-semibold text-sm mb-2">Created & Developed By</h4>
              <div className="space-y-1">
                <p className="text-sm font-medium">Wanderson Freitas Batista</p>
                <a
                  href="https://www.wbatista.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                >
                  www.wbatista.com
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                  </svg>
                </a>
              </div>
            </div>
            <div className="border-t pt-4">
              <p className="text-xs text-muted-foreground">
                © {new Date().getFullYear()} Wanderson Freitas Batista. All rights reserved.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowAboutDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remote File Browser */}
      {mode === "remote" && remoteConfigName && remoteConfig && (
        <>
          <RemoteFileBrowser
            open={showRemoteFileBrowser}
            onOpenChange={setShowRemoteFileBrowser}
            configName={remoteConfigName}
            configData={remoteConfig}
            initialPath="~"
            mode="file"
            multiSelect={true}
            onSelect={handleRemoteFilesSelect}
          />
          <RemoteFileBrowser
            open={showRemoteFolderBrowser}
            onOpenChange={setShowRemoteFolderBrowser}
            configName={remoteConfigName}
            configData={remoteConfig}
            initialPath="~"
            mode="both"
            multiSelect={false}
            onSelect={handleRemoteFolderSelect}
          />
        </>
      )}

      {/* Command Palette */}
      <CommandPalette open={showCommandPalette} onOpenChange={setShowCommandPalette} />

      {/* Documentation Dialog */}
      <DocumentationDialog open={showDocumentation} onOpenChange={setShowDocumentation} />
    </header>
  );
}
