import os
import fnmatch
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
# Add any extra files or directories you want to skip here.
# Supports wildcards like '*.log' or 'data/*'
MANUAL_IGNORES = {
    'temp_logs', 
    '*.sqlite3', 
    'tests/data/*', 
    'secret_configs',
    'package-lock.json',
    'build.css',
    'repocom.py',
    '*.md',
    'migrations',
    '*/migrations/*',
    # '*.html',
    '*.css',
    '*.js',
    '*.md',
    '*.txt',
}

# Binary/Media extensions to always skip
IGNORE_EXTENSIONS = {
    '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.svg', 
    '.pdf', '.woff', '.woff2', '.exe', '.bin', '.db', '.mp4'
}

def load_gitignore_patterns(repo_path):
    """Reads .gitignore and merges with MANUAL_IGNORES."""
    patterns = {'.git', '__pycache__', 'node_modules', 'venv', '.env'} # Hardcoded defaults
    patterns.update(MANUAL_IGNORES)
    
    gitignore_path = Path(repo_path) / '.gitignore'
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.add(line.rstrip('/'))
    return patterns

def should_ignore(path, patterns, repo_path):
    """Checks if a path matches any ignore patterns."""
    relative_path = os.path.relpath(path, repo_path)
    filename = os.path.basename(path)
    
    for pattern in patterns:
        # Check against filename, relative path, or any parent directory
        if fnmatch.fnmatch(filename, pattern) or \
           fnmatch.fnmatch(relative_path, pattern) or \
           any(fnmatch.fnmatch(part, pattern) for part in Path(relative_path).parts):
            return True
    return False

def generate_tree(startpath, patterns, repo_path, prefix=""):
    """Generates a visual tree structure respecting all ignore patterns."""
    tree_str = ""
    try:
        contents = sorted(os.listdir(startpath))
    except PermissionError:
        return ""

    items = [item for item in contents if not should_ignore(os.path.join(startpath, item), patterns, repo_path)]
    
    for i, item in enumerate(items):
        path = os.path.join(startpath, item)
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        
        tree_str += f"{prefix}{connector}{item}\n"
        
        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            tree_str += generate_tree(path, patterns, repo_path, prefix + extension)
    return tree_str

def convert_repo_to_text(repo_path, output_file):
    repo_path = os.path.abspath(repo_path)
    patterns = load_gitignore_patterns(repo_path)
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("REPOSITORY STRUCTURE:\n")
        out.write("=" * 30 + "\n")
        out.write(generate_tree(repo_path, patterns, repo_path))
        out.write("\n" + "=" * 30 + "\n\n")
        
        for root, dirs, files in os.walk(repo_path):
            # Prune directories to keep the walk efficient
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), patterns, repo_path)]
            
            for file in sorted(files):
                full_path = os.path.join(root, file)
                
                # Check patterns and extensions
                if should_ignore(full_path, patterns, repo_path) or \
                   any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                    continue
                
                relative_path = os.path.relpath(full_path, repo_path)
                
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    out.write(f"--- FILE: {relative_path} ---\n")
                    out.write(f"```{Path(file).suffix.lstrip('.')}\n")
                    out.write(content)
                    out.write("\n```\n\n")
                except (UnicodeDecodeError, PermissionError):
                    # Silently skip binaries or protected files
                    continue

if __name__ == "__main__":
    # You can specify a different folder path here if needed
    convert_repo_to_text('.', 'repo.txt')
    print("Successfully compiled repository into 'repo.txt'")