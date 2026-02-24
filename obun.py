#!/usr/bin/env python3
import argparse
import tempfile
import subprocess
import time
import os
import signal
from pathlib import Path


# Obun declaration bindings
INCLUDE = "#:section"
IF = "#:if"
ELSE = "#:else"
ENDIF = "#:endif"

MANIFEST_START = "0o ---"
MANIFEST_END = "--- o0"


# ---------------- MANIFEST ---------------- #

class Manifest:
    def __init__(self):
        self.data = {}

    @classmethod
    def parse(cls, text: str):
        manifest = cls()
        inside = False
        lines = []

        for line in text.splitlines():
            stripped = line.strip()

            if stripped == MANIFEST_START:
                inside = True
                continue
            if stripped == MANIFEST_END:
                break

            if inside:
                lines.append(line)

        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                manifest.data[k.strip()] = v.strip()

        return manifest


# ---------------- ASSEMBLER ---------------- #

class CodeAssembler:
    def __init__(self, root, defines=None):
        self.root = Path(root)
        self.visited = set()
        self.defines = set(defines or [])
        self.manifest = Manifest()

    def load_manifest(self, file):
        path = (self.root / file).resolve()
        text = path.read_text(encoding="utf-8")
        self.manifest = Manifest.parse(text)

    def strip_manifest(self, text):
        output = []
        inside = False

        for line in text.splitlines(True):
            stripped = line.strip()

            if stripped == MANIFEST_START:
                inside = True
                continue
            if stripped == MANIFEST_END:
                inside = False
                continue

            if not inside:
                output.append(line)

        return "".join(output)

    def build(self, file):
        file = (self.root / file).resolve()

        if file in self.visited:
            raise RuntimeError(f"Circular include detected: {file}")

        self.visited.add(file)

        text = file.read_text(encoding="utf-8")
        text = self.strip_manifest(text)

        output = []
        skip_stack = []

        for line in text.splitlines(True):
            stripped = line.strip()

            if stripped.startswith(INCLUDE):
                if not any(skip_stack):
                    include_path = stripped.split(maxsplit=1)[1]
                    output.append(self.build(include_path))
                continue

            if stripped.startswith(IF):
                condition = stripped.split(maxsplit=1)[1]
                skip_stack.append(condition not in self.defines)
                continue

            if stripped.startswith(ELSE):
                if not skip_stack:
                    raise RuntimeError("Unmatched #:else")

                parent_skipping = any(skip_stack[:-1])
                if not parent_skipping:
                    skip_stack[-1] = not skip_stack[-1]
                continue

            if stripped.startswith(ENDIF):
                if not skip_stack:
                    raise RuntimeError("Unmatched #:endif")
                skip_stack.pop()
                continue

            if not any(skip_stack):
                output.append(line)

        return "".join(output)


# ---------------- WATCH ---------------- #

def snapshot_files(root):
    files = {}
    for p in root.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                files[p] = p.stat().st_mtime
            except FileNotFoundError:
                pass
    return files


def watch_loop(root, build_fn, cleanup_fn=None, delay=0.5):
    print("o° Watch mode active\n   Ctrl+C: Stop\n")
    last = snapshot_files(root)
    last_build = 0

    try:
        while True:
            time.sleep(delay)
            current = snapshot_files(root)

            if current != last and time.time() - last_build > 0.3:
                print("\no° Changes detected. Rebuilding...\n")
                try:
                    build_fn()
                except Exception as e:
                    print(f"!° Build failed: {e}")

                last = current
                last_build = time.time()

    except KeyboardInterrupt:
        print("\no° Stopping watcher...")
        if cleanup_fn:
            cleanup_fn()


# ---------------- INPUT ---------------- #

def resolve_input(path):
    path = Path(path or ".")

    if path.is_dir():
        index = path / "index.obun"
    else:
        index = path

    if not index.exists():
        raise FileNotFoundError(f"!° Cannot find {index}")

    root = index.parent.resolve()
    return root, index.name


# ---------------- MAIN ---------------- #

def main():
    parser = argparse.ArgumentParser(
        description="o° Obun - Modular code build system"
    )
    parser.add_argument("input", nargs="?", default=".")
    parser.add_argument("-o", "--output")
    parser.add_argument("-D", "--define", action="append")
    parser.add_argument("-B", "--build-mode", choices=["run", "prod"])
    parser.add_argument("-w", "--watch", action="store_true")

    args = parser.parse_args()

    root, input_file = resolve_input(args.input)
    assembler = CodeAssembler(root, args.define)

    running_process = None

    def stop_process():
        nonlocal running_process
        if running_process and running_process.poll() is None:
            print("o° Stopping running process...")
            try:
                os.killpg(os.getpgid(running_process.pid), signal.SIGTERM)
            except Exception:
                running_process.terminate()
            running_process = None

    def run_build():
        nonlocal running_process

        assembler.visited.clear()
        assembler.load_manifest(input_file)
        manifest = assembler.manifest.data

        result = assembler.build(input_file)

        shebang = manifest.get("shebang")
        if shebang:
            result = f"#!{shebang}\n" + result

        output = args.output or manifest.get("artifact-name", "dist.py")
        build_mode = args.build_mode or manifest.get("build-mode", "prod")

        if build_mode == "run" and not args.output:
            tmp = Path(tempfile.gettempdir()) / output
            tmp.write_text(result, encoding="utf-8")
            tmp.chmod(0o755)

            if running_process and running_process.poll() is None:
                print("o° Restarting...")
                stop_process()

            # subprocess.run(["clear"], check=False)

            print(f"o° Running {tmp}")
            running_process = subprocess.Popen(
                [str(tmp)],
                preexec_fn=os.setsid
            )

        else:
            out_path = root / output
            out_path.write_text(result, encoding="utf-8")
            print(f"o° Build complete! -> {out_path}")

    run_build()

    if args.watch:
        watch_loop(root, run_build, stop_process)


if __name__ == "__main__":
    main()
