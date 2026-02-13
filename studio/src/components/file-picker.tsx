'use client';

import { useRef } from 'react';
import { Button } from '@/components/ui/button';
import { FileUp, FolderUp } from 'lucide-react';

interface FilePickerProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
}

export function FilePicker({ onFilesSelected, accept = '*', multiple = true }: FilePickerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onFilesSelected(files);
    }
    // Reset input to allow selecting the same file again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileChange}
        className="hidden"
      />
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        title="Open File(s)"
        className="h-8"
      >
        <FileUp className="h-4 w-4 mr-1" />
        Open File
      </Button>
    </>
  );
}

interface FolderPickerProps {
  onFolderSelected: (files: File[]) => void;
}

export function FolderPicker({ onFolderSelected }: FolderPickerProps) {
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleClick = async () => {
    // Try to use modern File System Access API if available
    if ('showDirectoryPicker' in window) {
      try {
        const dirHandle = await (window as any).showDirectoryPicker();
        const files = await readDirectoryRecursive(dirHandle);
        onFolderSelected(files);
      } catch (err) {
        // User cancelled or error occurred
        console.log('Directory picker cancelled or error:', err);
      }
    } else {
      // Fallback to traditional file input with webkitdirectory
      folderInputRef.current?.click();
    }
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      onFolderSelected(files);
    }
    // Reset input
    if (folderInputRef.current) {
      folderInputRef.current.value = '';
    }
  };

  return (
    <>
      <input
        ref={folderInputRef}
        type="file"
        // @ts-ignore - webkitdirectory is not in TypeScript types
        webkitdirectory="true"
        directory="true"
        onChange={handleFolderChange}
        className="hidden"
      />
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        title="Open Folder"
        className="h-8"
      >
        <FolderUp className="h-4 w-4 mr-1" />
        Open Folder
      </Button>
    </>
  );
}

/**
 * Recursively read all files from a directory handle (File System Access API)
 */
async function readDirectoryRecursive(dirHandle: any, basePath = ''): Promise<File[]> {
  const files: File[] = [];

  for await (const entry of dirHandle.values()) {
    const path = basePath ? `${basePath}/${entry.name}` : entry.name;

    if (entry.kind === 'file') {
      const file = await entry.getFile();
      // Add path property to file for directory structure
      Object.defineProperty(file, 'webkitRelativePath', {
        value: path,
        writable: false,
      });
      files.push(file);
    } else if (entry.kind === 'directory') {
      const subFiles = await readDirectoryRecursive(entry, path);
      files.push(...subFiles);
    }
  }

  return files;
}
