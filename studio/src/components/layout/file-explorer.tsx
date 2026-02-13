"use client";
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Folder,
  FolderOpen,
  File as FileIcon,
  ChevronRight,
  ChevronDown,
  FilePlus2,
  FolderPlus,
  RefreshCw,
  PanelLeftClose,
  Trash2,
  Edit2,
  Download,
  Search,
} from 'lucide-react';
import { type FileTreeNode } from '@/lib/file-tree';
import { API_BASE_URL } from '@/lib/api-client';
import { useFileSystem } from '@/contexts/file-system-context';
import { useDatabase } from '@/contexts/database-context';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { useToast } from '@/hooks/use-toast';
import { DatabaseExplorer } from '@/components/database-explorer';
import { FileSearchModal } from '@/components/file-search-modal';

// Helper to flatten visible nodes for range selection
function flattenVisibleNodes(nodes: FileTreeNode[], expandedFolders: Set<string>): FileTreeNode[] {
  const result: FileTreeNode[] = [];
  for (const node of nodes) {
    result.push(node);
    if (node.type === 'folder' && expandedFolders.has(node.id) && node.children) {
      result.push(...flattenVisibleNodes(node.children, expandedFolders));
    }
  }
  return result;
}

interface FileTreeItemProps {
  node: FileTreeNode;
  level: number;
  selectedNodeIds: Set<string>;
  lastSelectedNodeId: string | null;
  onSelectNode: (nodeId: string, event: React.MouseEvent) => void;
  visibleNodes: FileTreeNode[];
}

