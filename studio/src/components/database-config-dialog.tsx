"use client";

import React, { useState, useEffect } from "react";
import { useDatabase } from "@/contexts/database-context";
import { useFileSystem } from "@/contexts/file-system-context";
import { type DatabaseConfig, WS_BASE_URL } from "@/lib/api-client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { RemoteDirectoryBrowser } from "@/components/remote-directory-browser";
import { useToast } from "@/hooks/use-toast";
import { Loader2, Database, Trash2, CheckCircle2, Pencil, FolderOpen } from "lucide-react";

interface DatabaseConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DatabaseConfigDialog({ open, onOpenChange }: DatabaseConfigDialogProps) {
  const {
    availableConfigs,
    activeConfig,
    isLoading,
    testConnection,
    saveConfig,
    deleteConfig,
    setActiveConfig,
    loadConfigWithPassword,
  } = useDatabase();
  const { setMode } = useFileSystem();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState<"new" | "select">("select");
  const [configTab, setConfigTab] = useState<"database" | "ssh" | "remote">("database");
  const [isEditing, setIsEditing] = useState(false);
  const [editingConfigName, setEditingConfigName] = useState<string | null>(null);
  const [formData, setFormData] = useState<DatabaseConfig>({
    name: "",
    host: "informix",
    port: 9088,
    database: "",
    username: "informix",
    password: "",
    driver: "wbjdbc",
    server: "informix",
    db_type: "informix",
  });

  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [showDirectoryBrowser, setShowDirectoryBrowser] = useState(false);

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setTestResult(null);
      setIsEditing(false);
      setEditingConfigName(null);
      if (availableConfigs.length === 0) {
        setActiveTab("new");
      } else {
        setActiveTab("select");
      }
    }
  }, [open, availableConfigs.length]);

  const handleInputChange = (field: keyof DatabaseConfig, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      if (configTab === "ssh") {
        // Test SSH connection
        const sshHost = formData.ssh_host || formData.host;
        const sshPort = formData.ssh_port || 22;
        const sshUsername = formData.ssh_username || formData.username;
        const sshPassword = formData.ssh_password || formData.password;

        if (!sshHost || !sshUsername || !sshPassword) {
          setTestResult({
            success: false,
            message: "Please fill in SSH host, username, and password",
          });
          return;
        }

        // Test SSH by trying to connect via WebSocket
        const testSuccess = await new Promise<boolean>((resolve) => {
          const wsUrl = `${WS_BASE_URL}/api/terminal/connect`;
          const ws = new WebSocket(wsUrl);

          const timeout = setTimeout(() => {
            ws.close();
            resolve(false);
          }, 10000);

          ws.onopen = () => {
            ws.send(JSON.stringify({
              host: sshHost,
              port: sshPort,
              username: sshUsername,
              password: sshPassword,
              database: formData.database || 'test',
            }));
          };

          ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            clearTimeout(timeout);
            ws.close();
            resolve(message.type === 'connected');
          };

          ws.onerror = () => {
            clearTimeout(timeout);
            ws.close();
            resolve(false);
          };
        });

        setTestResult({
          success: testSuccess,
          message: testSuccess
            ? `SSH connection successful to ${sshUsername}@${sshHost}:${sshPort}`
            : "SSH connection failed",
        });
      } else {
        // Test database connection
        if (!formData.host || !formData.database) {
          setTestResult({
            success: false,
            message: "Please fill in Host and Database fields",
          });
          return;
        }

        if (formData.db_type === "informix" && !formData.server) {
          setTestResult({
            success: false,
            message: "Server parameter is required for Informix connections",
          });
          return;
        }

        const success = await testConnection(formData);
        setTestResult({
          success,
          message: success ? "Database connection successful!" : "Database connection failed",
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: `Error: ${error}`,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveConfig = async () => {
    if (!formData.name || !formData.host || !formData.database) {
      setTestResult({
        success: false,
        message: "Please fill in all required fields",
      });
      return;
    }

    // Validate server parameter for Informix
    if (formData.db_type === "informix" && !formData.server) {
      setTestResult({
        success: false,
        message: "Server parameter is required for Informix connections",
      });
      return;
    }

    setIsSaving(true);
    setTestResult({
      success: true,
      message: "Saving and connecting...",
    });

    try {
      // If editing and name changed, delete the old config
      if (isEditing && editingConfigName && editingConfigName !== formData.name) {
        await deleteConfig(editingConfigName);
      }

      await saveConfig(formData);
      setTestResult({
        success: true,
        message: isEditing ? "Configuration updated successfully!" : "Configuration saved successfully!",
      });

      // Set this config as active
      setActiveConfig(formData);

      // If remote files is enabled, switch to remote mode
      if (formData.use_remote_files && formData.name) {
        try {
          // Reset workspace path to default when connecting
          const configWithDefaultPath = {
            ...formData,
            remote_workspace_path: formData.remote_workspace_path || "~/fgl-projects"
          };
          await setMode("remote", formData.name, configWithDefaultPath);
        } catch (error: any) {
          console.error("Failed to switch to remote mode:", error);
          const errorMsg = error?.message || String(error);
          setTestResult({
            success: false,
            message: `Configuration saved, but cannot switch to remote mode: ${errorMsg}`,
          });
          alert(`Configuration saved successfully!\n\nHowever, cannot switch to remote mode:\n${errorMsg}\n\nPlease save or close all files, then select this configuration again.`);
          return;
        }
      } else {
        // Switch back to local mode if use_remote_files was disabled
        try {
          await setMode("local");
        } catch (error: any) {
          console.error("Failed to switch to local mode:", error);
          const errorMsg = error?.message || String(error);
          setTestResult({
            success: false,
            message: `Configuration saved, but cannot switch to local mode: ${errorMsg}`,
          });
          alert(`Configuration saved successfully!\n\nHowever, cannot switch to local mode:\n${errorMsg}\n\nPlease save or close all files first.`);
          return;
        }
      }

      // Reset form and editing state
      setFormData({
        name: "",
        host: "informix",
        port: 9088,
        database: "",
        username: "informix",
        password: "",
        driver: "wbjdbc",
        server: "informix",
        db_type: "informix",
      });
      setIsEditing(false);
      setEditingConfigName(null);

      // Close dialog after successful save
      onOpenChange(false);
    } catch (error) {
      // Error handling is done in the context
      setTestResult({
        success: false,
        message: `Error saving configuration: ${error}`,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleSelectConfig = async (config: DatabaseConfig) => {
    if (!config.name) return;

    try {
      // Fetch the full configuration with password from backend
      const fullConfig = await loadConfigWithPassword(config.name);
      setActiveConfig(fullConfig);

      // If remote files is enabled, switch to remote mode
      if (fullConfig.use_remote_files) {
        try {
          await setMode("remote", fullConfig.name, fullConfig);
        } catch (error: any) {
          console.error("Failed to switch to remote mode:", error);
          // Show user-friendly error message
          const errorMsg = error?.message || String(error);
          alert(`Cannot switch to remote mode:\n\n${errorMsg}\n\nPlease save or close all files before switching to remote mode.`);
          return; // Don't close dialog
        }
      } else {
        // Switch back to local mode if not using remote files
        try {
          await setMode("local");
        } catch (error: any) {
          console.error("Failed to switch to local mode:", error);
          const errorMsg = error?.message || String(error);
          alert(`Cannot switch to local mode:\n\n${errorMsg}\n\nPlease save or close all files before switching modes.`);
          return; // Don't close dialog
        }
      }

      onOpenChange(false);
    } catch (error) {
      // Error is already handled in the context with toast
      console.error("Failed to load configuration:", error);
    }
  };

  const handleDeleteConfig = async (name: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm(`Are you sure you want to delete the configuration "${name}"?`)) {
      return;
    }

    try {
      await deleteConfig(name);
    } catch (error) {
      // Error handling is done in the context
    }
  };

  const handleEditConfig = (config: DatabaseConfig, e: React.MouseEvent) => {
    e.stopPropagation();

    // Find the full config with password from backend
    const fullConfig = availableConfigs.find(c => c.name === config.name);
    if (fullConfig) {
      setFormData({
        ...fullConfig,
        password: "", // Password needs to be re-entered for security
      });
      setIsEditing(true);
      setEditingConfigName(config.name!);
      setActiveTab("new");
      setTestResult(null);
    }
  };

  const handleBrowseRemoteDirectory = () => {
    // Validate SSH credentials before opening browser
    if (!formData.ssh_host && !formData.host) {
      setTestResult({
        success: false,
        message: "Please configure SSH host before browsing directories",
      });
      return;
    }

    if (!formData.ssh_username && !formData.username) {
      setTestResult({
        success: false,
        message: "Please configure SSH username before browsing directories",
      });
      return;
    }

    if (!formData.ssh_password && !formData.password) {
      setTestResult({
        success: false,
        message: "Please configure SSH password before browsing directories",
      });
      return;
    }

    setShowDirectoryBrowser(true);
  };

  const handleDirectorySelect = (path: string) => {
    setFormData((prev) => ({ ...prev, remote_workspace_path: path }));
  };

  const handleClearActiveConnection = async () => {
    try {
      // Switch back to local mode
      await setMode("local");
      // Clear active database config
      setActiveConfig(null);
      toast({
        title: "Disconnected",
        description: "Switched back to local file system",
      });
    } catch (error: any) {
      const errorMsg = error?.message || String(error);
      toast({
        title: "Error",
        description: `Failed to disconnect: ${errorMsg}`,
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Database Configuration</DialogTitle>
          <DialogDescription>
            Configure and manage database connections for your 4GL code execution.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "new" | "select")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="select">Select Connection</TabsTrigger>
            <TabsTrigger value="new">New Connection</TabsTrigger>
          </TabsList>

          <TabsContent value="select" className="space-y-4">
            {availableConfigs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Database className="mx-auto h-12 w-12 mb-4 opacity-50" />
                <p>No saved configurations</p>
                <p className="text-sm mt-2">Create a new connection to get started</p>
              </div>
            ) : (
              <div className="space-y-2">
                {availableConfigs.map((config) => (
                  <div
                    key={config.name}
                    className={`flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-accent transition-colors ${
                      activeConfig?.name === config.name ? "border-primary bg-accent" : ""
                    }`}
                    onClick={() => handleSelectConfig(config)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium">{config.name}</h4>
                        {activeConfig?.name === config.name && (
                          <Badge variant="default" className="text-xs">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {config.host}:{config.port}/{config.database}
                        {config.server && ` (server: ${config.server})`}
                      </p>
                      <div className="flex gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {config.driver}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {config.db_type}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleEditConfig(config, e)}
                        disabled={isLoading}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleDeleteConfig(config.name!, e)}
                        disabled={isLoading}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeConfig && (
              <div className="pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={handleClearActiveConnection}
                  className="w-full"
                >
                  Clear Active Connection
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="new" className="space-y-4">
            {isEditing && (
              <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                Editing configuration: <span className="font-medium">{editingConfigName}</span>
              </div>
            )}

            {/* Inner tabs for Database, SSH, and Remote Files config */}
            <Tabs value={configTab} onValueChange={(v) => setConfigTab(v as "database" | "ssh" | "remote")} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="database">Database</TabsTrigger>
                <TabsTrigger value="ssh">SSH Terminal</TabsTrigger>
                <TabsTrigger value="remote">Remote Files</TabsTrigger>
              </TabsList>

              <TabsContent value="database" className="space-y-4 mt-4">
            <div className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="name">
                  Connection Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  placeholder="My Informix DB"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="host">
                    Host <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="host"
                    placeholder="localhost"
                    value={formData.host}
                    onChange={(e) => handleInputChange("host", e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="port">Port</Label>
                  <Input
                    id="port"
                    type="number"
                    placeholder="9088"
                    value={formData.port}
                    onChange={(e) => handleInputChange("port", parseInt(e.target.value) || 9088)}
                  />
                </div>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="database">
                  Database <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="database"
                  placeholder="testdb"
                  value={formData.database}
                  onChange={(e) => handleInputChange("database", e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="server">
                  Server Name {formData.db_type === "informix" && <span className="text-destructive">* (Required for Informix)</span>}
                </Label>
                <Input
                  id="server"
                  placeholder="informix"
                  value={formData.server || ""}
                  onChange={(e) => handleInputChange("server", e.target.value)}
                />
                {formData.db_type === "informix" && (
                  <p className="text-xs text-muted-foreground">
                    For Informix connections, the server name is mandatory
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    placeholder="informix"
                    value={formData.username}
                    onChange={(e) => handleInputChange("username", e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="driver">Backend Mode</Label>
                  <Select
                    value={formData.driver}
                    onValueChange={(value) => handleInputChange("driver", value)}
                  >
                    <SelectTrigger id="driver">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="wbjdbc">WBJDBC (Direct SQL)</SelectItem>
                      <SelectItem value="wborm">WBORM (ORM via WBJDBC)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Both use WBJDBC driver. WBORM provides ORM-style access.
                  </p>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="db_type">Database Type</Label>
                  <Select
                    value={formData.db_type}
                    onValueChange={(value) => handleInputChange("db_type", value)}
                  >
                    <SelectTrigger id="db_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="informix">Informix</SelectItem>
                      <SelectItem value="mysql">MySQL</SelectItem>
                      <SelectItem value="postgresql">PostgreSQL</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
              </TabsContent>

              <TabsContent value="ssh" className="space-y-4 mt-4">
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground">
                    Configure SSH access for terminal. If not provided, database credentials will be used as fallback.
                  </p>
                </div>
                <div className="grid gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="ssh_host">SSH Host</Label>
                    <Input
                      id="ssh_host"
                      placeholder={formData.host || "Same as database host"}
                      value={formData.ssh_host || ""}
                      onChange={(e) => handleInputChange("ssh_host", e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Leave empty to use database host
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ssh_port">SSH Port</Label>
                    <Input
                      id="ssh_port"
                      type="number"
                      placeholder="22"
                      value={formData.ssh_port || ""}
                      onChange={(e) => handleInputChange("ssh_port", parseInt(e.target.value) || 22)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="grid gap-2">
                    <Label htmlFor="ssh_username">SSH Username</Label>
                    <Input
                      id="ssh_username"
                      placeholder={formData.username || "Same as database username"}
                      value={formData.ssh_username || ""}
                      onChange={(e) => handleInputChange("ssh_username", e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Leave empty to use database username
                    </p>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="ssh_password">SSH Password</Label>
                    <Input
                      id="ssh_password"
                      type="password"
                      placeholder="Same as database password"
                      value={formData.ssh_password || ""}
                      onChange={(e) => handleInputChange("ssh_password", e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      Leave empty to use database password
                    </p>
                  </div>
                </div>
                </div>
              </TabsContent>

              <TabsContent value="remote" className="space-y-4 mt-4">
                <div className="mb-4">
                  <p className="text-sm text-muted-foreground">
                    Work directly on the remote server via SFTP. Files will be stored in a workspace directory on the SSH server.
                  </p>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="use-remote-files"
                      checked={formData.use_remote_files || false}
                      onCheckedChange={(checked) => handleInputChange("use_remote_files", !!checked)}
                    />
                    <label htmlFor="use-remote-files" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                      Use Remote Files (work directly on server)
                    </label>
                  </div>

                  {formData.use_remote_files && (
                    <div className="grid gap-2 pl-6">
                      <Label htmlFor="remote-workspace">Remote Workspace Path</Label>
                      <div className="flex gap-2">
                        <Input
                          id="remote-workspace"
                          value={formData.remote_workspace_path || "~/fgl-projects"}
                          onChange={(e) => handleInputChange("remote_workspace_path", e.target.value)}
                          placeholder="~/fgl-projects"
                        />
                        <Button
                          variant="outline"
                          size="icon"
                          type="button"
                          title="Browse directories on server"
                          onClick={handleBrowseRemoteDirectory}
                        >
                          <FolderOpen className="h-4 w-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        All files will be stored in this directory on the server. The directory will be created if it doesn't exist.
                      </p>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>

            {testResult && (
                <div
                  className={`p-4 rounded-lg ${
                    testResult.success
                      ? "bg-green-500/10 text-green-700 dark:text-green-400 border border-green-500/20"
                      : "bg-destructive/10 text-destructive border border-destructive/20"
                  }`}
                >
                  {testResult.message}
                </div>
              )}

            <DialogFooter className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={isTesting || isLoading}
              >
                {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Test Connection
              </Button>
              <Button onClick={handleSaveConfig} disabled={isLoading || isSaving}>
                {(isLoading || isSaving) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSaving ? "Connecting..." : isEditing ? "Update Configuration" : "Save Configuration"}
              </Button>
            </DialogFooter>
          </TabsContent>
        </Tabs>
      </DialogContent>

      {/* Remote Directory Browser */}
      {formData.name && (
        <RemoteDirectoryBrowser
          open={showDirectoryBrowser}
          onOpenChange={setShowDirectoryBrowser}
          configName={formData.name}
          configData={formData}
          initialPath={formData.remote_workspace_path || "~"}
          onSelect={handleDirectorySelect}
        />
      )}
    </Dialog>
  );
}
