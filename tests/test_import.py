import sys
sys.path = ["/app/routers", "/app", "/app/shared"]
from database import get_db
import inspect
print("Signature:", inspect.signature(get_db))
print("File:", inspect.getfile(get_db))
print("Source file content (first 20 lines):")
with open(inspect.getfile(get_db)) as f:
    for i, line in enumerate(f):
        if i >= 20:
            break
        print(f"{i+1}: {line}", end="")
