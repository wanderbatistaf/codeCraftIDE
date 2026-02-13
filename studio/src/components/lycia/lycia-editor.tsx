"use client";

import * as React from "react";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Eye,
  EyeOff,
  Grid3X3,
  ZoomIn,
  ZoomOut,
  RefreshCw,
  Loader2,
  AlertCircle,
  FileCode,
  Maximize2,
  Minimize2,
  Palette,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { LyciaFormData, LyciaComponent } from "@/lib/api-client";
import { LyciaFormPreview, LyciaComponentInfo } from "./lycia-form-preview";
import { useToast } from "@/hooks/use-toast";
import { useFileSystem } from "@/contexts/file-system-context";

interface LyciaEditorProps {
  content: string;
  cssContent?: string;
  onContentChange?: (content: string) => void;
  fileName?: string;
}

export function LyciaEditor({
  content,
  cssContent: initialCssContent,
  onContentChange,
  fileName,
}: LyciaEditorProps) {
  const { toast } = useToast();
  const { openFile, openTabs, mode, remoteConfigName, remoteConfig } = useFileSystem();
  const [formData, setFormData] = useState<LyciaFormData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(true);
  const [showGrid, setShowGrid] = useState(false);
  const [scale, setScale] = useState(1);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [previewFullscreen, setPreviewFullscreen] = useState(false);
  const [cssContent, setCssContent] = useState<string>(initialCssContent || "");
  const [showShell, setShowShell] = useState(false);
  const [showCssDialog, setShowCssDialog] = useState(false);
  const [cssPath, setCssPath] = useState<string>("");
  const [showHtmlDialog, setShowHtmlDialog] = useState(false);
  const [htmlSnapshot, setHtmlSnapshot] = useState("");
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Try to auto-load CSS file if it exists with same name
  useEffect(() => {
    if (fileName && !cssContent) {
      const cssFileName = fileName.replace(/\.fm2$/i, ".css");
      // Check if CSS file is already open
      const cssTab = openTabs.find(tab => tab.name === cssFileName);
      if (cssTab) {
        setCssContent(cssTab.content);
      }
    }
  }, [fileName, openTabs, cssContent]);

  // Parse the FM2 content
  const parseContent = useCallback(async (fm2Content: string) => {
    if (!fm2Content.trim()) {
      setFormData(null);
      setError(null);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.parseFM2(fm2Content);

      if (response.status === "error") {
        setError(response.error || "Failed to parse form");
        setFormData(null);
      } else {
        setFormData(response.form || null);
        setError(null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to parse form";
      setError(errorMessage);
      setFormData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Parse content with debounce when content changes
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      parseContent(content);
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [content, parseContent]);

  // Find component by identifier
  const findComponent = useCallback(
    (identifier: string, component?: LyciaComponent): LyciaComponent | null => {
      if (!component) {
        component = formData?.rootContainer || undefined;
      }
      if (!component) return null;

      if (component.identifier === identifier) {
        return component;
      }

      if (component.children) {
        for (const child of component.children) {
          const found = findComponent(identifier, child);
          if (found) return found;
        }
      }

      return null;
    },
    [formData]
  );

  const selectedComponentData = selectedComponent
    ? findComponent(selectedComponent)
    : null;

  const handleZoomIn = () => {
    setScale((prev) => Math.min(prev + 0.25, 3));
  };

  const handleZoomOut = () => {
    setScale((prev) => Math.max(prev - 0.25, 0.5));
  };

  const handleRefresh = () => {
    parseContent(content);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-2 py-1 border-b bg-muted/30">
        <div className="flex items-center gap-1">
          <FileCode className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">
            {fileName || "Lycia Form Editor"}
          </span>
        </div>

        <div className="flex items-center gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant={showPreview ? "default" : "ghost"}
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setShowPreview(!showPreview)}
                >
                  {showPreview ? (
                    <Eye className="h-4 w-4" />
                  ) : (
                    <EyeOff className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {showPreview ? "Hide Preview" : "Show Preview"}
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {showPreview && (
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={showGrid ? "default" : "ghost"}
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setShowGrid(!showGrid)}
                    >
                      <Grid3X3 className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Toggle Grid</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <div className="flex items-center border rounded">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomOut}
                  disabled={scale <= 0.5}
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-xs w-12 text-center">
                  {Math.round(scale * 100)}%
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleZoomIn}
                  disabled={scale >= 3}
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={handleRefresh}
                      disabled={isLoading}
                    >
                      <RefreshCw
                        className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
                      />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Refresh Preview</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={cssContent ? "default" : "ghost"}
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setShowCssDialog(true)}
                    >
                      <Palette className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {cssContent ? "CSS Loaded - Click to change" : "Load CSS Stylesheet"}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant={showShell ? "default" : "ghost"}
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setShowShell((prev) => !prev)}
                    >
                      Shell
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {showShell ? "Hide App Shell" : "Show App Shell"}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setShowHtmlDialog(true)}
                    >
                      HTML
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>View Rendered HTML</TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => setPreviewFullscreen(!previewFullscreen)}
                    >
                      {previewFullscreen ? (
                        <Minimize2 className="h-4 w-4" />
                      ) : (
                        <Maximize2 className="h-4 w-4" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {previewFullscreen ? "Exit Fullscreen" : "Fullscreen Preview"}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 min-h-0">
        {showPreview ? (
          <ResizablePanelGroup direction="horizontal">
            {/* Code editor panel - hidden in fullscreen */}
            {!previewFullscreen && (
              <>
                <ResizablePanel defaultSize={50} minSize={20}>
                  <div className="h-full flex flex-col bg-muted/10">
                    <div className="px-2 py-1 text-xs text-muted-foreground border-b">
                      XML Source (Editable)
                    </div>
                    <textarea
                      className="flex-1 w-full p-2 text-xs font-mono bg-transparent resize-none focus:outline-none"
                      value={content}
                      onChange={(e) => onContentChange?.(e.target.value)}
                      spellCheck={false}
                    />
                  </div>
                </ResizablePanel>
                <ResizableHandle withHandle />
              </>
            )}

            {/* Preview panel */}
            <ResizablePanel defaultSize={previewFullscreen ? 100 : 50} minSize={30}>
              <ResizablePanelGroup direction="horizontal">
                <ResizablePanel defaultSize={75} minSize={50}>
                  <div className="h-full flex flex-col">
                    <div className="px-2 py-1 text-xs text-muted-foreground border-b flex items-center justify-between">
                      <span>Visual Preview</span>
                      {isLoading && (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      )}
                    </div>

                    {error ? (
                      <div className="flex-1 flex items-center justify-center p-4">
                        <div className="text-center">
                          <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
                          <p className="text-sm text-destructive">{error}</p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex-1 overflow-auto">
                        <LyciaFormPreview
                          formData={formData}
                          cssContent={cssContent}
                          scale={scale}
                          showGrid={showGrid}
                          showShell={showShell}
                          captureHtml={showHtmlDialog}
                          onHtmlCapture={setHtmlSnapshot}
                          selectedComponent={selectedComponent}
                          onSelectComponent={setSelectedComponent}
                        />
                      </div>
                    )}
                  </div>
                </ResizablePanel>

                <ResizableHandle withHandle />

                {/* Component info panel */}
                <ResizablePanel defaultSize={25} minSize={15}>
                  <div className="h-full flex flex-col border-l">
                    <div className="px-2 py-1 text-xs text-muted-foreground border-b">
                      Properties
                    </div>
                    <ScrollArea className="flex-1">
                      <LyciaComponentInfo component={selectedComponentData} />
                    </ScrollArea>
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          // Code-only view
          <ScrollArea className="h-full">
            <pre className="p-4 text-xs font-mono whitespace-pre-wrap">
              {content}
            </pre>
          </ScrollArea>
        )}
      </div>

      {/* Status bar */}
      <div className="flex items-center justify-between px-2 py-1 border-t text-xs text-muted-foreground bg-muted/30">
        <div className="flex items-center gap-4">
          {formData && (
            <>
              <span>Database: {formData.database || "None"}</span>
              <span>
                Size: {formData.width} x {formData.height} chars
              </span>
            </>
          )}
          {cssContent && (
            <span className="text-purple-500">CSS Active</span>
          )}
        </div>
        <div>
          {selectedComponent && (
            <span>Selected: {selectedComponent}</span>
          )}
        </div>
      </div>

      {/* CSS Dialog */}
      <Dialog open={showCssDialog} onOpenChange={setShowCssDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Load CSS Stylesheet</DialogTitle>
            <DialogDescription>
              Enter the path to a CSS file or paste CSS content directly.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">CSS File Path</label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., form.css"
                  value={cssPath}
                  onChange={(e) => setCssPath(e.target.value)}
                />
                <Button
                  variant="outline"
                  onClick={async () => {
                    // Try to load CSS from open tabs
                    const cssTab = openTabs.find(tab => tab.name === cssPath || tab.path.endsWith(cssPath));
                    if (cssTab) {
                      setCssContent(cssTab.content);
                      toast({
                        title: "CSS Loaded",
                        description: `Loaded ${cssTab.name}`,
                      });
                      setShowCssDialog(false);
                    } else {
                      // Try to open the CSS file
                      const basePath = fileName?.replace(/[^/\\]*$/, '') || '';
                      const fullPath = cssPath.includes('/') || cssPath.includes('\\')
                        ? cssPath
                        : basePath + cssPath;

                      try {
                        await openFile(fullPath);
                        // Wait a bit for the file to load
                        setTimeout(() => {
                          const newTab = openTabs.find(tab => tab.path === fullPath || tab.name === cssPath);
                          if (newTab) {
                            setCssContent(newTab.content);
                            toast({
                              title: "CSS Loaded",
                              description: `Loaded ${cssPath}`,
                            });
                            setShowCssDialog(false);
                          }
                        }, 500);
                      } catch (err) {
                        toast({
                          title: "Error",
                          description: `Could not load ${cssPath}`,
                          variant: "destructive",
                        });
                      }
                    }
                  }}
                >
                  Load
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Open CSS files will be detected automatically
              </p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Or Paste CSS Content</label>
              <textarea
                className="w-full h-40 p-2 text-xs font-mono border rounded bg-muted/30"
                placeholder="/* Paste CSS here */"
                value={cssContent}
                onChange={(e) => setCssContent(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setCssContent("");
              setCssPath("");
            }}>
              Clear CSS
            </Button>
            <Button onClick={() => setShowCssDialog(false)}>
              Apply
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Rendered HTML Dialog */}
      <Dialog open={showHtmlDialog} onOpenChange={setShowHtmlDialog}>
        <DialogContent className="max-w-[90vw] w-[90vw] h-[80vh] max-h-[80vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Rendered HTML</DialogTitle>
            <DialogDescription>
              Snapshot of the current preview markup.
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 min-h-0">
            <textarea
              className="w-full h-full p-2 text-xs font-mono border rounded bg-muted/30"
              value={htmlSnapshot}
              readOnly
            />
          </div>
          <DialogFooter>
            <Button onClick={() => setShowHtmlDialog(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Fullscreen Preview Modal */}
      <Dialog open={previewFullscreen} onOpenChange={setPreviewFullscreen}>
        <DialogContent className="max-w-[95vw] w-[95vw] h-[90vh] max-h-[90vh] flex flex-col">
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center justify-between">
              <span>Preview: {fileName || "Lycia Form"}</span>
              <div className="flex items-center gap-2">
                <Button
                  variant={showGrid ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowGrid(!showGrid)}
                >
                  <Grid3X3 className="h-4 w-4 mr-1" />
                  Grid
                </Button>
                <div className="flex items-center border rounded">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleZoomOut}
                    disabled={scale <= 0.5}
                  >
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <span className="text-xs w-12 text-center">
                    {Math.round(scale * 100)}%
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleZoomIn}
                    disabled={scale >= 3}
                  >
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-auto border rounded bg-muted/20">
            {error ? (
              <div className="flex items-center justify-center h-full p-4">
                <div className="text-center">
                  <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
                  <p className="text-sm text-destructive">{error}</p>
                </div>
              </div>
            ) : (
              <LyciaFormPreview
                formData={formData}
                cssContent={cssContent}
                scale={scale}
                showGrid={showGrid}
                showShell={showShell}
                captureHtml={showHtmlDialog}
                onHtmlCapture={setHtmlSnapshot}
                selectedComponent={selectedComponent}
                onSelectComponent={setSelectedComponent}
              />
            )}
          </div>

          {/* Selected component info in modal */}
          {selectedComponent && (
            <div className="flex-shrink-0 border-t pt-2 mt-2">
              <div className="text-xs text-muted-foreground">
                <strong>Selected:</strong> {selectedComponent}
                {selectedComponentData && (
                  <span className="ml-4">
                    Type: {selectedComponentData.type} |
                    Position: ({selectedComponentData.x}, {selectedComponentData.y}) |
                    Size: {selectedComponentData.width}x{selectedComponentData.height}
                  </span>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
