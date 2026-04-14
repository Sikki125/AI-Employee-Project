import os
import time
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = r"E:\AI-Employee-Project"
VAULT_DIR = r"E:\My-Obsidian-Vault"
FOLDERS = ["inbox", "needs-action", "processed", "logs"]


class FileMoverHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        file_name = os.path.basename(file_path)

        # Skip the watcher itself and temporary/hidden files
        if file_name == "watcher.py" or file_name.startswith(".") or file_name.endswith(".tmp"):
            return

        # Small delay to ensure file is fully written
        time.sleep(0.5)

        # Step 1: Move file to inbox first
        inbox_path = os.path.join(VAULT_DIR, "inbox", file_name)

        try:
            # Ensure destination doesn't already exist
            if os.path.exists(inbox_path):
                print(f"File already exists in inbox: {file_name}")
                return

            shutil.move(file_path, inbox_path)
            print(f"Moved: {file_name} -> inbox")

            # Step 2: Open the file from inbox and check for URGENT
            if self._contains_urgent(inbox_path):
                needs_action_path = os.path.join(VAULT_DIR, "needs-action", file_name)
                if os.path.exists(needs_action_path):
                    print(f"File already exists in needs-action: {file_name}")
                else:
                    shutil.move(inbox_path, needs_action_path)
                    print(f"URGENT detected! Moved: {file_name} -> needs-action")
                    inbox_path = needs_action_path  # Update path for logging

            # Step 3: Create log entry with final destination
            self._create_log_entry(file_name, inbox_path)
        except Exception as e:
            print(f"Error moving {file_name}: {e}")

    def _contains_urgent(self, file_path):
        """Check if file contains 'URGENT' in its content."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return "URGENT" in content
        except Exception:
            return False

    def _create_log_entry(self, file_name, dest_path):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_filename = f"move-log-{datetime.now().strftime('%Y%m%d')}.md"
        log_path = os.path.join(VAULT_DIR, "logs", log_filename)

        # Determine folder from the actual destination path
        if "needs-action" in str(dest_path):
            folder_name = "needs-action"
        else:
            folder_name = "inbox"

        log_entry = f"## {timestamp}\n- **File:** {file_name}\n- **Moved to:** `{dest_path}`\n- **Folder:** {folder_name}\n\n"

        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing log: {e}")


def main():
    # Create vault folder structure
    for folder in FOLDERS:
        os.makedirs(os.path.join(VAULT_DIR, folder), exist_ok=True)

    print(f"Watching: {WATCH_DIR}")
    print(f"Vault structure ensured: {', '.join(FOLDERS)}")
    print("Press Ctrl+C to stop...\n")

    event_handler = FileMoverHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
