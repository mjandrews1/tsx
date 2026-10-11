#!/usr/bin/env python3
"""Create tsx_nat_index (PK-only) for nat_key lookup without secondary indexes."""
import subprocess, sys
DB = sys.argv[1] if len(sys.argv) > 1 else "testdb"

def q(sql):
    p = subprocess.run(["cdb2sql", DB, "local", sql], capture_output=True, text=True)
    print(sql[:70], "->", p.returncode, (p.stderr or p.stdout)[:80])
    return p.returncode

q("CREATE TABLE tsx_nat_index (id INTEGER PRIMARY KEY, stream_id TEXT, nat_key TEXT, obs_id INTEGER)")
print("created tsx_nat_index")
