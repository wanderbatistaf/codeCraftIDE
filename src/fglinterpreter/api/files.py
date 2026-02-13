"""
File management API endpoints for the fglInterpreter IDE.

Provides CRUD operations for files and folders in the workspace.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Auth imports
from .auth.config import auth_config
from .auth.core.permissions import Permission, require_permission
from .auth.dependencies.auth_deps import get_current_user_optional
from .auth.models import CurrentUser

router = APIRouter(prefix="/api/files", tags=["files"])

# Workspace directory for file storage
WORKSPACE_DIR = Path("workspace")
WORKSPACE_DIR.mkdir(exist_ok=True)

# File tree state file
FILE_TREE_STATE = WORKSPACE_DIR / ".filetree.json"


class FileNode(BaseModel):
    """File or folder node in the tree."""

    id: str
    name: str
    type: str = Field(..., pattern="^(file|folder)$")
    path: str
    content: Optional[str] = None
    children: Optional[List["FileNode"]] = None


class FileTreeResponse(BaseModel):
    """Response model for file tree."""

    tree: FileNode


class FileContentRequest(BaseModel):
    """Request model for creating/updating file content."""

    path: str
    content: str


class CreateNodeRequest(BaseModel):
    """Request model for creating a file or folder."""

    parentPath: str
    name: str
    type: str = Field(..., pattern="^(file|folder)$")


class RenameNodeRequest(BaseModel):
    """Request model for renaming a file or folder."""

    oldPath: str
    newName: str


class DeleteNodeRequest(BaseModel):
    """Request model for deleting a file or folder."""

    path: str


class SearchFilesRequest(BaseModel):
    """Request model for searching files."""

    query: str
    case_sensitive: bool = False
    regex: bool = False


class SearchMatch(BaseModel):
    """Model for a search match."""

    line: int
    column: int
    text: str


class SearchFileResult(BaseModel):
    """Model for search results in a file."""

    file: str
    matches: List[SearchMatch]


class SearchFilesResponse(BaseModel):
    """Response model for file search."""

    status: str
    results: List[SearchFileResult]
    error: Optional[str] = None


def load_file_tree() -> FileNode:
    """Load file tree from state file or create default."""
    if FILE_TREE_STATE.exists():
        try:
            data = json.loads(FILE_TREE_STATE.read_text(encoding="utf-8"))
            return FileNode(**data)
        except Exception:
            pass

    # Create default tree with example projects
    default_tree = FileNode(
        id="root",
        name="workspace",
        type="folder",
        path="/",
        children=[
            FileNode(
                id="examples",
                name="examples",
                type="folder",
                path="/examples",
                children=[
                    FileNode(
                        id="examples/hello.4gl",
                        name="hello.4gl",
                        type="file",
                        path="/examples/hello.4gl",
                        content="""MAIN
    DISPLAY "Hello, World!"
    DISPLAY "Welcome to the 4GL Interpreter!"
END MAIN""",
                    ),
                    FileNode(
                        id="examples/variables.4gl",
                        name="variables.4gl",
                        type="file",
                        path="/examples/variables.4gl",
                        content="""MAIN
    DEFINE name STRING
    DEFINE age INTEGER
    DEFINE salary DECIMAL(10,2)

    LET name = "John Doe"
    LET age = 30
    LET salary = 75000.50

    DISPLAY "Name: ", name
    DISPLAY "Age: ", age
    DISPLAY "Salary: $", salary
END MAIN""",
                    ),
                    FileNode(
                        id="examples/loops.4gl",
                        name="loops.4gl",
                        type="file",
                        path="/examples/loops.4gl",
                        content="""MAIN
    DEFINE i INTEGER

    DISPLAY "Counting from 1 to 5:"
    FOR i = 1 TO 5
        DISPLAY "Count: ", i
    END FOR

    DISPLAY ""
    DISPLAY "Countdown from 5 to 1:"
    LET i = 5
    WHILE i > 0
        DISPLAY "Count: ", i
        LET i = i - 1
    END WHILE
END MAIN""",
                    ),
                    FileNode(
                        id="examples/stores_demo_query.4gl",
                        name="stores_demo_query.4gl",
                        type="file",
                        path="/examples/stores_demo_query.4gl",
                        content="""-- stores_demo_query.4gl
-- Simple query example using Informix stores_demo database
-- Perfect for testing database connectivity

