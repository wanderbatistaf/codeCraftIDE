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
import { Loader2, Folder, ChevronUp, Home } from "lucide-react";
import { apiClient, type DatabaseConfig } from "@/lib/api-client";

interface RemoteDirectoryBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  configName: string;
  configData: DatabaseConfig;
  initialPath: string;
  onSelect: (path: string) => void;
}

interface FolderItem {
  name: string;
  path: string;
}

export function RemoteDirectoryBrowser({
  open,
  onOpenChange,
  configName,
  configData,
  initialPath,
  onSelect,
}: RemoteDirectoryBrowserProps) {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadFolders = async (path: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.browseSFTPDirectories(
        configName,
        configData,
        path
      );
      setFolders(response.folders);
      setCurrentPath(path);
    } catch (err: any) {
      console.error("Failed to load directories:", err);
      setError(err?.message || "Failed to load directories");
      setFolders([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Load initial path when dialog opens
  useEffect(() => {
    if (open) {
      loadFolders(initialPath);
    }
  }, [open, initialPath]);

  const handleGoUp = () => {
    // Go to parent directory
    const parts = currentPath.split("/").filter(Boolean);
    parts.pop();
    const parentPath = parts.length > 0 ? "/" + parts.join("/") : "/";
    loadFolders(parentPath);
  };

  const handleGoHome = () => {
    loadFolders("~");
  };

  const handleFolderDoubleClick = (folder: FolderItem) => {
    loadFolders(folder.path);
  };

  const handleSelect = () => {
    onSelect(currentPath);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Select Remote Workspace Directory</DialogTitle>
          <DialogDescription>
            Browse directories on the SSH server to select your workspace location.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Navigation Controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={handleGoUp}
              disabled={isLoading || currentPath === "/"}
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
              {currentPath}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
              {error}
            </div>
          )}

          {/* Folder List */}
          <ScrollArea className="h-[400px] border rounded-md">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : folders.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Folder className="h-12 w-12 mb-4 opacity-50" />
                <p>No subdirectories found</p>
                <p className="text-sm mt-1">You can select this directory</p>
              </div>
            ) : (
              <div className="p-2">
                {folders.map((folder) => (
                  <div
                    key={folder.path}
                    className="flex items-center gap-3 p-3 rounded-md hover:bg-accent cursor-pointer transition-colors"
                    onDoubleClick={() => handleFolderDoubleClick(folder)}
                  >
                    <Folder className="h-5 w-5 text-primary" />
                    <span className="flex-1 font-medium">{folder.name}</span>
                    <span className="text-xs text-muted-foreground">
                      Double-click to open
                    </span>
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
          <Button onClick={handleSelect} disabled={isLoading}>
            Select This Directory
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
