import os
import shutil
import json
from pathlib import Path
from backend.core.gemini_client import ask_gemini

SYSTEM_PROMPT = """You are a helpful File System Automator agent.
Your goal is to parse the user's natural language command into a structured list of file system operations to execute.
Return ONLY valid JSON. The JSON should be a dictionary with a key "operations", mapped to a list of operation objects.

Supported actions:
1. create
   Format: {"action": "create", "type": "folder" | "file", "path": "<absolute or relative path>"}
2. search
   Format: {"action": "search", "query": "<file name or extension pattern>", "directory": "<directory to search in>"}
   Note: if no directory is specified by the user, use "." (current directory).
3. move
   Format: {"action": "move", "source": "<file or folder path>", "destination": "<target folder path>"}
4. organize
   Format: {"action": "organize", "directory": "<directory to organize>"}
   Note: this will automatically group files by extension in the target directory.
5. delete
   Format: {"action": "delete", "target": "<file or folder path>"}
   Note: will permanently delete the specified file or folder. Use with caution.

Example Output:
```json
{
    "operations": [
        {"action": "create", "type": "folder", "path": "./my_folder"}
    ]
}
```

If the user requests an action that is NOT supported (like 'select' or 'hack'), or you don't have enough context, you MUST still return valid JSON indicating an error:
```json
{
    "error": "The requested action is not supported or lacks context."
}
```
"""

async def fs_agent(user_input: str) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nUser natural language command:\n{user_input}"
    response_text = await ask_gemini(prompt)
    
    clean_text = response_text.replace("```json", "").replace("```", "").strip()
    
    output = []
    
    try:
        data = json.loads(clean_text)
        
        if "error" in data:
            return f"Error: {data['error']}"
            
        operations = data.get("operations", [])
        if not operations:
            return "Could not extract any valid file system operations from your input."
        
        for op in operations:
            action = op.get("action")
            res_str = f"[Executing] {action.upper()}: {json.dumps(op)}\n"
            try:
                if action == "create":
                    target = Path(op.get("path"))
                    op_type = op.get("type", "folder")
                    if op_type == "folder":
                        target.mkdir(parents=True, exist_ok=True)
                        res_str += f"  -> Created folder at {target.resolve()}"
                    elif op_type == "file":
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.touch(exist_ok=True)
                        res_str += f"  -> Created file at {target.resolve()}"
                        
                elif action == "search":
                    directory = Path(op.get("directory", "."))
                    query = op.get("query", "")
                    res_str += f"  -> Searching for '{query}' in {directory.resolve()}...\n"
                    found = False
                    for path in directory.rglob(f"*{query}*"):
                        res_str += f"     Found: {path.resolve()}\n"
                        found = True
                    if not found:
                        res_str += "     No matching files found."
                        
                elif action == "move":
                    source = Path(op.get("source"))
                    destination = Path(op.get("destination"))
                    if not source.exists():
                        res_str += f"  -> [Error] Source {source.resolve()} does not exist."
                    else:
                        destination.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(source), str(destination / source.name))
                        res_str += f"  -> Moved {source.name} to {destination.resolve()}"
                        
                elif action == "organize":
                    directory = Path(op.get("directory", "."))
                    if not directory.exists() or not directory.is_dir():
                        res_str += f"  -> [Error] Directory {directory.resolve()} is invalid."
                    else:
                        res_str += f"  -> Organizing directory {directory.resolve()}...\n"
                        moved_count = 0
                        for item in directory.iterdir():
                            if item.is_file():
                                ext = item.suffix.strip('.').lower()
                                if not ext:
                                    ext = "others"
                                target_folder = directory / ext.capitalize()
                                target_folder.mkdir(exist_ok=True)
                                shutil.move(str(item), str(target_folder / item.name))
                                moved_count += 1
                        res_str += f"  -> Organized {moved_count} files."
                
                elif action == "delete":
                    target = Path(op.get("target"))
                    if not target.exists():
                        res_str += f"  -> [Error] Target {target.resolve()} does not exist."
                    else:
                        if target.is_dir():
                            shutil.rmtree(target)
                            res_str += f"  -> Deleted folder {target.resolve()}"
                        else:
                            target.unlink()
                            res_str += f"  -> Deleted file {target.resolve()}"
                else:
                    res_str += f"  -> [Error] Unknown action: {action}"
            except Exception as e:
                res_str += f"  -> [Error] Failed to execute {action}: {e}"
                
            output.append(res_str)
            
        return "\n".join(output)
    except json.JSONDecodeError:
        return f"Error understanding the command. Raw Response: {response_text}"