MAIN
    DEFINE cust_num INTEGER
    DEFINE fname CHAR(15)
    DEFINE lname CHAR(15)
    DEFINE city CHAR(15)
    DEFINE state CHAR(2)
    DEFINE count_result INTEGER

    DISPLAY "=== Stores Demo Database Query ==="
    DISPLAY ""

    -- Example 1: Simple count query
    SELECT COUNT(*) INTO count_result
    FROM customer

    DISPLAY "Total customers in database: ", count_result
    DISPLAY ""

    -- Example 2: Select specific customer
    DISPLAY "Sample Customer (Customer #101):"
    DISPLAY "--------------------------------"

    SELECT customer_num, fname, lname, city, state
    INTO cust_num, fname, lname, city, state
    FROM customer
    WHERE customer_num = 101

    DISPLAY "Customer Number: ", cust_num
    DISPLAY "Name: ", fname, " ", lname
    DISPLAY "Location: ", city, ", ", state
    DISPLAY ""

    -- Example 3: List first 5 customers
    DISPLAY "First 5 Customers:"
    DISPLAY "--------------------------------"

    DECLARE cust_cursor CURSOR FOR
        SELECT FIRST 5 customer_num, fname, lname, city, state
        FROM customer
        ORDER BY customer_num

    FOREACH cust_cursor INTO cust_num, fname, lname, city, state
        DISPLAY cust_num, " | ", fname, " ", lname, " | ", city, ", ", state
    END FOREACH

    CLOSE cust_cursor

    DISPLAY ""
    DISPLAY "=== Query Complete ==="

END MAIN""",
                    ),
                    FileNode(
                        id="examples/customer_report.4gl",
                        name="customer_report.4gl",
                        type="file",
                        path="/examples/customer_report.4gl",
                        content="""-- customer_report.4gl
-- Demonstrates cursor loops with real Informix stores_demo database
-- This example connects to the Docker Informix container and queries
-- the pre-installed stores_demo database

MAIN
    DEFINE cust_num INTEGER
    DEFINE fname CHAR(15)
    DEFINE lname CHAR(15)
    DEFINE company CHAR(20)
    DEFINE city CHAR(15)
    DEFINE state CHAR(2)
    DEFINE order_num INTEGER
    DEFINE order_date DATE
    DEFINE ship_date DATE
    DEFINE customer_count INTEGER
    DEFINE total_orders INTEGER

    DISPLAY "=== Customer Orders Report ==="
    DISPLAY "Using stores_demo database on Docker Informix"
    DISPLAY ""

    -- Initialize counters
    LET customer_count = 0
    LET total_orders = 0

    -- Main cursor: Get customers from California
    DISPLAY "California Customers and Their Orders:"
    DISPLAY "========================================"
    DISPLAY ""

    DECLARE customer_cursor CURSOR FOR
        SELECT customer_num, fname, lname, company, city, state
        FROM customer
        WHERE state = "CA"
        ORDER BY lname, fname

    FOREACH customer_cursor INTO cust_num, fname, lname, company, city, state
        LET customer_count = customer_count + 1

        DISPLAY "Customer #", cust_num, ": ", fname, " ", lname
        DISPLAY "  Company: ", company
        DISPLAY "  Location: ", city, ", ", state
        DISPLAY "  Orders:"

        -- Nested cursor: Get orders for this customer
        DECLARE order_cursor CURSOR FOR
            SELECT order_num, order_date, ship_date
            FROM orders
            WHERE customer_num = cust_num
            ORDER BY order_date DESC

        FOREACH order_cursor INTO order_num, order_date, ship_date
            DISPLAY "    Order #", order_num
            DISPLAY "      Date: ", order_date
            IF ship_date IS NOT NULL THEN
                DISPLAY "      Shipped: ", ship_date
            ELSE
                DISPLAY "      Status: Not yet shipped"
            END IF

            LET total_orders = total_orders + 1
        END FOREACH

        CLOSE order_cursor

        DISPLAY ""
    END FOREACH

    CLOSE customer_cursor

    -- Display summary
    DISPLAY "========================================"
    DISPLAY "Summary:"
    DISPLAY "  Total CA Customers: ", customer_count
    DISPLAY "  Total Orders: ", total_orders
    DISPLAY ""
    DISPLAY "=== Report Complete ==="

END MAIN""",
                    ),
                ],
            ),
            FileNode(
                id="README.md",
                name="README.md",
                type="file",
                path="/README.md",
                content="""# 4GL Workspace

Welcome to the 4GL Interpreter IDE!

## Getting Started

1. Open a file from the `examples` folder to see sample code
2. Edit the code in the editor
3. Click the "Run" button to execute your 4GL code
4. View the output in the console below

## Example Files

### Basic Examples
- **hello.4gl**: Simple Hello World program
- **variables.4gl**: Working with variables and data types
- **loops.4gl**: FOR and WHILE loop examples

