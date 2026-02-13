"use client";

import * as React from "react";
import { useEffect, useState } from "react";
import { File, FolderOpen, Play, Save, X } from "lucide-react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { useFileSystem, type FileTreeNode } from "@/contexts/file-system-context";
import { useToast } from "@/hooks/use-toast";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const { fileTree, openFile, saveAllFiles, openTabs } = useFileSystem();
  const { toast } = useToast();
  const [files, setFiles] = useState<Array<{ path: string; name: string }>>([]);

  // Flatten file tree to get all files
  useEffect(() => {
    const flattenTree = (node: FileTreeNode, parentPath: string = ""): Array<{ path: string; name: string }> => {
      const result: Array<{ path: string; name: string }> = [];

      if (node.type === "file") {
        result.push({
          path: node.path,
          name: node.name,
        });
      } else if (node.type === "folder" && node.children) {
        for (const child of node.children) {
          result.push(...flattenTree(child, node.path));
        }
      }

      return result;
    };

    if (fileTree.children) {
      const allFiles: Array<{ path: string; name: string }> = [];
      for (const child of fileTree.children) {
        allFiles.push(...flattenTree(child));
      }
      setFiles(allFiles);
    }
  }, [fileTree]);

  const handleOpenFile = async (path: string) => {
    try {
      await openFile(path);
      onOpenChange(false);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to open file",
        variant: "destructive",
      });
    }
  };

  const handleSaveAll = async () => {
    try {
      await saveAllFiles();
      onOpenChange(false);
      toast({
        title: "Saved All",
        description: "All files have been saved",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save files",
        variant: "destructive",
      });
    }
  };

  const handleCloseAllTabs = () => {
    // Close all tabs logic would go here
    onOpenChange(false);
    toast({
      title: "Info",
      description: "Close all tabs feature coming soon",
    });
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search files..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>

        <CommandGroup heading="Commands">
          <CommandItem onSelect={handleSaveAll}>
            <Save className="mr-2 h-4 w-4" />
            <span>Save All Files</span>
          </CommandItem>
          <CommandItem onSelect={handleCloseAllTabs}>
            <X className="mr-2 h-4 w-4" />
            <span>Close All Tabs</span>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Recent Files">
          {openTabs.slice(0, 5).map((tab) => (
            <CommandItem key={tab.id} onSelect={() => handleOpenFile(tab.path)}>
              <File className="mr-2 h-4 w-4" />
              <span>{tab.name}</span>
              {tab.isDirty && <span className="ml-2 text-xs text-muted-foreground">●</span>}
            </CommandItem>
          ))}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Files">
          {files.map((file) => (
            <CommandItem key={file.path} onSelect={() => handleOpenFile(file.path)}>
              <File className="mr-2 h-4 w-4" />
              <span>{file.name}</span>
              <span className="ml-2 text-xs text-muted-foreground">{file.path}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
