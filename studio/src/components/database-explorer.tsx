"use client";

import * as React from "react";
import { useState, useEffect } from "react";
import {
  Database,
  Table2,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Key,
  Circle,
  Loader2,
  AlertCircle,
  Eye,
  Search,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { apiClient } from "@/lib/api-client";
import { useToast } from "@/hooks/use-toast";
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
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { Copy, Code, Eye as EyeIcon } from "lucide-react";

interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  default_value?: string;
  description?: string;
}

interface TableInfo {
  name: string;
  type: string;
  columns: TableColumn[];
  row_count?: number;
}

interface DatabaseExplorerProps {
  configName: string | null;
  databaseName?: string;
}

export function DatabaseExplorer({ configName, databaseName }: DatabaseExplorerProps) {
  const { toast } = useToast();
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [loadingTables, setLoadingTables] = useState<boolean>(false);
  const [loadingSchemas, setLoadingSchemas] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Data viewer state
  const [dataViewerOpen, setDataViewerOpen] = useState<boolean>(false);
  const [selectedTableForData, setSelectedTableForData] = useState<string | null>(null);
  const [tableData, setTableData] = useState<any[]>([]);
  const [loadingTableData, setLoadingTableData] = useState<boolean>(false);

  // Load tables when configName changes
  useEffect(() => {
    if (configName) {
      loadTables();
    } else {
      setTables([]);
      setError(null);
    }
  }, [configName]);

  const loadTables = async () => {
    if (!configName) return;

    setLoadingTables(true);
    setError(null);

    try {
      const response = await apiClient.getDatabaseTables(configName);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to load tables");
      }

      setTables(response.tables || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load tables";
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoadingTables(false);
    }
  };

  const loadTableSchema = async (tableName: string) => {
    if (!configName) return;

    setLoadingSchemas((prev) => new Set(prev).add(tableName));

    try {
      const response = await apiClient.getTableSchema(configName, tableName);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to load table schema");
      }

      if (response.table) {
        setTables((prev) =>
          prev.map((t) =>
            t.name === tableName ? { ...t, columns: response.table!.columns } : t
          )
        );
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load schema";
      toast({
        title: "Error",
        description: `Failed to load schema for ${tableName}: ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      setLoadingSchemas((prev) => {
        const next = new Set(prev);
        next.delete(tableName);
        return next;
      });
    }
  };

  const toggleTable = (tableName: string) => {
    const isExpanded = expandedTables.has(tableName);

    if (!isExpanded) {
      // Expanding - load schema if not already loaded
      const table = tables.find((t) => t.name === tableName);
      if (table && table.columns.length === 0) {
        loadTableSchema(tableName);
      }
    }

    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (isExpanded) {
        next.delete(tableName);
      } else {
        next.add(tableName);
      }
      return next;
    });
  };

  const handleRefresh = async () => {
    if (!configName) return;

    try {
      await apiClient.refreshDatabaseSchema(configName);
      await loadTables();

      toast({
        title: "Refreshed",
        description: "Database schema refreshed successfully",
      });
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to refresh schema",
        variant: "destructive",
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied",
      description: `Copied "${text}" to clipboard`,
    });
  };

  // Filter tables based on search query
  const filteredTables = React.useMemo(() => {
    if (!searchQuery.trim()) return tables;

    const query = searchQuery.toLowerCase();
    return tables.filter((table) => {
      // Match by table name
      if (table.name.toLowerCase().includes(query)) return true;

      // Match by column name
      if (table.columns.some((col) => col.name.toLowerCase().includes(query))) return true;

      return false;
    });
  }, [tables, searchQuery]);

  // Auto-expand tables that match the search
  useEffect(() => {
    if (searchQuery.trim() && filteredTables.length > 0) {
      const matchingTableIds = filteredTables
        .filter((table) => {
          const query = searchQuery.toLowerCase();
          return table.columns.some((col) => col.name.toLowerCase().includes(query));
        })
        .map((table) => table.name);

      if (matchingTableIds.length > 0) {
        setExpandedTables((prev) => {
          const next = new Set(prev);
          matchingTableIds.forEach((id) => next.add(id));
          return next;
        });

        // Load schemas for matching tables
        matchingTableIds.forEach((tableName) => {
          const table = tables.find((t) => t.name === tableName);
          if (table && table.columns.length === 0) {
            loadTableSchema(tableName);
          }
        });
      }
    }
  }, [searchQuery, filteredTables]);

  const viewTableData = async (tableName: string) => {
    if (!configName) return;

    setSelectedTableForData(tableName);
    setDataViewerOpen(true);
    setLoadingTableData(true);
    setTableData([]);

    try {
      const response = await apiClient.getTableData(configName, tableName, 100);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to load table data");
      }

      setTableData(response.rows || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load table data";
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
      setDataViewerOpen(false);
    } finally {
      setLoadingTableData(false);
    }
  };

  if (!configName) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-4 text-center text-muted-foreground">
        <Database className="h-12 w-12 mb-2 opacity-50" />
        <p className="text-sm">No database connection configured</p>
        <p className="text-xs mt-1">Configure a database connection to explore schema</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-2 border-b">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold">
            {databaseName || configName}
          </span>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={handleRefresh}
          disabled={loadingTables}
        >
          <RefreshCw className={`h-3 w-3 ${loadingTables ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* Search Bar */}
      <div className="p-2 border-b">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search tables or columns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-7 pr-7 h-7 text-xs"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-0 top-1/2 transform -translate-y-1/2 h-6 w-6"
              onClick={() => setSearchQuery("")}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>
        {searchQuery && (
          <p className="text-xs text-muted-foreground mt-1">
            Found {filteredTables.length} {filteredTables.length === 1 ? 'table' : 'tables'}
          </p>
        )}
      </div>

      {/* Content */}
      <ScrollArea className="flex-1">
        {error && (
          <div className="p-4 m-2 bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-destructive">Error loading database</p>
              <p className="text-xs text-destructive/80 mt-1">{error}</p>
            </div>
          </div>
        )}

        {loadingTables && (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loadingTables && !error && tables.length === 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
            <Table2 className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No tables found</p>
          </div>
        )}

        {!loadingTables && !error && searchQuery && filteredTables.length === 0 && tables.length > 0 && (
          <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
            <Search className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No tables or columns match "{searchQuery}"</p>
          </div>
        )}

        {!loadingTables && !error && filteredTables.length > 0 && (
          <div className="p-2">
            {filteredTables.map((table) => {
              const isExpanded = expandedTables.has(table.name);
              const isLoadingSchema = loadingSchemas.has(table.name);

              const generateSelect = (tableName: string) => {
                const sql = `SELECT * FROM ${tableName}`;
                navigator.clipboard.writeText(sql);
                toast({
                  title: "Copied",
                  description: `SELECT statement copied to clipboard`,
                });
              };

              return (
                <ContextMenu key={table.name}>
                  <ContextMenuTrigger>
                    <Collapsible
                      open={isExpanded}
                      onOpenChange={() => toggleTable(table.name)}
                    >
                      <div className="flex items-center gap-0.5 p-1 rounded hover:bg-accent text-sm group w-full">
                        <CollapsibleTrigger className="flex items-center gap-1 min-w-0 flex-1">
                          {isExpanded ? (
                            <ChevronDown className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                          ) : (
                            <ChevronRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                          )}
                          <Table2 className="h-3 w-3 text-primary flex-shrink-0" />
                          <span
                            className="text-left truncate"
                            title={table.name}
                          >
                            {table.name.length > 20 ? table.name.substring(0, 17) + "..." : table.name}
                          </span>
                          {table.type === "view" && (
                            <span className="text-xs text-muted-foreground flex-shrink-0 ml-1">(view)</span>
                          )}
                        </CollapsibleTrigger>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-5 w-5 flex-shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            viewTableData(table.name);
                          }}
                          title="View sample data"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                      <CollapsibleContent>
                        {isLoadingSchema ? (
                          <div className="flex items-center gap-2 p-2 pl-8 text-xs text-muted-foreground">
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>Loading columns...</span>
                          </div>
                        ) : (
                          <div className="pl-6 space-y-0.5">
                            {table.columns.map((column) => (
                              <TooltipProvider key={column.name}>
                                <Tooltip>
                                  <TooltipTrigger asChild>
                                    <div
                                      className="flex items-center gap-1 p-1 rounded hover:bg-accent text-xs cursor-pointer"
                                      onClick={() => copyToClipboard(column.name)}
                                    >
                                      {column.primary_key ? (
                                        <Key className="h-2.5 w-2.5 text-yellow-500" />
                                      ) : (
                                        <Circle className="h-2 w-2 text-muted-foreground" />
                                      )}
                                      <span className="flex-1 truncate">{column.name}</span>
                                      <span className="text-muted-foreground text-xs">
                                        {column.type}
                                      </span>
                                      {!column.nullable && (
                                        <span className="text-red-500 text-xs font-bold">*</span>
                                      )}
                                    </div>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    <div className="text-xs">
                                      <p><strong>{column.name}</strong></p>
                                      <p>Type: {column.type}</p>
                                      <p>Nullable: {column.nullable ? "Yes" : "No"}</p>
                                      {column.primary_key && <p className="text-yellow-500">Primary Key</p>}
                                      {column.default_value && <p>Default: {column.default_value}</p>}
                                      <p className="mt-1 text-muted-foreground">Click to copy column name</p>
                                    </div>
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            ))}
                          </div>
                        )}
                      </CollapsibleContent>
                    </Collapsible>
                  </ContextMenuTrigger>
                  <ContextMenuContent>
                    <ContextMenuItem onClick={() => copyToClipboard(table.name)}>
                      <Copy className="mr-2 h-4 w-4" />
                      Copy Table Name
                    </ContextMenuItem>
                    <ContextMenuItem onClick={() => generateSelect(table.name)}>
                      <Code className="mr-2 h-4 w-4" />
                      Generate SELECT *
                    </ContextMenuItem>
                    <ContextMenuSeparator />
                    <ContextMenuItem onClick={() => viewTableData(table.name)}>
                      <Eye className="mr-2 h-4 w-4" />
                      View Sample Data
                    </ContextMenuItem>
                  </ContextMenuContent>
                </ContextMenu>
              );
            })}
          </div>
        )}
      </ScrollArea>

      {/* Table Data Viewer Dialog */}
      <Dialog open={dataViewerOpen} onOpenChange={(open) => {
        setDataViewerOpen(open);
        if (!open) {
          setTableData([]);
          setSelectedTableForData(null);
        }
      }}>
        <DialogContent
          className="max-w-6xl max-h-[80vh] flex flex-col"
          onInteractOutside={(e) => {
            e.preventDefault();
            setDataViewerOpen(false);
          }}
          onEscapeKeyDown={() => setDataViewerOpen(false)}
        >
          <DialogHeader>
            <DialogTitle>Sample Data: {selectedTableForData}</DialogTitle>
            <DialogDescription>
              Showing {tableData.length} rows from the table
            </DialogDescription>
          </DialogHeader>

          {loadingTableData ? (
            <div className="flex items-center justify-center p-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : tableData.length === 0 ? (
            <div className="flex flex-col items-center justify-center p-12 text-muted-foreground">
              <Table2 className="h-12 w-12 mb-2 opacity-50" />
              <p className="text-sm">No data found in this table</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2 flex-1 min-h-0 overflow-hidden">
              <div className="flex-1 border rounded-md overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {Object.keys(tableData[0] || {}).map((column) => (
                        <TableHead key={column} className="font-semibold whitespace-nowrap bg-muted sticky top-0 z-10">
                          {column}
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {tableData.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {Object.values(row).map((value: any, cellIndex) => (
                          <TableCell key={cellIndex} className="whitespace-nowrap">
                            {value === null || value === undefined ? (
                              <span className="text-muted-foreground italic">NULL</span>
                            ) : (
                              String(value)
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="flex justify-end pt-2">
                <Button variant="outline" onClick={() => setDataViewerOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
