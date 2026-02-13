'use client';

import { useEffect, useState, useRef } from 'react';
import dynamic from 'next/dynamic';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from '@/components/ui/button';
import { X, Save, Circle, Play, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useFileSystem } from '@/contexts/file-system-context';
import { useEditor } from '@/contexts/editor-context';
import { useExecution } from '@/contexts/execution-context';

// Dynamically import Monaco editor to avoid SSR issues
const FGLMonacoEditor = dynamic(
  () => import('@/components/monaco-editor').then(mod => ({ default: mod.FGLMonacoEditor })),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-full">Loading editor...</div> }
);

// Dynamically import Form Preview
const FormPreview = dynamic(
  () => import('@/components/form-preview').then(mod => ({ default: mod.FormPreview })),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-full">Loading preview...</div> }
);

// Dynamically import Lycia Editor for .fm2 files
const LyciaEditor = dynamic(
  () => import('@/components/lycia').then(mod => ({ default: mod.LyciaEditor })),
  { ssr: false, loading: () => <div className="flex items-center justify-center h-full">Loading Lycia editor...</div> }
);

export function EditorArea() {
  const { toast } = useToast();
  const {
    openTabs,
    activeTabId,
    setActiveTab,
    closeTab,
    updateFileContent,
    saveFile,
    saveAllFiles,
  } = useFileSystem();
  const { executeCode, isExecuting } = useExecution();
  const { editorRef, monacoRef } = useEditor();

  // Register editor instance when it mounts
  const handleEditorReady = (editor: any, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  const [localContent, setLocalContent] = useState<{ [key: string]: string }>({});

  // Sync local content with tabs
  useEffect(() => {
    const newContent: { [key: string]: string } = {};
    openTabs.forEach(tab => {
      if (!(tab.id in localContent)) {
        newContent[tab.id] = tab.content;
      } else {
        newContent[tab.id] = localContent[tab.id];
      }
    });
    setLocalContent(newContent);
  }, [openTabs.length]); // Only sync when tabs are added/removed

  const handleContentChange = (tabId: string, content: string) => {
    setLocalContent(prev => ({ ...prev, [tabId]: content }));
    const tab = openTabs.find(t => t.id === tabId);
    if (tab) {
      updateFileContent(tab.path, content);
    }
  };

  const handleSave = async (tabId: string) => {
    const tab = openTabs.find(t => t.id === tabId);
    if (tab) {
      try {
        await saveFile(tab.path);
        toast({
          title: "Saved",
          description: `${tab.name} has been saved.`,
        });
      } catch (error) {
        toast({
          title: "Error",
          description: `Failed to save ${tab.name}`,
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

  const handleRun = async () => {
    if (!activeTabId) return;

    const activeTab = openTabs.find(t => t.id === activeTabId);
    if (!activeTab) return;

    // Check if file is a 4GL file
    if (!activeTab.path.endsWith('.4gl')) {
      toast({
        title: "Cannot Execute",
        description: "Only .4gl files can be executed. Python files cannot be run in the 4GL interpreter.",
        variant: "destructive",
      });
      return;
    }

    try {
      const code = localContent[activeTabId] ?? activeTab.content;
      await executeCode(code);
      toast({
        title: "Execution Complete",
        description: "Check the console for output.",
      });
    } catch (error) {
      toast({
        title: "Execution Failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  };

  const handleCloseTab = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    const tab = openTabs.find(t => t.id === tabId);
    if (tab?.isDirty) {
      const confirmed = confirm(`${tab.name} has unsaved changes. Close anyway?`);
      if (!confirmed) return;
    }
    closeTab(tabId);
  };

  const handleKeyDown = (e: React.KeyboardEvent, tabId: string) => {
    // Ctrl+S or Cmd+S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave(tabId);
    }
  };

  if (openTabs.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center bg-[hsl(var(--background))] text-muted-foreground">
        <p className="text-lg">No file open</p>
        <p className="text-sm mt-2">Open a file from the explorer to start editing</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden bg-[hsl(var(--background))]">
      <Tabs value={activeTabId || undefined} onValueChange={setActiveTab} className="flex h-full flex-col">
        <div className="flex items-center border-b bg-muted/30">
          <TabsList className="flex-1 justify-start rounded-none border-0 bg-transparent p-0 h-10 overflow-x-auto">
            {openTabs.map(tab => (
              <TabsTrigger
                key={tab.id}
                value={tab.id}
                className="h-10 rounded-none border-r data-[state=active]:bg-background data-[state=active]:shadow-none relative group pr-8"
              >
                <div className="flex items-center gap-2">
                  {tab.isDirty && <Circle className="h-2 w-2 fill-current" />}
                  <span className="max-w-[120px] truncate">{tab.name}</span>
                </div>
                <div
                  role="button"
                  onClick={(e) => handleCloseTab(e, tab.id)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 hover:bg-accent rounded p-0.5 transition-opacity cursor-pointer"
                  title="Close"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      handleCloseTab(e as any, tab.id);
                    }
                  }}
                >
                  <X className="h-3 w-3" />
                </div>
              </TabsTrigger>
            ))}
          </TabsList>
          <div className="flex items-center gap-2 px-2">
            <Button
              variant="default"
              size="sm"
              onClick={handleRun}
              disabled={isExecuting || !activeTabId || !openTabs.find(t => t.id === activeTabId)?.path.endsWith('.4gl')}
              title={openTabs.find(t => t.id === activeTabId)?.path.endsWith('.4gl') ? "Run Code (F5)" : "Only .4gl files can be executed"}
              className="h-8 bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isExecuting ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-1" />
              )}
              Run
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSaveAll}
              disabled={!openTabs.some(t => t.isDirty)}
              title="Save All (Ctrl+Shift+S)"
              className="h-8"
            >
              <Save className="h-4 w-4 mr-1" />
              Save All
            </Button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          {openTabs.map(tab => {
            const isPerFile = tab.name.endsWith('.per');
            const isFm2File = tab.name.endsWith('.fm2');
            const isPythonFile = tab.name.endsWith('.py');
            const is4GLFile = tab.name.endsWith('.4gl');
            const isCssFile = tab.name.endsWith('.css');

            // Determine language and diagnostics settings based on file type
            const language = isPerFile ? 'per' : isPythonFile ? 'python' : isFm2File ? 'xml' : isCssFile ? 'css' : 'fgl';
            const enableDiagnostics = is4GLFile || isPerFile; // Only enable for 4GL and .per files

            return (
              <TabsContent
                key={tab.id}
                value={tab.id}
                className="h-full m-0 p-0 data-[state=active]:flex data-[state=active]:flex-col"
              >
                <div className="flex-1 overflow-hidden flex">
                  {isFm2File ? (
                    /* Lycia editor for .fm2 files */
                    <div className="flex-1 overflow-hidden">
                      <LyciaEditor
                        content={localContent[tab.id] ?? tab.content}
                        onContentChange={(value) => handleContentChange(tab.id, value)}
                        fileName={tab.name}
                      />
                    </div>
                  ) : isPerFile ? (
                    <>
                      {/* Split view for .per files */}
                      <div className="flex-1 border-r overflow-hidden">
                        <FGLMonacoEditor
                          value={localContent[tab.id] ?? tab.content}
                          onChange={(value) => handleContentChange(tab.id, value)}
                          onKeyDown={(e) => handleKeyDown(e, tab.id)}
                          language="per"
                          enableDiagnostics={true}
                          onEditorReady={handleEditorReady}
                        />
                      </div>
                      <div className="flex-1 overflow-auto">
                        <FormPreview content={localContent[tab.id] ?? tab.content} />
                      </div>
                    </>
                  ) : (
                    /* Normal editor for .4gl, .py, and other files */
                    <div className="flex-1 overflow-hidden">
                      <FGLMonacoEditor
                        value={localContent[tab.id] ?? tab.content}
                        onChange={(value) => handleContentChange(tab.id, value)}
                        onKeyDown={(e) => handleKeyDown(e, tab.id)}
                        language={language}
                        onEditorReady={handleEditorReady}
                        enableDiagnostics={enableDiagnostics}
                      />
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between border-t px-4 py-1 text-xs text-muted-foreground bg-muted/20">
                  <div className="flex items-center gap-4">
                    <span>{tab.path}</span>
                    {tab.isDirty && <span className="text-amber-500">● Modified</span>}
                    {isPerFile && <span className="text-blue-500">● Form File</span>}
                    {isFm2File && <span className="text-purple-500">● Lycia Form</span>}
                  </div>
                  <div className="flex items-center gap-4">
                    <span>{localContent[tab.id]?.split('\n').length || 1} lines</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSave(tab.id)}
                      disabled={!tab.isDirty}
                      className="h-6 px-2"
                    >
                      <Save className="h-3 w-3 mr-1" />
                      Save
                    </Button>
                  </div>
                </div>
              </TabsContent>
            );
          })}
        </div>
      </Tabs>
    </div>
  );
}
