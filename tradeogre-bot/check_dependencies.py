#!/usr/bin/env python3
"""
Check for unused dependencies in the project
"""
import os
import sys
import importlib
import pkg_resources
import ast
from collections import defaultdict

def get_imports_from_file(file_path):
    """Extract all imports from a Python file"""
    with open(file_path, 'r') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            print(f"Syntax error in {file_path}, skipping")
            return set()
    
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    
    return imports

def get_installed_packages():
    """Get all installed packages"""
    return {pkg.key for pkg in pkg_resources.working_set}

def find_python_files(directory):
    """Find all Python files in a directory"""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    # Get directory to scan
    directory = os.getcwd()
    
    # Find all Python files
    python_files = find_python_files(directory)
    print(f"Found {len(python_files)} Python files")
    
    # Extract all imports
    all_imports = set()
    file_imports = defaultdict(set)
    
    for file_path in python_files:
        imports = get_imports_from_file(file_path)
        file_imports[file_path] = imports
        all_imports.update(imports)
    
    # Get installed packages
    installed_packages = get_installed_packages()
    
    # Find unused packages
    used_packages = {imp.lower() for imp in all_imports}
    unused_packages = installed_packages - used_packages
    
    # Print results
    print("\nImports by file:")
    for file_path, imports in file_imports.items():
        rel_path = os.path.relpath(file_path, directory)
        print(f"  {rel_path}: {', '.join(sorted(imports))}")
    
    print("\nAll imports:")
    print(', '.join(sorted(all_imports)))
    
    print("\nUnused packages:")
    for pkg in sorted(unused_packages):
        # Skip standard library and development packages
        if pkg in {'pip', 'setuptools', 'wheel', 'pkg_resources', 'pkg-resources'}:
            continue
        print(f"  {pkg}")

if __name__ == "__main__":
    main()