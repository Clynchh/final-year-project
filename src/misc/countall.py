import os
#count all line of text in dataset

root = "/home/corey/Uni/ThirdYr/final-year-project/data/segmented"
total_lines = 0

for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
    for filename in filenames:
        if filename.endswith(".txt"):
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    file_lines = sum(1 for _ in f)
                    print(f"{filepath}: {file_lines} lines")
                    total_lines += file_lines
            except PermissionError:
                pass

print(f"\nTotal lines: {total_lines}")