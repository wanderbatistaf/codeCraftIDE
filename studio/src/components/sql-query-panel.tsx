"use client";

import { useState, useEffect } from "react";
import { Play, Loader2, Copy, Download, Plus, X, Code2, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useToast } from "@/hooks/use-toast";
import { useDatabase } from "@/contexts/database-context";
import { API_BASE_URL } from "@/lib/api-client";

interface QueryResult {
  status: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time?: number;
  error?: string;
}

interface SQLTab {
  id: string;
  name: string;
  query: string;
  result: QueryResult | null;
  isExecuting: boolean;
  viewMode: "editor" | "results";
}

export function SQLQueryPanel() {
  const { toast } = useToast();
  const { activeConfig } = useDatabase();

  // Load tabs from sessionStorage on mount (per-tab isolation)
  const [tabs, setTabs] = useState<SQLTab[]>(() => {
    if (typeof window !== "undefined") {
      const saved = sessionStorage.getItem("sql-query-tabs");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          // Ensure viewMode exists on all tabs
          return parsed.map((tab: any) => ({
            ...tab,
            viewMode: tab.viewMode || "editor",
          }));
        } catch (e) {
          console.error("Failed to parse saved SQL tabs:", e);
        }
      }
    }
    return [
      {
        id: "tab-1",
        name: "Query 1",
        query: "",
        result: null,
        isExecuting: false,
        viewMode: "editor",
      },
    ];
  });

  const [activeTabId, setActiveTabId] = useState<string>(() => {
    if (typeof window !== "undefined") {
      const saved = sessionStorage.getItem("sql-active-tab");
      if (saved) {
        return saved;
      }
    }
    return "tab-1";
  });

  // Save tabs to sessionStorage whenever they change (per-tab isolation)
  useEffect(() => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("sql-query-tabs", JSON.stringify(tabs));
    }
  }, [tabs]);

  // Save active tab to sessionStorage whenever it changes (per-tab isolation)
  useEffect(() => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("sql-active-tab", activeTabId);
    }
  }, [activeTabId]);

  // Get current tab
  const currentTab = tabs.find((tab) => tab.id === activeTabId) || tabs[0];
  const currentTabIndex = tabs.findIndex((tab) => tab.id === activeTabId);

  // Update current tab
  const updateCurrentTab = (updates: Partial<SQLTab>) => {
    setTabs((prevTabs) =>
      prevTabs.map((tab) =>
        tab.id === activeTabId ? { ...tab, ...updates } : tab
      )
    );
  };

  // Add new tab
  const addNewTab = () => {
    const newTabNumber = tabs.length + 1;
    const newTab: SQLTab = {
      id: `tab-${Date.now()}`,
      name: `Query ${newTabNumber}`,
      query: "",
      result: null,
      isExecuting: false,
      viewMode: "editor",
    };
    setTabs([...tabs, newTab]);
    setActiveTabId(newTab.id);
  };

  // Close tab
  const closeTab = (tabId: string) => {
    if (tabs.length === 1) {
      toast({
        title: "Cannot Close",
        description: "You must have at least one query tab open.",
        variant: "destructive",
      });
      return;
    }

    const tabIndex = tabs.findIndex((tab) => tab.id === tabId);
    const newTabs = tabs.filter((tab) => tab.id !== tabId);
    setTabs(newTabs);

    // Switch to adjacent tab
    if (activeTabId === tabId) {
      const newActiveIndex = Math.min(tabIndex, newTabs.length - 1);
      setActiveTabId(newTabs[newActiveIndex].id);
    }
  };

  const executeQuery = async () => {
    if (!activeConfig) {
      toast({
        title: "No Database Connection",
        description: "Please select a database connection first.",
        variant: "destructive",
      });
      return;
    }

    if (!currentTab.query.trim()) {
      toast({
        title: "Empty Query",
        description: "Please enter an SQL query.",
        variant: "destructive",
      });
      return;
    }

    updateCurrentTab({ isExecuting: true, result: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/sql/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          config_name: activeConfig.name,
          query: currentTab.query,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: QueryResult = await response.json();
      updateCurrentTab({ result: data, isExecuting: false, viewMode: "results" });

      if (data.status === "success") {
        toast({
          title: "Query Executed",
          description: `Returned ${data.row_count} row(s) in ${(data.execution_time! * 1000).toFixed(2)}ms`,
        });
      } else {
        toast({
          title: "Query Failed",
          description: data.error || "Unknown error",
          variant: "destructive",
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to execute query";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      updateCurrentTab({
        result: {
          status: "error",
          columns: [],
          rows: [],
          row_count: 0,
          error: errorMessage,
        },
        isExecuting: false,
        viewMode: "results",
      });
    }
  };

  const copyResultsAsCSV = () => {
    if (!currentTab.result || currentTab.result.rows.length === 0) return;

    const csv = [
      currentTab.result.columns.join(","),
      ...currentTab.result.rows.map((row) =>
        currentTab.result!.columns.map((col) => {
          const val = row[col];
          return val === null || val === undefined ? "" : `"${String(val).replace(/"/g, '""')}"`;
        }).join(",")
      ),
    ].join("\n");

    navigator.clipboard.writeText(csv);
    toast({
      title: "Copied",
      description: "Results copied to clipboard as CSV",
    });
  };

  const downloadResultsAsCSV = () => {
    if (!currentTab.result || currentTab.result.rows.length === 0) return;

    const csv = [
      currentTab.result.columns.join(","),
      ...currentTab.result.rows.map((row) =>
        currentTab.result!.columns.map((col) => {
          const val = row[col];
          return val === null || val === undefined ? "" : `"${String(val).replace(/"/g, '""')}"`;
        }).join(",")
      ),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `query-results-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Downloaded",
      description: "Results downloaded as CSV",
    });
  };

  if (!activeConfig) {
    return (
      <div className="p-4 h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">No database connection configured.</p>
          <p className="text-xs mt-2">
            Configure a database connection to execute SQL queries.
          </p>
        </div>
      </div>
    );
  }

  return (
    <Tabs value={activeTabId} onValueChange={setActiveTabId} className="flex flex-col h-full">
      {/* Tab Headers */}
      <div className="flex-shrink-0 border-b bg-muted/30">
        <div className="flex items-center">
          <TabsList className="h-10 bg-transparent p-0 space-x-0">
            {tabs.map((tab) => (
              <div key={tab.id} className="relative group">
                <TabsTrigger
                  value={tab.id}
                  className="h-10 rounded-none border-b-2 border-b-transparent data-[state=active]:border-b-primary data-[state=active]:bg-transparent pr-8"
                >
                  {tab.name}
                  {tab.isExecuting && (
                    <Loader2 className="ml-2 h-3 w-3 animate-spin" />
                  )}
                </TabsTrigger>
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 opacity-0 group-hover:opacity-100"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </TabsList>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 ml-2"
            onClick={addNewTab}
            title="New Query Tab"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Tab Contents */}
      {tabs.map((tab) => (
        <TabsContent key={tab.id} value={tab.id} className="flex-1 m-0 data-[state=inactive]:hidden">
          <div className="flex flex-col h-full">
            {/* Toolbar */}
            <div className="flex-shrink-0 border-b bg-muted/50">
              <div className="flex items-center gap-2 p-2">
                {tab.viewMode === "editor" ? (
                  <>
                    <Button
                      size="sm"
                      onClick={() => {
                        if (tab.id === activeTabId) {
                          executeQuery();
                        }
                      }}
                      disabled={tab.isExecuting || !tab.query.trim()}
                      className="gap-1"
                    >
                      {tab.isExecuting ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Play className="h-3 w-3" />
                      )}
                      Execute
                    </Button>
                    {tab.result && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => updateCurrentTab({ viewMode: "results" })}
                        className="gap-1"
                      >
                        <Table2 className="h-3 w-3" />
                        Results
                      </Button>
                    )}
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => updateCurrentTab({ viewMode: "editor" })}
                    className="gap-1"
                  >
                    <Code2 className="h-3 w-3" />
                    Code
                  </Button>
                )}
                {tab.result && tab.result.rows.length > 0 && (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={copyResultsAsCSV}
                      className="gap-1"
                    >
                      <Copy className="h-3 w-3" />
                      Copy CSV
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={downloadResultsAsCSV}
                      className="gap-1"
                    >
                      <Download className="h-3 w-3" />
                      Download CSV
                    </Button>
                  </>
                )}
                <div className="ml-auto text-xs text-muted-foreground">
                  Connected to: <span className="font-semibold">{activeConfig.name}</span>
                </div>
              </div>
            </div>

            {/* Query Editor - Only show in editor mode */}
            {tab.viewMode === "editor" && (
              <div className="flex-shrink-0 border-b">
                <textarea
                  value={tab.query}
                  onChange={(e) => updateCurrentTab({ query: e.target.value })}
                  placeholder="Enter SQL query here... (e.g., SELECT * FROM customer LIMIT 10)"
                  className="w-full p-4 font-mono text-sm bg-background resize-none focus:outline-none focus:ring-0 border-0"
                  rows={8}
                  onKeyDown={(e) => {
                    if (e.ctrlKey && e.key === "Enter") {
                      executeQuery();
                    }
                  }}
                />
                <div className="px-4 pb-2 text-xs text-muted-foreground">
                  Press Ctrl+Enter to execute
                </div>
              </div>
            )}

            {/* Results */}
            <div className="flex-1 overflow-hidden relative">
              {tab.isExecuting && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2 text-primary" />
                    <p className="text-sm text-muted-foreground">Executing query...</p>
                  </div>
                </div>
              )}

              {!tab.isExecuting && !tab.result && (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-muted-foreground">
                    <p className="text-sm">No query executed yet.</p>
                    <p className="text-xs mt-2">
                      Write an SQL query above and click Execute or press Ctrl+Enter.
                    </p>
                  </div>
                </div>
              )}

              {!tab.isExecuting && tab.result && tab.result.status === "error" && (
                <div className="p-4">
                  <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4">
                    <p className="text-sm font-semibold text-destructive mb-2">❌ Query Error</p>
                    <pre className="text-xs text-destructive/90 whitespace-pre-wrap font-mono">
                      {tab.result.error}
                    </pre>
                  </div>
                </div>
              )}

              {!tab.isExecuting && tab.result && tab.result.status === "success" && (
                <div className="absolute inset-0 flex flex-col">
                  <div className="flex-shrink-0 px-4 py-2 bg-muted/30 border-b">
                    <p className="text-xs text-muted-foreground">
                      {tab.result.row_count} row(s) returned
                      {tab.result.execution_time && (
                        <span> in {(tab.result.execution_time * 1000).toFixed(2)}ms</span>
                      )}
                    </p>
                  </div>
                  {tab.result.rows.length === 0 ? (
                    <div className="flex items-center justify-center flex-1">
                      <p className="text-sm text-muted-foreground">Query executed successfully but returned no rows.</p>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-auto relative">
                      <Table>
                        <TableHeader className="sticky top-0 bg-background z-10">
                          <TableRow>
                            {tab.result.columns.map((column, index) => (
                              <TableHead key={index} className="font-semibold whitespace-nowrap bg-muted">
                                {column}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {tab.result.rows.map((row, rowIndex) => (
                            <TableRow key={rowIndex}>
                              {tab.result.columns.map((column, colIndex) => {
                                const value = row[column];
                                return (
                                  <TableCell key={colIndex} className="whitespace-nowrap">
                                    {value === null || value === undefined ? (
                                      <span className="text-muted-foreground italic">NULL</span>
                                    ) : (
                                      String(value)
                                    )}
                                  </TableCell>
                                );
                              })}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
