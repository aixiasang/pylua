#!/usr/bin/env python3
"""
Debug constant table differences

Based on Lua 5.3.6 official implementation.
Author: aixiasang
"""
import sys
import os
import subprocess
import tempfile
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pylua.compile import pylua_compile

def get_pylua_constants(source):
    cp, error = pylua_compile(source)
    if error:
        print(f"Error: {error}")
        return []
    

    result = []
    for idx, val in cp.constants:

        if isinstance(val, str):
            result.append((idx, val))
        elif isinstance(val, int):
            result.append((idx, str(val)))
        elif isinstance(val, float):
            result.append((idx, str(val)))
        else:
            result.append((idx, str(val)[:40]))
    return result

def get_lua_constants(source):
    """Get constant table from luac53 -l -l"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', 
                                     delete=False, encoding='utf-8') as f:
        f.write(source)
        src_file = f.name
    
    try:
        result = subprocess.run(
            ['luac53', '-l', '-l', src_file],
            capture_output=True,
            timeout=10,
            text=True
        )
        
        constants = []
        in_constants = False

        for line in result.stdout.split('\n'):
            if 'constants (' in line and ') for' in line:
                in_constants = True
                continue
            if 'locals (' in line or 'upvalues (' in line:
                in_constants = False
                continue
            if in_constants:
                line = line.strip()
                if line:

                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].strip().isdigit():
                        idx = int(parts[0].strip())
                        val = '\t'.join(parts[1:])
                        constants.append((idx, val))
        return constants
    except Exception as e:
        print(f"Lua error: {e}")
        return []
    finally:
        os.unlink(src_file)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            source = f.read()
    else:
        source = "print('test'); local x = 0"
    
    print("=== Lua Constants ===")
    lua_k = get_lua_constants(source)
    for idx, val in lua_k[:30]:
        print(f"  {idx}: {val}")
    
    print("\n=== PyLua Constants ===")
    pylua_k = get_pylua_constants(source)
    for idx, val in pylua_k[:30]:
        print(f"  {idx}: {val}")
    
    print("\n=== Differences ===")
    max_len = max(len(lua_k), len(pylua_k))
    for i in range(min(max_len, 30)):
        l = lua_k[i] if i < len(lua_k) else (i, "MISSING")
        p = pylua_k[i] if i < len(pylua_k) else (i, "MISSING")
        if l[1] != p[1]:
            print(f"  {i}: Lua={l[1]}, PyLua={p[1]}")
