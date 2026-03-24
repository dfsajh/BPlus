import sys
import random
import os
import time

variables = {}
types = {}
arrays = {}

enabled_funcs = set()
user_funcs = {}

lines_global = []
current_index = [0]

system_imported = False
system_verbose = False

# ------------------ SYSTEM ------------------

def system_print(msg):
    if system_verbose:
        print(f"[SYSTEM] Intilializing Interperter Code...")
        time.sleep(5)
        print(f"[SYSTEM] Running Compiler...")
        time.sleep(5)
        print(f"[SYSTEM] B+ Interperter Loaded. Coding finished.")
        print(f" ")

# ------------------ HELPERS ------------------

def is_number(x):
    try:
        float(x)
        return True
    except:
        return False

def get_val(x):
    if x in variables:
        return variables[x]
    elif is_number(x):
        return float(x)
    else:
        raise ValueError("Invalid value: " + x)

def eval_math(parts):
    stack = []
    for token in parts:
        if token in ["ad","su","mu","di"]:
            b = stack.pop()
            a = stack.pop()
            if token == "ad": stack.append(a + b)
            elif token == "su": stack.append(a - b)
            elif token == "mu": stack.append(a * b)
            elif token == "di": stack.append(a / b)
        else:
            stack.append(get_val(token))
    return stack[0]

def eval_condition(parts):
    *expr, op = parts
    right = get_val(expr[-1])
    left = eval_math(expr[:-1]) if len(expr) > 1 else get_val(expr[0])

    if op == "=": return left == right
    if op == "≠": return left != right
    if op == ">": return left > right
    if op == "<": return left < right
    if op == "<o=": return left >= right
    if op == ">o=": return left <= right

# ------------------ FILE ------------------

def filecreate(name):
    try:
        with open(name, "w") as f:
            pass
        print(f"File '{name}' created")
        system_print(f"File created: {name}")
    except Exception as e:
        print("File Error:", e)

# ------------------ BLOCK ------------------

def get_block(lines, i):
    block = []
    i += 1
    depth = 1
    while i < len(lines):
        if "{" in lines[i]: depth += 1
        if "}" in lines[i]: depth -= 1
        if depth == 0:
            break
        block.append(lines[i])
        i += 1
    return block, i

# ------------------ EXECUTE LINE ------------------

def run_line(line):
    global enabled_funcs, user_funcs, system_imported, system_verbose

    line = line.strip()
    if not line or line.startswith("#"):
        return

    # -------- TURNON --------
    if line.startswith("turnon"):
        func = line.split("(FUNC-")[1].replace(")", "")
        enabled_funcs.add(func)
        system_print(f"Enabled FUNC-{func}")
        return

    # -------- FUNCTION DEFINE --------
    if line.startswith("func "):
        name = line.split()[1]
        block, new_i = get_block(lines_global, current_index[0])
        user_funcs[name] = block
        system_print(f"Defined function: {name}")
        current_index[0] = new_i
        return

    # -------- WRITE --------
    if line.startswith("write("):
        content = line[6:-1].strip()

        if content.startswith("String(") and content.endswith(")"):
            inner = content[7:-1].strip()
            print(inner[1:-1])
        elif content in variables:
            print(variables[content])
        else:
            print("Invalid write")
        return

    # -------- VARIABLES VIEW --------
    if line == "bp-dir /w":
        print("Variables:", variables)
        system_print("Variables displayed")
        return

    # -------- FILE CREATE --------
    if line.startswith("filecreate()"):
        parts = line.split("--")
        filename = parts[1].strip().replace("o", "")
        filecreate(filename)
        return

    parts = line.split()

    # -------- ASSIGNMENT --------
    if len(parts) >= 4 and parts[2] == "=":
        name = parts[0]
        typ = parts[1]
        val = parts[3:]

        try:
            # -------- FUNC SYSTEM --------
            if val[0].startswith("(FUNC-"):
                func_name = val[0][6:-1]

                if func_name not in enabled_funcs:
                    raise ValueError("Function not enabled")

                system_print(f"Executing FUNC-{func_name}")

                if func_name == "SOUT":
                    with open(sys.argv[1]) as f:
                        print(f.read())
                    value = ""

                elif func_name in user_funcs:
                    run_block(user_funcs[func_name])
                    value = ""

                else:
                    raise ValueError("Unknown FUNC")

            # -------- RANDOM --------
            elif val[0] == "(RANDOM)":
                value = random.randint(0, 100)
                system_print("Generated random number")

            # -------- LENGTH --------
            elif val[0] == "(LEN":
                varname = val[1].replace(")", "")
                value = len(str(variables.get(varname, "")))
                system_print(f"Calculated length of {varname}")

            # -------- MATH --------
            elif any(x in ["ad","su","mu","di"] for x in val):
                value = eval_math(val)
                if typ == "Int":
                    value = int(value)

            # -------- NORMAL --------
            else:
                if typ == "Int":
                    value = int(val[0])
                elif typ == "Dcm":
                    value = float(val[0])
                elif typ == "String":
                    value = " ".join(val).strip('"')
                elif typ == "Char":
                    value = val[0][1]

            variables[name] = value
            types[name] = typ

        except Exception as e:
            print("Error:", e)

        return