const FileTreeItem = ({ node, level, selectedNodeIds, lastSelectedNodeId, onSelectNode, visibleNodes }: FileTreeItemProps) => {
  const {
    openFile,
    expandedFolders,
    toggleFolder,
    deleteNode,
    renameNode,
    createFile,
    createFolder,
  } = useFileSystem();
  const { toast } = useToast();
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameName, setRenameName] = useState(node.name);

  const isFolder = node.type === 'folder';
  const isOpen = expandedFolders.has(node.id);
  const isSelected = selectedNodeIds.has(node.id);

  const handleClick = (e: React.MouseEvent) => {
    // Single click: toggle folder or select file
    if (isFolder && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
      toggleFolder(node.id);
    }
    onSelectNode(node.id, e);
  };

  const handleDoubleClick = async () => {
    // Double click: open file or toggle folder
    if (isFolder) {
      toggleFolder(node.id);
    } else {
      try {
        await openFile(node.path);
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to open ${node.name}`,
          variant: "destructive",
        });
      }
    }
  };

  const handleDelete = async () => {
    try {
      await deleteNode(node.id);
      toast({
        title: "Deleted",
        description: `${node.name} has been deleted.`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to delete ${node.name}`,
        variant: "destructive",
      });
    }
  };

  const handleRename = () => {
    setIsRenaming(true);
  };

  const handleRenameSubmit = async () => {
    if (renameName && renameName !== node.name) {
      try {
        await renameNode(node.id, renameName);
        toast({
          title: "Renamed",
          description: `Renamed to ${renameName}`,
        });
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to rename ${node.name}`,
          variant: "destructive",
        });
      }
    }
    setIsRenaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRenameSubmit();
    } else if (e.key === 'Escape') {
      setIsRenaming(false);
      setRenameName(node.name);
    }
  };

  const handleDownload = async () => {
    if (isFolder) return; // Only download files, not folders

    try {
      // Fetch file content from the API
      const response = await fetch(`${API_BASE_URL}/api/files/content?path=${encodeURIComponent(node.path)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Failed to fetch file content');
      }

      // Create blob and download
      const blob = new Blob([data.content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = node.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Downloaded",
        description: `${node.name} has been downloaded.`,
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to download ${node.name}`,
        variant: "destructive",
      });
    }
  };

  return (
    <div>
      <ContextMenu>
        <ContextMenuTrigger>
          <div
            onClick={handleClick}
            onDoubleClick={handleDoubleClick}
            className={`flex cursor-pointer items-center rounded-md py-1 px-2 text-sm hover:bg-accent ${isSelected ? 'bg-accent/80 ring-1 ring-accent' : ''}`}
            style={{ paddingLeft: `${level * 16 + 4}px` }}
          >
            {isFolder ? (
              <>
                {isOpen ? <ChevronDown className="mr-1 h-4 w-4 flex-shrink-0" /> : <ChevronRight className="mr-1 h-4 w-4 flex-shrink-0" />}
                {isOpen ? <FolderOpen className="mr-2 h-4 w-4 text-primary flex-shrink-0" /> : <Folder className="mr-2 h-4 w-4 text-primary flex-shrink-0" />}
              </>
            ) : (
              <FileIcon className="mr-2 h-4 w-4 flex-shrink-0" style={{ marginLeft: '20px' }} />
            )}
            {isRenaming ? (
              <Input
                value={renameName}
                onChange={(e) => setRenameName(e.target.value)}
                onBlur={handleRenameSubmit}
                onKeyDown={handleKeyDown}
                className="h-6 py-0 px-1 text-sm"
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <span className="truncate" title={node.path}>{node.name}</span>
            )}
          </div>
        </ContextMenuTrigger>
        <ContextMenuContent>
          {isFolder && (
            <>
              <ContextMenuItem onClick={async () => {
                const fileName = prompt("Enter file name:");
                if (fileName) {
                  try {
                    await createFile(node.path, fileName);
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
              }}>
                <FilePlus2 className="mr-2 h-4 w-4" />
                New File
              </ContextMenuItem>
              <ContextMenuItem onClick={async () => {
                const folderName = prompt("Enter folder name:");
                if (folderName) {
                  try {
                    await createFolder(node.path, folderName);
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
              }}>
                <FolderPlus className="mr-2 h-4 w-4" />
                New Folder
              </ContextMenuItem>
            </>
          )}
          {!isFolder && (
            <ContextMenuItem onClick={handleDownload}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </ContextMenuItem>
          )}
          <ContextMenuItem onClick={handleRename}>
            <Edit2 className="mr-2 h-4 w-4" />
            Rename
          </ContextMenuItem>
          {node.id !== 'root' && (
            <ContextMenuItem onClick={handleDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </ContextMenuItem>
          )}
        </ContextMenuContent>
      </ContextMenu>
      {isOpen && isFolder && node.children && (
        <div>
          {node.children.map((childNode) => (
            <FileTreeItem
              key={childNode.id}
              node={childNode}
              level={level + 1}
              selectedNodeIds={selectedNodeIds}
              lastSelectedNodeId={lastSelectedNodeId}
              onSelectNode={onSelectNode}
              visibleNodes={visibleNodes}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export function FileExplorer() {
  const { fileTree, createFile, createFolder, refreshFileTree, deleteNode, expandedFolders } = useFileSystem();
  const { activeConfig } = useDatabase();
  const { toast } = useToast();
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [selectedNodeIds, setSelectedNodeIds] = useState<Set<string>>(new Set());
  const [lastSelectedNodeId, setLastSelectedNodeId] = useState<string | null>(null);

  // Get flattened list of visible nodes for range selection
  const visibleNodes = useMemo(() => {
    return flattenVisibleNodes(fileTree.children || [], expandedFolders);
  }, [fileTree.children, expandedFolders]);

  // Handle node selection with Shift/Ctrl modifiers
  const handleSelectNode = useCallback((nodeId: string, event: React.MouseEvent) => {
    if (event.shiftKey && lastSelectedNodeId) {
      // Shift+Click: select range
      const startIndex = visibleNodes.findIndex(n => n.id === lastSelectedNodeId);
      const endIndex = visibleNodes.findIndex(n => n.id === nodeId);

      if (startIndex !== -1 && endIndex !== -1) {
        const start = Math.min(startIndex, endIndex);
        const end = Math.max(startIndex, endIndex);
        const rangeNodes = visibleNodes.slice(start, end + 1);

        setSelectedNodeIds(prev => {
          const newSet = new Set(prev);
          rangeNodes.forEach(n => newSet.add(n.id));
          return newSet;
        });
      }
    } else if (event.ctrlKey || event.metaKey) {
      // Ctrl/Cmd+Click: toggle selection
      setSelectedNodeIds(prev => {
        const newSet = new Set(prev);
        if (newSet.has(nodeId)) {
          newSet.delete(nodeId);
        } else {
          newSet.add(nodeId);
        }
        return newSet;
      });
      setLastSelectedNodeId(nodeId);
    } else {
      // Regular click: select only this node
      setSelectedNodeIds(new Set([nodeId]));
      setLastSelectedNodeId(nodeId);
    }
  }, [lastSelectedNodeId, visibleNodes]);

  // Handle Delete key press
  const handleKeyDown = useCallback(async (e: KeyboardEvent) => {
    if (e.key === 'Delete' && selectedNodeIds.size > 0) {
      const nodesToDelete = visibleNodes.filter(n => selectedNodeIds.has(n.id) && n.id !== 'root');

      if (nodesToDelete.length === 0) return;

      const confirmMessage = nodesToDelete.length === 1
        ? `Delete "${nodesToDelete[0].name}"?`
        : `Delete ${nodesToDelete.length} items?`;

      if (confirm(confirmMessage)) {
        let deletedCount = 0;
        for (const node of nodesToDelete) {
          try {
            await deleteNode(node.id);
            deletedCount++;
          } catch (error) {
            toast({
              title: "Error",
              description: `Failed to delete ${node.name}`,
              variant: "destructive",
            });
          }
        }
        if (deletedCount > 0) {
          toast({
            title: "Deleted",
            description: `${deletedCount} item(s) deleted.`,
          });
          setSelectedNodeIds(new Set());
        }
      }
    }
  }, [selectedNodeIds, visibleNodes, deleteNode, toast]);

  // Register keyboard listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Handle bulk delete from context menu
  const handleBulkDelete = async () => {
    const nodesToDelete = visibleNodes.filter(n => selectedNodeIds.has(n.id) && n.id !== 'root');

    if (nodesToDelete.length === 0) return;

    let deletedCount = 0;
    for (const node of nodesToDelete) {
      try {
        await deleteNode(node.id);
        deletedCount++;
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to delete ${node.name}`,
          variant: "destructive",
        });
      }
    }
    if (deletedCount > 0) {
      toast({
        title: "Deleted",
        description: `${deletedCount} item(s) deleted.`,
      });
      setSelectedNodeIds(new Set());
    }
  };

  const handleNewFile = async () => {
    const fileName = prompt("Enter file name:");
    if (fileName) {
      try {
        await createFile("/", fileName);
        toast({
          title: "Created",
          description: `File ${fileName} created in root.`,
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
          description: `Folder ${folderName} created in root.`,
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

  const handleRefresh = async () => {
    try {
      await refreshFileTree();
      toast({
        title: "Refreshed",
        description: "File tree refreshed.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to refresh`,
        variant: "destructive",
      });
    }
  };

  return (
    <aside className="hidden w-64 flex-shrink-0 border-r bg-muted/20 md:flex">
      <ResizablePanelGroup orientation="vertical" className="h-full w-full">
        {/* File Explorer Panel */}
        <ResizablePanel defaultSize={60} minSize={30}>
          <div className="flex h-full flex-col">
            <div className="flex h-10 items-center justify-between border-b px-3">
              <h2 className="text-sm font-semibold uppercase">Explorer</h2>
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSearchModalOpen(true)} title="Search Files">
                  <Search className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNewFile} title="New File">
                  <FilePlus2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleNewFolder} title="New Folder">
                  <FolderPlus className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleRefresh} title="Refresh">
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <ScrollArea className="flex-1 p-2">
              {fileTree.children?.map((node) => (
                <FileTreeItem
                  key={node.id}
                  node={node}
                  level={0}
                  selectedNodeIds={selectedNodeIds}
                  lastSelectedNodeId={lastSelectedNodeId}
                  onSelectNode={handleSelectNode}
                  visibleNodes={visibleNodes}
                />
              ))}
            </ScrollArea>
            {selectedNodeIds.size > 1 && (
              <div className="flex items-center justify-between border-t px-3 py-1.5 text-xs text-muted-foreground">
                <span>{selectedNodeIds.size} items selected</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-xs text-destructive hover:text-destructive"
                  onClick={handleBulkDelete}
                >
                  <Trash2 className="mr-1 h-3 w-3" />
                  Delete
                </Button>
              </div>
            )}
          </div>
        </ResizablePanel>

        {/* Resizable Handle */}
        <ResizableHandle withHandle />

        {/* Database Explorer Panel */}
        <ResizablePanel defaultSize={40} minSize={20}>
          <DatabaseExplorer
            configName={activeConfig?.name || null}
            databaseName={activeConfig?.database}
          />
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* File Search Modal */}
      <FileSearchModal open={searchModalOpen} onOpenChange={setSearchModalOpen} />
    </aside>
  );
}