### Database Examples (Requires Informix Connection)
- **stores_demo_query.4gl**: Simple database queries with cursors
- **customer_report.4gl**: Advanced report with nested cursor loops

## Using Database Examples

1. Click **Database** in the menu bar
2. Select **"Docker Informix (Sample)"** connection
3. Open a database example file
4. Click **Run** - the code will automatically use the active connection

The Informix container includes the `stores_demo` database with sample customer and order data.

## Creating New Files

- Click the "+" icon in the file explorer
- Or use the File menu → New File

Happy coding!
""",
            ),
        ],
    )

    save_file_tree(default_tree)
    return default_tree


def save_file_tree(tree: FileNode):
    """Save file tree to state file."""
    # Use model_dump_json for Pydantic v2 compatibility
    try:
        json_str = tree.model_dump_json(indent=2)
    except AttributeError:
        # Fallback for Pydantic v1
        json_str = tree.json(indent=2)
    FILE_TREE_STATE.write_text(json_str, encoding="utf-8")


def find_node_by_path(tree: FileNode, path: str) -> Optional[FileNode]:
    """Find a node by its path."""
    if tree.path == path:
        return tree

    if tree.children:
        for child in tree.children:
            result = find_node_by_path(child, path)
            if result:
                return result

    return None


def update_node_in_tree(tree: FileNode, path: str, updates: Dict) -> FileNode:
    """Update a node in the tree."""
    if tree.path == path:
        for key, value in updates.items():
            setattr(tree, key, value)
        return tree

    if tree.children:
        tree.children = [update_node_in_tree(child, path, updates) for child in tree.children]

    return tree


def add_node_to_tree(tree: FileNode, parent_path: str, new_node: FileNode) -> FileNode:
    """Add a new node to the tree."""
    if tree.path == parent_path:
        if not tree.children:
            tree.children = []
        tree.children.append(new_node)
        # Sort: folders first, then files
        tree.children.sort(key=lambda n: (n.type != "folder", n.name.lower()))
        return tree

    if tree.children:
        tree.children = [add_node_to_tree(child, parent_path, new_node) for child in tree.children]

    return tree


def remove_node_from_tree(tree: FileNode, path: str) -> FileNode:
    """Remove a node from the tree."""
    if tree.path == path:
        raise HTTPException(status_code=400, detail="Cannot remove root node")

    if tree.children:
        tree.children = [child for child in tree.children if child.path != path]
        tree.children = [remove_node_from_tree(child, path) for child in tree.children]

    return tree


@router.get("/tree", response_model=FileTreeResponse)
async def get_file_tree(
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Get the complete file tree.

    Returns:
        FileTreeResponse with the complete workspace structure
    """
    try:
        tree = load_file_tree()
        return FileTreeResponse(tree=tree)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load file tree: {str(e)}")


