"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Folder, File, ChevronUp, Home, CheckSquare, Square } from "lucide-react";
import { apiClient, type DatabaseConfig } from "@/lib/api-client";

interface RemoteFileBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  configName: string;
  configData: DatabaseConfig;
  initialPath: string;
  mode: "file" | "folder" | "both";
  multiSelect?: boolean;
  onSelect: (selections: string[]) => void;
}

interface FileItem {
  name: string;
  path: string;
  type: string;
  size?: number;
}

export function RemoteFileBrowser({
  open,
  onOpenChange,
  configName,
  configData,
  initialPath,
  mode,
  multiSelect = false,
  onSelect,
}: RemoteFileBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [items, setItems] = useState<FileItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadItems = async (path: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.listSFTPDirectoryAbsolute(
        configName,
        configData,
        path || "~"
      );

      // Filter items based on mode
      let filteredItems = response.items;
      if (mode === "folder") {
        // In folder mode, show only folders
        filteredItems = filteredItems.filter(item => item.type === "folder");
      }
      // In file mode or both mode, show everything (need folders for navigation)

      setItems(filteredItems);
      setCurrentPath(response.current_path);
    } catch (err: any) {
      console.error("Failed to load directory:", err);
      setError(err?.message || "Failed to load directory");
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load initial path when dialog opens
  useEffect(() => {
    if (open) {
      loadItems(initialPath);
      setSelectedItems(new Set());
    }
  }, [open, initialPath]);

  const handleGoUp = () => {
    // Go to parent directory
    if (!currentPath || currentPath === "/" || currentPath === "~") {
      // Already at root or home
      return;
    }

    const parts = currentPath.split("/").filter(Boolean);
    parts.pop();
    const parentPath = parts.length > 0 ? "/" + parts.join("/") : "/";
    loadItems(parentPath);
  };

  const handleGoHome = () => {
    loadItems("~");
  };

  const handleItemClick = (item: FileItem) => {
    if (item.type === "folder") {
      // Navigate into folder (single click)
      loadItems(item.path);
    } else {
      // Toggle file selection (only files can be selected in file mode)
      if (mode === "file" || mode === "both") {
        if (multiSelect) {
          const newSelected = new Set(selectedItems);
          if (newSelected.has(item.path)) {
            newSelected.delete(item.path);
          } else {
            newSelected.add(item.path);
          }
          setSelectedItems(newSelected);
        } else {
          setSelectedItems(new Set([item.path]));
        }
      }
    }
  };

  const handleItemDoubleClick = (item: FileItem) => {
    if (item.type === "folder") {
      loadItems(item.path);
    }
  };

  const handleToggleItem = (item: FileItem, event: React.MouseEvent) => {
    event.stopPropagation();
    const newSelected = new Set(selectedItems);
    if (newSelected.has(item.path)) {
      newSelected.delete(item.path);
    } else {
      newSelected.add(item.path);
    }
    setSelectedItems(newSelected);
  };

  const handleSelect = () => {
    const selections = Array.from(selectedItems);

    // If selecting folders (or both) and nothing selected, select current directory
    if ((mode === "folder" || mode === "both") && selections.length === 0) {
      onSelect([currentPath]);
    } else {
      onSelect(selections);
    }

    onOpenChange(false);
  };

  const getItemIcon = (item: FileItem) => {
    if (item.type === "folder") {
      return <Folder className="h-5 w-5 text-primary" />;
    }
    return <File className="h-5 w-5 text-muted-foreground" />;
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>
            {mode === "file" && "Select Remote File(s)"}
            {mode === "folder" && "Select Remote Folder"}
            {mode === "both" && "Select Remote Files/Folders"}
          </DialogTitle>
          <DialogDescription>
            Browse and select {mode === "file" ? "files" : mode === "folder" ? "a folder" : "files or folders"} from the SSH server.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Navigation Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handleGoUp}
              disabled={isLoading || !currentPath || currentPath === "/" || currentPath === "~"}
              title="Go to parent directory"
            >
              <ChevronUp className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleGoHome}
              disabled={isLoading}
              title="Go to home directory"
            >
              <Home className="h-4 w-4" />
            </Button>
            <div className="flex-1 px-3 py-2 bg-muted rounded-md font-mono text-sm">
              {currentPath || "~"}
            </div>
          </div>

          {/* Selection Info */}
          {multiSelect && selectedItems.size > 0 && (
            <div className="px-3 py-2 bg-primary/10 text-primary rounded-md text-sm">
              {selectedItems.size} item(s) selected
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
              {error}
            </div>
          )}

          {/* Items List */}
          <ScrollArea className="h-[400px] border rounded-md">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : items.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Folder className="h-12 w-12 mb-4 opacity-50" />
                <p>No {mode === "file" ? "files" : mode === "folder" ? "folders" : "items"} found</p>
                {mode === "folder" && (
                  <p className="text-sm mt-1">You can select this directory</p>
                )}
              </div>
            ) : (
              <div className="p-2">
                {items.map((item) => (
                  <div
                    key={item.path}
                    className={`flex items-center gap-3 p-3 rounded-md hover:bg-accent cursor-pointer transition-colors ${
                      selectedItems.has(item.path) ? "bg-accent" : ""
                    }`}
                    onClick={() => handleItemClick(item)}
                    onDoubleClick={() => handleItemDoubleClick(item)}
                  >
                    {multiSelect && item.type === "file" && (
                      <button
                        onClick={(e) => handleToggleItem(item, e)}
                        className="flex-shrink-0"
                      >
                        {selectedItems.has(item.path) ? (
                          <CheckSquare className="h-5 w-5 text-primary" />
                        ) : (
                          <Square className="h-5 w-5 text-muted-foreground" />
                        )}
                      </button>
                    )}
                    {getItemIcon(item)}
                    <span className="flex-1 font-medium">{item.name}</span>
                    {item.type === "file" && item.size !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        {formatFileSize(item.size)}
                      </span>
                    )}
                    {item.type === "folder" && (
                      <span className="text-xs text-muted-foreground">
                        {mode === "folder" && multiSelect ? "Click to select" : "Click to navigate"}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSelect}
            disabled={isLoading || (mode === "file" && selectedItems.size === 0)}
          >
            {mode === "folder"
              ? "Select This Directory"
              : mode === "both"
                ? (selectedItems.size > 0 ? `Select (${selectedItems.size})` : "Select This Directory")
                : `Select ${selectedItems.size > 0 ? `(${selectedItems.size})` : ""}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
