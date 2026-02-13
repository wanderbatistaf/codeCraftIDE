"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import * as VisuallyHidden from "@radix-ui/react-visually-hidden";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Book,
  FileText,
  Loader2,
  Layout,
  FolderOpen,
  Search,
  Code2,
  Play,
  Hammer,
  ArrowRightLeft,
  Stethoscope,
  Database,
  Server,
  FormInput,
  Save,
  Keyboard,
  HelpCircle,
  ChevronRight,
  MessageCircleQuestion,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DocFile {
  filename: string;
  number: string;
  title: string;
  displayTitle: string;
}

interface DocumentationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Map doc numbers to icons
const docIcons: Record<string, React.ReactNode> = {
  "00": <MessageCircleQuestion className="h-4 w-4" />, // FAQ
  "01": <Book className="h-4 w-4" />,                  // Overview
  "02": <Layout className="h-4 w-4" />,                // Interface
  "03": <FolderOpen className="h-4 w-4" />,            // Files and Projects
  "04": <Search className="h-4 w-4" />,                // Search
  "05": <Code2 className="h-4 w-4" />,                 // Editor
  "06": <Play className="h-4 w-4" />,                  // 4GL Interpretation
  "07": <Hammer className="h-4 w-4" />,                // 4make Compilation
  "08": <ArrowRightLeft className="h-4 w-4" />,        // Conversion
  "09": <Stethoscope className="h-4 w-4" />,           // Diagnostics
  "10": <Database className="h-4 w-4" />,              // Database
  "11": <Server className="h-4 w-4" />,                // Remote SFTP
  "12": <FormInput className="h-4 w-4" />,             // Forms
  "13": <Save className="h-4 w-4" />,                  // Session
  "14": <Keyboard className="h-4 w-4" />,              // Shortcuts
  "15": <HelpCircle className="h-4 w-4" />,            // Troubleshooting
};