@router.get("/content")
async def get_file_content(
    path: str,
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Get content of a specific file.

    Args:
        path: File path
        current_user: Current authenticated user (optional)

    Returns:
        File content
    """
    try:
        tree = load_file_tree()
        node = find_node_by_path(tree, path)

        if not node:
            raise HTTPException(status_code=404, detail="File not found")

        if node.type != "file":
            raise HTTPException(status_code=400, detail="Path is not a file")

        return {"path": path, "content": node.content or ""}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.post("/content")
async def save_file_content(
    request: FileContentRequest,
    current_user: CurrentUser = Depends(
        require_permission(Permission.WRITE_FILES)
        if auth_config.enabled
        else get_current_user_optional
    ),
):
    """
    Save file content.

    Requires FILE_WRITE permission (Developer or Admin role).

    Args:
        request: File content update request
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Success status
    """
    try:
        tree = load_file_tree()
        node = find_node_by_path(tree, request.path)

        if not node:
            raise HTTPException(status_code=404, detail="File not found")

        if node.type != "file":
            raise HTTPException(status_code=400, detail="Path is not a file")

        # Update content
        tree = update_node_in_tree(tree, request.path, {"content": request.content})
        save_file_tree(tree)

        return {"status": "success", "message": "File saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")


@router.post("/create")
async def create_node(
    request: CreateNodeRequest,
    current_user: CurrentUser = Depends(
        require_permission(Permission.CREATE_FILES)
        if auth_config.enabled
        else get_current_user_optional
    ),
):
    """
    Create a new file or folder.

    Requires FILE_CREATE permission (Developer or Admin role).

    Args:
        request: Node creation request
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Created node
    """
    try:
        tree = load_file_tree()

        # Generate path and ID
        new_path = f"{request.parentPath.rstrip('/')}/{request.name}"
        if request.parentPath == "/":
            new_path = f"/{request.name}"

        new_id = new_path.lstrip("/")

        # Check if already exists
        if find_node_by_path(tree, new_path):
            raise HTTPException(status_code=409, detail="File or folder already exists")

        # Create new node
        new_node = FileNode(
            id=new_id,
            name=request.name,
            type=request.type,
            path=new_path,
            content="" if request.type == "file" else None,
            children=[] if request.type == "folder" else None,
        )

        # Add to tree
        tree = add_node_to_tree(tree, request.parentPath, new_node)
        save_file_tree(tree)

        return {"status": "success", "node": new_node}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create node: {str(e)}")


@router.post("/rename")
async def rename_node(
    request: RenameNodeRequest,
    current_user: CurrentUser = Depends(
        require_permission(Permission.RENAME_FILES)
        if auth_config.enabled
        else get_current_user_optional
    ),
):
    """
    Rename a file or folder.

    Requires FILE_WRITE permission (Developer or Admin role).

    Args:
        request: Rename request
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Updated node
    """
    try:
        tree = load_file_tree()
        node = find_node_by_path(tree, request.oldPath)

        if not node:
            raise HTTPException(status_code=404, detail="File or folder not found")

        # Generate new path
        parent_path = "/".join(request.oldPath.rstrip("/").split("/")[:-1]) or "/"
        new_path = f"{parent_path.rstrip('/')}/{request.newName}"
        if parent_path == "/":
            new_path = f"/{request.newName}"

        new_id = new_path.lstrip("/")

        # Update node
        tree = update_node_in_tree(
            tree,
            request.oldPath,
            {
                "name": request.newName,
                "path": new_path,
                "id": new_id,
            },
        )
        save_file_tree(tree)

        updated_node = find_node_by_path(tree, new_path)
        return {"status": "success", "node": updated_node}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename node: {str(e)}")


@router.post("/delete")
async def delete_node(
    request: DeleteNodeRequest,
    current_user: CurrentUser = Depends(
        require_permission(Permission.DELETE_FILES)
        if auth_config.enabled
        else get_current_user_optional
    ),
):
    """
    Delete a file or folder.

    Requires FILE_DELETE permission (Developer or Admin role).

    Args:
        request: Delete request
        current_user: Current authenticated user (required if auth enabled)

    Returns:
        Success status
    """
    try:
        tree = load_file_tree()
        node = find_node_by_path(tree, request.path)

        if not node:
            raise HTTPException(status_code=404, detail="File or folder not found")

        # Remove from tree
        tree = remove_node_from_tree(tree, request.path)
        save_file_tree(tree)

        return {"status": "success", "message": "Node deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete node: {str(e)}")


def search_in_node(
    node: FileNode, query: str, case_sensitive: bool, use_regex: bool
) -> List[SearchFileResult]:
    """
    Recursively search for text in files.

    Args:
        node: File tree node to search
        query: Search query
        case_sensitive: Whether search is case-sensitive
        use_regex: Whether to use regex matching

    Returns:
        List of search results
    """
    results = []

    if node.type == "file" and node.content:
        matches = []
        lines = node.content.split("\n")

        for line_num, line_text in enumerate(lines, start=1):
            # Prepare search pattern
            if use_regex:
                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    pattern = re.compile(query, flags)
                except re.error:
                    # Invalid regex, skip this file
                    continue
            else:
                # Escape special regex characters for literal search
                escaped_query = re.escape(query)
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(escaped_query, flags)

            # Search for matches in the line
            for match in pattern.finditer(line_text):
                matches.append(
                    SearchMatch(line=line_num, column=match.start() + 1, text=line_text.strip())
                )

        if matches:
            results.append(SearchFileResult(file=node.path, matches=matches))

    # Recursively search children
    if node.children:
        for child in node.children:
            results.extend(search_in_node(child, query, case_sensitive, use_regex))

    return results


@router.post("/search", response_model=SearchFilesResponse)
async def search_files(
    request: SearchFilesRequest,
    current_user: CurrentUser = Depends(get_current_user_optional),
):
    """
    Search for text across all files in the workspace.

    Args:
        request: Search request with query and options
        current_user: Current authenticated user (optional)

    Returns:
        Search results with file paths and matching lines
    """
    try:
        if not request.query.strip():
            return SearchFilesResponse(status="error", results=[], error="Empty search query")

        tree = load_file_tree()
        results = search_in_node(tree, request.query, request.case_sensitive, request.regex)

        return SearchFilesResponse(status="success", results=results)

    except Exception as e:
        return SearchFilesResponse(status="error", results=[], error=str(e))


# Update forward references
FileNode.model_rebuild()
