import re
import sys
import os

def extract_logs():
    log_file = "LightRAG/lightrag.log"
    if not os.path.exists(log_file):
        print(f"Log file not found at {log_file}")
        return

    pattern = r"\[Frontend\] \[DeleteDocumentsDialog\]"
    
    print(f"Scanning {log_file} for '{pattern}'...")
    found = False
    with open(log_file, 'r') as f:
        for line in f:
            if re.search(pattern, line):
                print(line.strip())
                found = True
    
    if not found:
        print("No matching logs found.")

if __name__ == "__main__":
    extract_logs()
