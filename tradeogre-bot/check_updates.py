#!/usr/bin/env python3
"""
Check for updates to dependencies
"""
import subprocess
import sys
import pkg_resources

def main():
    """Check for outdated packages and update them"""
    print("Checking for outdated packages...")
    
    try:
        # Get list of outdated packages
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated"],
            capture_output=True,
            text=True,
            check=True
        )
        
        outdated = result.stdout.strip().split('\n')[2:]  # Skip header rows
        
        if not outdated:
            print("All packages are up to date!")
            return
        
        print(f"Found {len(outdated)} outdated packages:")
        for package in outdated:
            print(f"  {package}")
        
        # Ask user if they want to update
        choice = input("\nDo you want to update these packages? (y/n): ").strip().lower()
        
        if choice == 'y':
            print("\nUpdating packages...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "-r", "requirements.txt"],
                check=True
            )
            print("Update complete!")
        else:
            print("Update cancelled.")
    
    except subprocess.CalledProcessError as e:
        print(f"Error checking for updates: {e}")
        print(f"Output: {e.output}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()