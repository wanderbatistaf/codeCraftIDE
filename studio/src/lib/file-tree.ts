export type FileTreeNode = {
  id: string;
  name: string;
  type: "file" | "folder";
  children?: FileTreeNode[];
  content?: string; // For files
  path: string; // Full path from root
};

// Initial sample file tree structure
export const initialFileTree: FileTreeNode = {
  id: "root",
  name: "project",
  type: "folder",
  path: "/",
  children: [
    {
      id: "src",
      name: "src",
      type: "folder",
      path: "/src",
      children: [
        {
          id: "src/app",
          name: "app",
          type: "folder",
          path: "/src/app",
          children: [
            {
              id: "src/app/page.tsx",
              name: "page.tsx",
              type: "file",
              path: "/src/app/page.tsx",
              content: `export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1>Welcome to Studio IDE</h1>
    </main>
  );
}`,
            },
            {
              id: "src/app/layout.tsx",
              name: "layout.tsx",
              type: "file",
              path: "/src/app/layout.tsx",
              content: `export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}`,
            },
          ],
        },
        {
          id: "src/components",
          name: "components",
          type: "folder",
          path: "/src/components",
          children: [
            {
              id: "src/components/button.tsx",
              name: "button.tsx",
              type: "file",
              path: "/src/components/button.tsx",
              content: `export function Button() {
  return <button>Click me</button>;
}`,
            },
          ],
        },
      ],
    },
    {
      id: "public",
      name: "public",
      type: "folder",
      path: "/public",
      children: [
        {
          id: "public/README.md",
          name: "README.md",
          type: "file",
          path: "/public/README.md",
          content: "# Public Assets\n\nPlace your static assets here.",
        },
      ],
    },
    {
      id: "package.json",
      name: "package.json",
      type: "file",
      path: "/package.json",
      content: `{
  "name": "studio-ide",
  "version": "1.0.0",
  "description": "A JetBrains-style IDE"
}`,
    },
    {
      id: "README.md",
      name: "README.md",
      type: "file",
      path: "/README.md",
      content: "# Studio IDE\n\nA modern web-based IDE with JetBrains-style layout.",
    },
  ],
};

// Utility functions for working with the file tree
export function findNodeByPath(
  tree: FileTreeNode,
  path: string
): FileTreeNode | null {
  if (tree.path === path) return tree;

  if (tree.children) {
    for (const child of tree.children) {
      const found = findNodeByPath(child, path);
      if (found) return found;
    }
  }

  return null;
}

export function findNodeById(
  tree: FileTreeNode,
  id: string
): FileTreeNode | null {
  if (tree.id === id) return tree;

  if (tree.children) {
    for (const child of tree.children) {
      const found = findNodeById(child, id);
      if (found) return found;
    }
  }

  return null;
}

export function generateId(path: string): string {
  return path.replace(/^\//, "").replace(/\/$/, "");
}

export function getParentPath(path: string): string {
  const parts = path.split("/").filter(Boolean);
  parts.pop();
  return "/" + parts.join("/");
}

export function addNodeToTree(
  tree: FileTreeNode,
  parentPath: string,
  newNode: FileTreeNode
): FileTreeNode {
  if (tree.path === parentPath) {
    return {
      ...tree,
      children: [...(tree.children || []), newNode].sort((a, b) => {
        // Folders first, then files
        if (a.type !== b.type) {
          return a.type === "folder" ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      }),
    };
  }

  if (tree.children) {
    return {
      ...tree,
      children: tree.children.map((child) =>
        addNodeToTree(child, parentPath, newNode)
      ),
    };
  }

  return tree;
}

export function removeNodeFromTree(
  tree: FileTreeNode,
  nodeId: string
): FileTreeNode {
  if (tree.id === nodeId) {
    throw new Error("Cannot remove root node");
  }

  return {
    ...tree,
    children: tree.children
      ?.filter((child) => child.id !== nodeId)
      .map((child) => removeNodeFromTree(child, nodeId)),
  };
}

export function updateNodeInTree(
  tree: FileTreeNode,
  nodeId: string,
  updates: Partial<FileTreeNode>
): FileTreeNode {
  if (tree.id === nodeId) {
    return { ...tree, ...updates };
  }

  if (tree.children) {
    return {
      ...tree,
      children: tree.children.map((child) =>
        updateNodeInTree(child, nodeId, updates)
      ),
    };
  }

  return tree;
}

export function getAllFiles(tree: FileTreeNode): FileTreeNode[] {
  const files: FileTreeNode[] = [];

  if (tree.type === "file") {
    files.push(tree);
  }

  if (tree.children) {
    for (const child of tree.children) {
      files.push(...getAllFiles(child));
    }
  }

  return files;
}