# ------------------ BLOCK RUNNER ------------------

def run_block(lines):
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        current_index[0] = i

        # -------- IF --------
        if line.startswith("if "):
            cond = line[3:].replace("{","").split()
            block, i = get_block(lines, i)
            if eval_condition(cond):
                run_block(block)

        # -------- ELSE IF --------
        elif line.startswith("else if "):
            cond = line[8:].replace("{","").split()
            block, i = get_block(lines, i)
            if eval_condition(cond):
                run_block(block)

        # -------- ELSE --------
        elif line.startswith("else"):
            block, i = get_block(lines, i)
            run_block(block)

        # -------- WHILE --------
        elif line.startswith("while "):
            cond = line[6:].replace("{","").split()
            block, i = get_block(lines, i)
            while eval_condition(cond):
                run_block(block)

        # -------- REPEAT --------
        elif line.startswith("repeat"):
            times = int(line.split("(")[1].split(")")[0])
            block, i = get_block(lines, i)
            system_print(f"Repeating block {times} times")
            for _ in range(times):
                run_block(block)
            return

         # -------SETTINGS-------
        line = lines[i].strip()
        current_index[0] = i

        if line.startswith("if "):
            pass

        elif line.startswith("repeat"):
            pass

        elif line.startswith("/Settings()"):
            block, i = get_block(lines, i)

            temp_array = []

            for cmd in block:
                cmd = cmd.strip()

                if cmd.startswith("array["):
                    inside = cmd[6:-1]
                    temp_array = [int(x.strip()) for x in inside.split(",")]

                elif cmd.startswith("return array as"):
                    varname = cmd.split("as")[1].strip()
                    variables[varname] = temp_array
                    arrays[varname] = temp_array
                    system_print(f"Array stored in {varname}")

                elif cmd == "clrscreen":
                    os.system("cls")
                    system_print("Screen cleared")
        else:
            run_line(line)

        i += 1

# -------- READ FILE --------
if len(sys.argv) < 2:
    print("Usage: python interperter.py file.bp")
    exit()

try:
    with open(sys.argv[1], encoding="utf-8") as f:
        lines_global = f.readlines()
except Exception as e:
    print("FILE ERROR:", e)
    exit()

# -------- SYSTEM IMPORT --------
if not lines_global:
    print("ERROR: EMPTY FILE")
    exit()

first_line = lines_global[0].strip()

if not first_line.startswith("[SYSTEM] Import"):
    print("ERROR: SYSTEM IMPORT NOT FOUND")
    exit()

# -------- ACTIVATE SYSTEM --------
if "bp-dir /in" in first_line:
    system_imported = True
    system_verbose = True

    print("[SYSTEM] Import loaded: bp-dir")
    print("[SYSTEM] B+ Engine Ready")

# -------- BOOT SCREEN --------
import time

print("[SYSTEM] Initializing Interpreter Code...")
time.sleep(1)

print("[SYSTEM] Running Compiler...")
time.sleep(1)

print("[SYSTEM] B+ Interpreter Loaded. Coding started.")
print()

# -------- REMOVE SYSTEM LINE COMPLETELY  --------
program_lines = lines_global[1:]

# -------- RUN PROGRAM LAST --------
run_block(program_lines)



print("LINES:", lines_global)