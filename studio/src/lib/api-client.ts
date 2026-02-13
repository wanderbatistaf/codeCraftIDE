/**
 * API client for communicating with the fglInterpreter backend.
 */

import type { FileTreeNode } from "./file-tree";

// API base URL - can be configured via environment variable
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// WebSocket base URL - derived from API_BASE_URL or explicit override
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  API_BASE_URL.replace(/^http/, "ws");

export interface DatabaseConfig {
  name?: string; // User-friendly name for the connection
  host: string;
  port: number;
  database: string;
  username?: string;
  password?: string;
  driver: "wbjdbc" | "wborm";
  server?: string; // Informix server name
  db_type?: string; // Database type (informix, mysql, postgresql)
  // SSH-specific fields for terminal connection (optional)
  ssh_host?: string; // SSH host (default: same as host)
  ssh_port?: number; // SSH port (default: 22)
  ssh_username?: string; // SSH username (default: same as username)
  ssh_password?: string; // SSH password (default: same as password)
  // Remote file system settings (optional)
  use_remote_files?: boolean; // Use SFTP for file operations
  remote_workspace_path?: string; // Remote workspace directory (default: ~/fgl-projects)
}

export interface ExecuteRequest {
  code: string;
  database_config?: DatabaseConfig;
  enable_profiling?: boolean;
}

export interface ExecuteResponse {
  status: "success" | "error";
  output?: string;
  execution_time?: number;
  profiling?: any;
  error?: string;
  message?: string;
  line?: number;
  column?: number;
}

export interface ParseRequest {
  code: string;
}

export interface ParseResponse {
  status: "success" | "error";
  ast?: any;
  tokens?: any;
  error?: string;
  message?: string;
  line?: number;
  column?: number;
}

export interface QuickFix {
  title: string;
  new_text: string;
  insert_line: number;
  insert_column: number;
  description?: string;
}

export interface Diagnostic {
  severity: "error" | "warning" | "info" | "hint";
  message: string;
  line: number;
  column: number;
  end_line?: number;
  end_column?: number;
  quick_fixes: QuickFix[];
}

export interface DiagnosticsRequest {
  code: string;
}

export interface DiagnosticsResponse {
  status: "success" | "error";
  diagnostics?: Diagnostic[];
  error?: string;
  message?: string;
}

export interface CodeActionsRequest {
  code: string;
  line: number;
  column: number;
}

export interface CodeAction {
  title: string;
  new_text: string;
  insert_line: number;
  insert_column: number;
  description?: string;
}

export interface CodeActionsResponse {
  status: "success" | "error";
  actions?: CodeAction[];
  error?: string;
  message?: string;
}

export interface CompilationMessage {
  file: string;
  line?: number;
  column?: number;
  severity: string;
  message: string;
  code?: string;
  suggestion?: string;
}

export interface CompileRequest {
  code?: string;
  file_path?: string;
  directory?: string;
  target_name?: string;
  make_executable?: string;
  library_path?: string;
  keep_temp_files?: boolean;
}

export interface CompileResponse {
  status: string;
  success: boolean;
  target: string;
  output: string;
  errors: CompilationMessage[];
  warnings: CompilationMessage[];
  compilation_time: number;
  make_def_content: string;
  error_count: number;
  warning_count: number;
}

export interface ConversionRequest {
  source: string;
  config?: any;
}

