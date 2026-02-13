"use client";

import * as React from "react";
import { useState, useRef } from "react";
import {
  Search,
  X,
  Loader2,
  FileText,
  ChevronRight,
  ChevronDown,
  CaseSensitive,
  Regex,
  FileSearch,
  FileCode,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/hooks/use-toast";
import { useFileSystem } from "@/contexts/file-system-context";
import { useEditor } from "@/contexts/editor-context";

interface SearchMatch {
  line: number;
  column: number;
  text: string;
}

interface SearchResult {
  file: string;
  matches: SearchMatch[];
}

interface FileSearchModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function FileSearchModal({ open, onOpenChange }: FileSearchModalProps) {
  const { toast } = useToast();
  const { openFile, mode, remoteConfigName, remoteConfig } = useFileSystem();
  const { goToLine } = useEditor();
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [caseSensitive, setCaseSensitive] = useState<boolean>(false);
  const [useRegex, setUseRegex] = useState<boolean>(false);
  const [searchInContent, setSearchInContent] = useState<boolean>(true); // true = search content, false = search file names only
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [fileNameResults, setFileNameResults] = useState<string[]>([]); // For file name search results
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleCancelSearch = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsSearching(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast({
        title: "Empty query",
        description: "Please enter a search term",
        variant: "destructive",
      });
      return;
    }

    // Cancel any existing search
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsSearching(true);
    setResults([]);
    setFileNameResults([]);
    setExpandedFiles(new Set());

    try {
      // Search by file name only (local filtering of file tree)
      if (!searchInContent) {
        // Get the file tree and filter by name
        const response = mode === "remote" && remoteConfigName && remoteConfig
          ? await apiClient.getSFTPTree(remoteConfigName, remoteConfig)
          : await apiClient.getFileTree();

        // Recursive function to find all files matching the search query
        const findMatchingFiles = (node: any, matchingFiles: string[] = []): string[] => {
          const query = caseSensitive ? searchQuery : searchQuery.toLowerCase();
          const nodeName = caseSensitive ? node.name : node.name.toLowerCase();

          if (nodeName.includes(query)) {
            matchingFiles.push(node.path);
          }

          if (node.children) {
            node.children.forEach((child: any) => findMatchingFiles(child, matchingFiles));
          }

          return matchingFiles;
        };

        const matchingFiles = findMatchingFiles(response.tree);
        setFileNameResults(matchingFiles);

        if (matchingFiles.length === 0) {
          toast({
            title: "No results",
            description: `No files found matching "${searchQuery}"`,
          });
        }
      } else {
        // Search in file content
        let response;

        // Check if we're in remote mode and use appropriate search
        if (mode === "remote" && remoteConfigName && remoteConfig) {
          response = await apiClient.searchSFTPFiles(
            remoteConfigName,
            remoteConfig,
            searchQuery,
            caseSensitive,
            useRegex
          );
        } else {
          response = await apiClient.searchFiles(searchQuery, caseSensitive, useRegex);
        }

        if (response.status === "error") {
          throw new Error(response.error || "Search failed");
        }

        // Group matches by line (remove duplicate lines)
        const processedResults = (response.results || []).map(result => {
          // Group matches by line number, keeping only unique lines
          const lineMap = new Map<number, SearchMatch>();

          result.matches.forEach(match => {
            if (!lineMap.has(match.line)) {
              lineMap.set(match.line, match);
            }
          });

          return {
            ...result,
            matches: Array.from(lineMap.values()).sort((a, b) => a.line - b.line)
          };
        });

        setResults(processedResults);

        // Auto-expand all files
        const allFiles = new Set(processedResults.map((r) => r.file));
        setExpandedFiles(allFiles);

        if (response.results.length === 0) {
          toast({
            title: "No results",
            description: `No matches found for "${searchQuery}"`,
          });
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Search failed";
      toast({
        title: "Search Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const toggleFile = (fileName: string) => {
    setExpandedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(fileName)) {
        next.delete(fileName);
      } else {
        next.add(fileName);
      }
      return next;
    });
  };

  const handleMatchClick = async (fileName: string, line: number) => {
    try {
      await openFile(fileName);

      // Use setTimeout to ensure the editor is ready before navigating
      setTimeout(() => {
        goToLine(line);
      }, 100);

      onOpenChange(false);

      toast({
        title: "File opened",
        description: `Jumped to line ${line} in ${fileName}`,
      });
    } catch (err) {
      toast({
        title: "Error",
        description: `Failed to open ${fileName}`,
        variant: "destructive",
      });
    }
  };

  const getTotalMatches = () => {
    return results.reduce((total, result) => total + result.matches.length, 0);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col gap-4">
        <DialogHeader>
          <DialogTitle>Search Files</DialogTitle>
          <DialogDescription>
            Search for text across all files in the workspace
          </DialogDescription>
        </DialogHeader>

        {/* Search Input */}
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search for..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-8"
                autoFocus
              />
            </div>
            {isSearching ? (
              <Button onClick={handleCancelSearch} variant="destructive">
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            ) : (
              <Button onClick={handleSearch}>
                <Search className="h-4 w-4 mr-2" />
                Search
              </Button>
            )}
          </div>

          {/* Search Options */}
          <div className="flex gap-2 flex-wrap">
            <Button
              variant={searchInContent ? "default" : "outline"}
              size="sm"
              onClick={() => setSearchInContent(true)}
            >
              <FileCode className="h-3 w-3 mr-1" />
              Search Content
            </Button>
            <Button
              variant={!searchInContent ? "default" : "outline"}
              size="sm"
              onClick={() => setSearchInContent(false)}
            >
              <FileSearch className="h-3 w-3 mr-1" />
              Search File Names
            </Button>
            <div className="border-l mx-1" />
            <Button
              variant={caseSensitive ? "default" : "outline"}
              size="sm"
              onClick={() => setCaseSensitive(!caseSensitive)}
            >
              <CaseSensitive className="h-3 w-3 mr-1" />
              Case Sensitive
            </Button>
            {searchInContent && (
              <Button
                variant={useRegex ? "default" : "outline"}
                size="sm"
                onClick={() => setUseRegex(!useRegex)}
              >
                <Regex className="h-3 w-3 mr-1" />
                Use Regex
              </Button>
            )}
          </div>
        </div>

        {/* Results Summary */}
        {searchInContent && results.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Found {getTotalMatches()} {getTotalMatches() === 1 ? 'match' : 'matches'} in {results.length} {results.length === 1 ? 'file' : 'files'}
          </div>
        )}
        {!searchInContent && fileNameResults.length > 0 && (
          <div className="text-sm text-muted-foreground">
            Found {fileNameResults.length} {fileNameResults.length === 1 ? 'file' : 'files'} matching "{searchQuery}"
          </div>
        )}

        {/* Results List */}
        <div className="flex-1 min-h-0 border rounded-md overflow-hidden">
          <ScrollArea className="h-full">
            <div className="p-2">
          {isSearching && (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {!isSearching && results.length === 0 && fileNameResults.length === 0 && searchQuery && (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Search className="h-12 w-12 mb-2 opacity-50" />
              <p className="text-sm">No results found</p>
              <p className="text-xs mt-1">Try a different search term</p>
            </div>
          )}

          {!isSearching && results.length === 0 && fileNameResults.length === 0 && !searchQuery && (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Search className="h-12 w-12 mb-2 opacity-50" />
              <p className="text-sm">Enter a search term to get started</p>
            </div>
          )}

          {/* File Name Search Results */}
          {!isSearching && !searchInContent && fileNameResults.length > 0 && (
            <div className="space-y-1">
              {fileNameResults.map((filePath) => (
                <div
                  key={filePath}
                  onClick={async () => {
                    try {
                      await openFile(filePath);
                      onOpenChange(false);
                    } catch (err) {
                      toast({
                        title: "Error",
                        description: `Failed to open file`,
                        variant: "destructive",
                      });
                    }
                  }}
                  className="flex items-center gap-2 p-2 hover:bg-accent cursor-pointer rounded-md"
                >
                  <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                  <span className="text-sm truncate">{filePath}</span>
                </div>
              ))}
            </div>
          )}

          {/* Content Search Results */}
          {!isSearching && searchInContent && results.length > 0 && (
            <div className="space-y-2">
              {results.map((result) => {
                const isExpanded = expandedFiles.has(result.file);

                return (
                  <Collapsible
                    key={result.file}
                    open={isExpanded}
                    onOpenChange={() => toggleFile(result.file)}
                  >
                    <div className="rounded-md border">
                      <CollapsibleTrigger className="flex items-center gap-2 p-2 w-full hover:bg-accent">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 flex-shrink-0" />
                        ) : (
                          <ChevronRight className="h-4 w-4 flex-shrink-0" />
                        )}
                        <FileText className="h-4 w-4 text-primary flex-shrink-0" />
                        <span className="text-sm font-medium flex-1 text-left truncate">
                          {result.file}
                        </span>
                        <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                          {result.matches.length} {result.matches.length === 1 ? 'match' : 'matches'}
                        </span>
                      </CollapsibleTrigger>

                      <CollapsibleContent>
                        <div className="border-t">
                          {result.matches.map((match, idx) => (
                            <div
                              key={`${result.file}-${match.line}-${match.column}-${idx}`}
                              onClick={() => handleMatchClick(result.file, match.line)}
                              className="flex items-start gap-2 p-2 hover:bg-accent cursor-pointer text-xs font-mono border-b last:border-b-0"
                            >
                              <span className="text-muted-foreground min-w-[3rem] text-right">
                                {match.line}
                              </span>
                              <span className="flex-1 whitespace-pre-wrap break-all">
                                {match.text}
                              </span>
                            </div>
                          ))}
                        </div>
                      </CollapsibleContent>
                    </div>
                  </Collapsible>
                );
              })}
            </div>
          )}
            </div>
          </ScrollArea>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
