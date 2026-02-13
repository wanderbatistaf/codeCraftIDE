'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { FileUp, FolderUp, FileDown, FilePlus, Menu, Wand2 } from 'lucide-react';
import { FilePicker, FolderPicker } from './file-picker';
import { useToast } from '@/hooks/use-toast';

interface ProjectToolbarProps {
  onOpenFiles?: (files: File[]) => void;
  onOpenFolder?: (files: File[]) => void;
  onNewProject?: (name: string, description: string) => void;
  onOpenProject?: (file: File) => void;
  onSaveProject?: () => void;
  projectName?: string;
}

export function ProjectToolbar({
  onOpenFiles,
  onOpenFolder,
  onNewProject,
  onOpenProject,
  onSaveProject,
  projectName,
}: ProjectToolbarProps) {
  const { toast } = useToast();
  const [showNewProjectDialog, setShowNewProjectDialog] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDescription, setNewProjectDescription] = useState('');

  const handleNewProject = () => {
    if (!newProjectName.trim()) {
      toast({
        title: 'Error',
        description: 'Project name is required',
        variant: 'destructive',
      });
      return;
    }

    onNewProject?.(newProjectName, newProjectDescription);
    setShowNewProjectDialog(false);
    setNewProjectName('');
    setNewProjectDescription('');

    toast({
      title: 'Project Created',
      description: `New project "${newProjectName}" created successfully`,
    });
  };

  const handleOpenProjectFile = (files: File[]) => {
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.ccp')) {
        onOpenProject?.(file);
      } else {
        toast({
          title: 'Invalid File',
          description: 'Please select a .ccp (CodeCraft Project) project file',
          variant: 'destructive',
        });
      }
    }
  };

  return (
    <>
      <div className="flex items-center gap-2 border-b bg-muted/30 px-4 py-2">
        {/* File Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8">
              <Menu className="h-4 w-4 mr-1" />
              File
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start">
            <DropdownMenuItem onClick={() => setShowNewProjectDialog(true)}>
              <FilePlus className="h-4 w-4 mr-2" />
              New Project
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <div className="cursor-pointer">
                <FilePicker
                  onFilesSelected={handleOpenProjectFile}
                  accept=".ccp"
                  multiple={false}
                />
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={onSaveProject} disabled={!projectName}>
              <FileDown className="h-4 w-4 mr-2" />
              Save Project (.ccp)
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <div className="cursor-pointer">
                <FilePicker
                  onFilesSelected={onOpenFiles || (() => {})}
                  accept=".4gl,.per,.sql,.def"
                  multiple={true}
                />
              </div>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <div className="cursor-pointer">
                <FolderPicker onFolderSelected={onOpenFolder || (() => {})} />
              </div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Project Name Display */}
        {projectName && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground ml-4">
            <Wand2 className="h-4 w-4 text-purple-500" />
            <span className="font-semibold text-foreground">{projectName}</span>
          </div>
        )}
      </div>

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
    </>
  );
}
