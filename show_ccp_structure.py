#!/usr/bin/env python3
import json

# Load the .ccp file
with open("ware_print_loc.ccp") as f:
    data = json.load(f)

# Show structure without file contents
structure = {k: v for k, v in data.items() if k != "files"}
structure["files_summary"] = {"count": len(data["files"]), "types": {}, "examples": []}

# Count file types
for file in data["files"]:
    file_type = file["type"]
    structure["files_summary"]["types"][file_type] = (
        structure["files_summary"]["types"].get(file_type, 0) + 1
    )

# Show first 3 file names
for _i, file in enumerate(data["files"][:3]):
    structure["files_summary"]["examples"].append(
        {"path": file["path"], "type": file["type"], "size": len(file["content"])}
    )

print(json.dumps(structure, indent=2))