export interface ConversionResponse {
  python: string;
  warnings: string[];
  lineMapping: Record<number, number>;
}

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: response.statusText,
      }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<{
    status: string;
    version: string;
    interpreter_ready: boolean;
    database_drivers: string[];
  }> {
    return this.request("/api/health");
  }

  // File operations
  async getFileTree(): Promise<{ tree: FileTreeNode }> {
    return this.request("/api/files/tree");
  }

  async getFileContent(path: string): Promise<{ path: string; content: string }> {
    return this.request(`/api/files/content?path=${encodeURIComponent(path)}`);
  }

  async saveFileContent(path: string, content: string): Promise<{ status: string; message: string }> {
    return this.request("/api/files/content", {
      method: "POST",
      body: JSON.stringify({ path, content }),
    });
  }

  async createNode(
    parentPath: string,
    name: string,
    type: "file" | "folder"
  ): Promise<{ status: string; node: FileTreeNode }> {
    return this.request("/api/files/create", {
      method: "POST",
      body: JSON.stringify({ parentPath, name, type }),
    });
  }

  async renameNode(
    oldPath: string,
    newName: string
  ): Promise<{ status: string; node: FileTreeNode }> {
    return this.request("/api/files/rename", {
      method: "POST",
      body: JSON.stringify({ oldPath, newName }),
    });
  }

  async deleteNode(path: string): Promise<{ status: string; message: string }> {
    return this.request("/api/files/delete", {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  }

  async searchFiles(
    query: string,
    caseSensitive: boolean = false,
    regex: boolean = false
  ): Promise<{
    status: string;
    results: Array<{
      file: string;
      matches: Array<{
        line: number;
        column: number;
        text: string;
      }>;
    }>;
    error?: string;
  }> {
    return this.request("/api/files/search", {
      method: "POST",
      body: JSON.stringify({ query, case_sensitive: caseSensitive, regex }),
    });
  }

  // Code execution
  async executeCode(request: ExecuteRequest): Promise<ExecuteResponse> {
    return this.request("/api/execute", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Code parsing/validation
  async parseCode(request: ParseRequest): Promise<ParseResponse> {
    return this.request("/api/parse", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Code diagnostics
  async getDiagnostics(request: DiagnosticsRequest): Promise<DiagnosticsResponse> {
    return this.request("/api/diagnostics", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Code actions (quick fixes)
  async getCodeActions(request: CodeActionsRequest): Promise<CodeActionsResponse> {
    return this.request("/api/code-actions", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // Code conversion
  async convertCode(request: ConversionRequest): Promise<ConversionResponse> {
    return this.request("/api/conversion/convert", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getConversionConfig(): Promise<any> {
    return this.request("/api/conversion/config");
  }

  async saveConversionConfig(config: any): Promise<{ status: string; file: string }> {
    return this.request("/api/conversion/config", {
      method: "POST",
      body: JSON.stringify(config),
    });
  }

  async getConversionMappings(): Promise<any> {
    return this.request("/api/conversion/mappings");
  }

  async convertPythonTo4GL(pythonCode: string): Promise<{ fgl_code: string; warnings: string[] }> {
    return this.request("/api/conversion/reverse", {
      method: "POST",
      body: JSON.stringify({ python_code: pythonCode }),
    });
  }

  // Database operations
  async testDatabaseConnection(config: DatabaseConfig): Promise<{
    success: boolean;
    message: string;
    error?: string;
  }> {
    return this.request("/api/database/test", {
      method: "POST",
      body: JSON.stringify({ config }),
    });
  }

  async getDatabaseConfigs(): Promise<{ configs: DatabaseConfig[] }> {
    return this.request("/api/database/configs");
  }

  async getDatabaseConfig(name: string): Promise<DatabaseConfig> {
    return this.request(`/api/database/configs/${encodeURIComponent(name)}`);
  }

  async saveDatabaseConfig(config: DatabaseConfig): Promise<{
    success: boolean;
    message: string;
  }> {
    return this.request("/api/database/configs", {
      method: "POST",
      body: JSON.stringify({ config }),
    });
  }

  async deleteDatabaseConfig(name: string): Promise<{
    success: boolean;
    message: string;
  }> {
    return this.request("/api/database/configs", {
      method: "DELETE",
      body: JSON.stringify({ name }),
    });
  }

  async getAvailableDrivers(): Promise<{
    available: Record<string, boolean>;
    supported_db_types: string[];
  }> {
    return this.request("/api/database/drivers");
  }

  // Compilation
  async compileCode(request: CompileRequest): Promise<CompileResponse> {
    return this.request("/api/compile", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  // SFTP file operations (remote file system)
  async getSFTPTree(configName: string, configData: DatabaseConfig): Promise<{ tree: FileTreeNode }> {
    return this.request("/api/sftp/tree", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData }),
    });
  }

  async getSFTPFileContent(configName: string, configData: DatabaseConfig, path: string): Promise<{ path: string; content: string }> {
    return this.request("/api/sftp/content/read", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path }),
    });
  }

  async getSFTPFileContentAbsolute(configName: string, configData: DatabaseConfig, path: string): Promise<{ path: string; content: string }> {
    return this.request("/api/sftp/content/read-absolute", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path }),
    });
  }

  async saveSFTPFileContent(configName: string, configData: DatabaseConfig, path: string, content: string): Promise<{ status: string; message: string }> {
    return this.request("/api/sftp/content/write", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path, content }),
    });
  }

  async saveSFTPFileContentAbsolute(configName: string, configData: DatabaseConfig, path: string, content: string): Promise<{ status: string; message: string }> {
    return this.request("/api/sftp/content/write-absolute", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path, content }),
    });
  }

  async createSFTPNode(
    configName: string,
    configData: DatabaseConfig,
    parentPath: string,
    name: string,
    type: "file" | "folder"
  ): Promise<{ status: string; node: FileTreeNode }> {
    return this.request("/api/sftp/create", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, parent_path: parentPath, name, type }),
    });
  }

  async renameSFTPNode(
    configName: string,
    configData: DatabaseConfig,
    oldPath: string,
    newName: string
  ): Promise<{ status: string; node: FileTreeNode }> {
    return this.request("/api/sftp/rename", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, old_path: oldPath, new_name: newName }),
    });
  }

  async deleteSFTPNode(
    configName: string,
    configData: DatabaseConfig,
    path: string,
    isFolder: boolean
  ): Promise<{ status: string; message: string }> {
    return this.request("/api/sftp/delete", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path, is_folder: isFolder }),
    });
  }

  async browseSFTPDirectories(
    configName: string,
    configData: DatabaseConfig,
    startPath: string = "~"
  ): Promise<{ folders: Array<{name: string; path: string}> }> {
    return this.request("/api/sftp/browse", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, start_path: startPath }),
    });
  }

  async listSFTPDirectory(
    configName: string,
    configData: DatabaseConfig,
    path: string = ""
  ): Promise<{ items: Array<{name: string; path: string; type: string; size?: number}>; current_path: string }> {
    return this.request("/api/sftp/list", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path }),
    });
  }

  async listSFTPDirectoryAbsolute(
    configName: string,
    configData: DatabaseConfig,
    path: string = "~"
  ): Promise<{ items: Array<{name: string; path: string; type: string; size?: number}>; current_path: string }> {
    return this.request("/api/sftp/list-absolute", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData, path }),
    });
  }

  async disconnectSFTP(configName: string, configData: DatabaseConfig): Promise<{ status: string }> {
    return this.request("/api/sftp/disconnect", {
      method: "POST",
      body: JSON.stringify({ config_name: configName, config_data: configData }),
    });
  }

  async searchSFTPFiles(
    configName: string,
    configData: DatabaseConfig,
    query: string,
    caseSensitive: boolean = false,
    regex: boolean = false
  ): Promise<{
    status: string;
    results: Array<{
      file: string;
      matches: Array<{
        line: number;
        column: number;
        text: string;
      }>;
    }>;
    error?: string;
  }> {
    return this.request("/api/sftp/search", {
      method: "POST",
      body: JSON.stringify({
        config_name: configName,
        config_data: configData,
        query,
        case_sensitive: caseSensitive,
        regex
      }),
    });
  }

  // Database Schema Methods
  async getDatabaseTables(configName: string): Promise<{
    status: string;
    tables: Array<{
      name: string;
      type: string;
      columns: any[];
      row_count?: number;
    }>;
    error?: string;
  }> {
    return this.request(`/api/database/${encodeURIComponent(configName)}/tables`);
  }

  async getTableSchema(configName: string, tableName: string): Promise<{
    status: string;
    table?: {
      name: string;
      type: string;
      columns: Array<{
        name: string;
        type: string;
        nullable: boolean;
        primary_key: boolean;
        default_value?: string;
        description?: string;
      }>;
      row_count?: number;
    };
    error?: string;
  }> {
    return this.request(`/api/database/${encodeURIComponent(configName)}/table/${encodeURIComponent(tableName)}/schema`);
  }

  async refreshDatabaseSchema(configName: string): Promise<{
    status: string;
    message: string;
  }> {
    return this.request(`/api/database/${encodeURIComponent(configName)}/refresh`);
  }

  async getTableData(configName: string, tableName: string, limit: number = 100): Promise<{
    status: string;
    table: string;
    rows: any[];
    count: number;
    error?: string;
  }> {
    return this.request(`/api/database/${encodeURIComponent(configName)}/table/${encodeURIComponent(tableName)}/data?limit=${limit}`);
  }

  // Lycia form operations
  async parseFM2(content: string): Promise<{
    status: string;
    form?: LyciaFormData;
    error?: string;
  }> {
    return this.request("/api/lycia/parse-fm2", {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  }

  async convertPerToFM2(content: string, formName: string): Promise<{
    status: string;
    fm2?: string;
    error?: string;
  }> {
    return this.request("/api/lycia/convert-per-to-fm2", {
      method: "POST",
      body: JSON.stringify({ content, form_name: formName }),
    });
  }
}

// Lycia form types
export interface LyciaComponent {
  type: string;
  identifier: string;
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  fieldTable?: string;
  dataType?: string;
  noEntry?: boolean;
  toCase?: string;
  isDynamic?: boolean;
  separatorType?: string;
  children?: LyciaComponent[];
}

export interface LyciaFormData {
  database?: string;
  width: number;
  height: number;
  rootContainer?: LyciaComponent;
  screenRecords?: Array<{ identifier: string; fields: string }>;
}

// Export singleton instance
export const apiClient = new APIClient();