// Enhanced markdown to HTML converter
function renderMarkdown(markdown: string): string {
  let html = markdown
    // Remove BOM if present
    .replace(/^\uFEFF/, '')
    // Remove first H1 since it's shown in the header
    .replace(/^# .*\n\n?/, '');

  // Process code blocks FIRST (before inline code) to avoid conflicts
  html = html.replace(/```(\w*)\n([\s\S]*?)```/gim, '<pre class="bg-zinc-950 dark:bg-zinc-900 text-zinc-100 p-4 rounded-lg overflow-x-auto my-4 border border-border"><code class="text-sm font-mono leading-relaxed">$2</code></pre>');

  // Process inline code - use a more specific regex
  html = html.replace(/`([^`\n]+)`/g, '<code class="px-1.5 py-0.5 bg-primary/10 text-primary rounded text-sm font-mono border border-primary/20">$1</code>');

  html = html
    // Headers with better styling
    .replace(/^### (.*$)/gim, '<h3 class="text-base font-semibold text-foreground mt-6 mb-3 flex items-center gap-2"><span class="w-1 h-4 bg-primary/50 rounded-full"></span>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-lg font-semibold text-foreground mt-8 mb-4 pb-2 border-b border-border">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-foreground mb-6">$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold text-foreground">$1</strong>')
    // Italic (but not inside code tags)
    .replace(/(?<!<code[^>]*>.*)\*([^*]+)\*(?![^<]*<\/code>)/gim, '<em class="italic">$1</em>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors">$1</a>')
    // Unordered lists with custom bullets
    .replace(/^\s*[-*]\s+(.*)$/gim, '<li class="flex items-start gap-2 my-1"><span class="text-primary mt-2">•</span><span>$1</span></li>')
    // Ordered lists
    .replace(/^\s*(\d+)\.\s+(.*)$/gim, '<li class="flex items-start gap-2 my-1"><span class="text-primary font-medium min-w-[1.5rem]">$1.</span><span>$2</span></li>')
    // Q&A styling
    .replace(/^Q:\s*(.*)$/gim, '<div class="mt-4 mb-1"><span class="inline-flex items-center gap-1.5 text-sm font-medium text-primary"><span class="w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center text-xs">Q</span>$1</span></div>')
    .replace(/^A:\s*(.*)$/gim, '<div class="mb-4 pl-6 text-muted-foreground">$1</div>')
    // Blockquotes with accent
    .replace(/^>\s+(.*)$/gim, '<blockquote class="border-l-4 border-primary/50 bg-primary/5 pl-4 py-2 pr-4 my-4 rounded-r-lg italic text-muted-foreground">$1</blockquote>')
    // Horizontal rules
    .replace(/^---$/gim, '<hr class="my-6 border-border">')
    // Line breaks
    .replace(/\n\n/gim, '</p><p class="my-3 text-muted-foreground leading-relaxed">')
    // Single newlines in lists context
    .replace(/<\/li>\n<li/gim, '</li><li');

  // Wrap lists with better styling
  html = html.replace(/(<li class="flex items-start gap-2 my-1">.*?<\/li>)+/gis, (match) => {
    if (match.includes('min-w-[1.5rem]')) {
      return `<ol class="my-4 space-y-1">${match}</ol>`;
    }
    return `<ul class="my-4 space-y-1">${match}</ul>`;
  });

  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<')) {
    html = `<p class="my-3 text-muted-foreground leading-relaxed">${html}</p>`;
  }

  return html;
}

export function DocumentationDialog({ open, onOpenChange }: DocumentationDialogProps) {
  const [language, setLanguage] = useState<string>("en-us");
  const [languages, setLanguages] = useState<string[]>([]);
  const [files, setFiles] = useState<DocFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);

  // Load available languages
  useEffect(() => {
    if (open) {
      fetch("/api/docs")
        .then(res => res.json())
        .then(data => {
          if (data.languages) {
            setLanguages(data.languages);
            // Auto-detect browser language
            const browserLang = navigator.language.toLowerCase();
            if (browserLang.startsWith('pt') && data.languages.includes('pt-br')) {
              setLanguage('pt-br');
            } else if (data.languages.includes('en-us')) {
              setLanguage('en-us');
            }
          }
        })
        .catch(console.error);
    }
  }, [open]);

  // Load files for selected language
  useEffect(() => {
    if (open && language) {
      setLoading(true);
      setSelectedFile(null); // Reset selection when language changes
      setContent(""); // Clear content
      fetch(`/api/docs?lang=${language}`)
        .then(res => res.json())
        .then(data => {
          if (data.files) {
            setFiles(data.files);
            // Select first file by default
            if (data.files.length > 0) {
              setSelectedFile(data.files[0].filename);
            }
          }
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [open, language]);

  // Load content for selected file
  useEffect(() => {
    // Only load if file exists in current files list (prevents 404 on language switch)
    const fileExists = files.some(f => f.filename === selectedFile);
    if (open && language && selectedFile && fileExists) {
      setLoadingContent(true);
      fetch(`/api/docs?lang=${language}&file=${encodeURIComponent(selectedFile)}`)
        .then(res => res.json())
        .then(data => {
          if (data.content) {
            setContent(data.content);
          }
        })
        .catch(console.error)
        .finally(() => setLoadingContent(false));
    }
  }, [open, language, selectedFile, files]);

  const languageLabels: Record<string, { label: string; flag: string }> = {
    "en-us": { label: "English", flag: "🇺🇸" },
    "pt-br": { label: "Português", flag: "🇧🇷" },
  };

  const selectedFileData = files.find(f => f.filename === selectedFile);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl h-[85vh] flex flex-col p-0 gap-0 overflow-hidden" hideCloseButton>
        <VisuallyHidden.Root>
          <DialogTitle>Documentation</DialogTitle>
        </VisuallyHidden.Root>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-primary/5 to-transparent flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Book className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Documentation</h2>
              <p className="text-xs text-muted-foreground">Codecraft IDE User Guide</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Language Selector */}
            <div className="flex items-center gap-1 bg-muted/50 rounded-lg p-1">
              {languages.map(lang => (
                <Button
                  key={lang}
                  variant={language === lang ? "default" : "ghost"}
                  size="sm"
                  className={cn(
                    "h-8 px-3 gap-1.5",
                    language === lang && "shadow-sm"
                  )}
                  onClick={() => setLanguage(lang)}
                >
                  <span>{languageLabels[lang]?.flag}</span>
                  <span className="text-xs">{languageLabels[lang]?.label || lang}</span>
                </Button>
              ))}
            </div>
            {/* Close Button */}
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full hover:bg-destructive/10 hover:text-destructive"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-72 border-r bg-muted/20 flex-shrink-0 flex flex-col">
            <div className="p-3 border-b">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <FileText className="h-3.5 w-3.5" />
                <span>{files.length} topics</span>
              </div>
            </div>
            <ScrollArea className="flex-1">
              <div className="p-2">
                {loading ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-3">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    <span className="text-xs text-muted-foreground">Loading topics...</span>
                  </div>
                ) : (
                  <nav className="space-y-0.5">
                    {files.map(file => {
                      const isSelected = selectedFile === file.filename;
                      const icon = docIcons[file.number] || <FileText className="h-4 w-4" />;
                      return (
                        <button
                          key={file.filename}
                          className={cn(
                            "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-150",
                            "hover:bg-accent/50 group",
                            isSelected && "bg-primary/10 text-primary hover:bg-primary/15"
                          )}
                          onClick={() => setSelectedFile(file.filename)}
                        >
                          <span className={cn(
                            "flex-shrink-0 p-1.5 rounded-md transition-colors",
                            isSelected ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground group-hover:bg-accent"
                          )}>
                            {icon}
                          </span>
                          <span className={cn(
                            "flex-1 text-sm truncate",
                            isSelected ? "font-medium" : "text-muted-foreground group-hover:text-foreground"
                          )}>
                            {file.title}
                          </span>
                          {isSelected && (
                            <ChevronRight className="h-4 w-4 text-primary flex-shrink-0" />
                          )}
                        </button>
                      );
                    })}
                  </nav>
                )}
              </div>
            </ScrollArea>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden flex flex-col bg-background">
            {/* Content Header */}
            {selectedFileData && (
              <div className="px-8 py-4 border-b bg-muted/10 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <span className="p-2 bg-primary/10 rounded-lg">
                    {docIcons[selectedFileData.number] || <FileText className="h-5 w-5" />}
                  </span>
                  <div>
                    <Badge variant="secondary" className="mb-1 text-[10px]">
                      Section {selectedFileData.number}
                    </Badge>
                    <h3 className="font-semibold">{selectedFileData.title}</h3>
                  </div>
                </div>
              </div>
            )}

            <ScrollArea className="flex-1">
              <div className="px-8 py-6 max-w-3xl">
                {loadingContent ? (
                  <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="relative">
                      <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl animate-pulse" />
                      <Loader2 className="h-10 w-10 animate-spin text-primary relative" />
                    </div>
                    <span className="text-sm text-muted-foreground">Loading content...</span>
                  </div>
                ) : content ? (
                  <article
                    className="documentation-content"
                    dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center py-20 text-center">
                    <div className="p-4 bg-muted/50 rounded-full mb-4">
                      <Book className="h-10 w-10 text-muted-foreground/50" />
                    </div>
                    <h4 className="font-medium mb-1">Select a Topic</h4>
                    <p className="text-sm text-muted-foreground">Choose a topic from the sidebar to get started</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
