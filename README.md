# o° Obun
A build system that makes it easy to modularize code for any non-compiled programming language.
It lets you easily split your code into multiple snippet files you can piece together with a central `index.obun` file + the Obun CLI and build a single, perfectly compact executable script.

---

## What can you do with it?
- Organize your 1000-line prototype single-file scripts in no time
- Compile your project to a single compact file ready for distribution and execution
  - Or instantly run your Obun project without generating a file!
- Conditionally include snippets with compile-time flags
- Automatically rebuild and re-run your servers when changes are detected with watcher mode
- Add a manifest to your index file to automate build config

And guess what? it has *zero* external dependencies!

---

## How to install
Clone the repo and run `install.sh`:
```bash
git clone https://github.com/Dogo6647/obun.git
cd obun
./install.sh
```
This will automatically add obun to your PATH so you can just run it using `obun`.

---

## Get started

Here's an example of an Obun project's folder structure:

```
sample/
├── index.obun
└── src/
    └── routes.obun.py
    └── titles/
        └── default.obun.py
        └── (...)
```

### Example `index.obun`

```
0o ---
artifact-name: obun-example.py
shebang: /usr/bin/env python3
build-mode: run
--- o0

import flask
from flask import Flask

app = Flask(__name__)

#:section src/routes.obun.py

if __name__ == '__main__':
    app.run(port=8080)
```

You can build your project with:

```bash
obun sample
```

---

## Manifest

Each project can include a manifest at the top of the main file,
like this:

```
0o ---
key: value
--- o0
```

| Key             | What it does                    |
| --------------- | ------------------------------- |
| `shebang`       | Interpreter for the output file |
| `artifact-name` | Name of the generated file      |
| `build-mode`    | `run` or `prod`                 |
|                 | (prod exports a file)           |

Here's an example of a valid manifest:

```
0o ---
shebang: /usr/bin/env python3
artifact-name: server.py
build-mode: prod
--- o0
```

---

## Includes

You can use section markers to insert other files right where the marker is:

```
#:section path/to/file.obun.extension
```

Obun recursively resolves these, stitches them together, and builds a single output.

---

## Conditional Compilation

You can decide to include or not include certain sections at compile time based on
the compile flags you've set.

```
#:if DEBUG
print("Debug enabled, careful now :P")
#:else
print("Running in prod")
#:endif
```

You can define your flags via CLI:

```bash
obun -D DEBUG
```

Or even pass multiple:

```bash
obun -D DEBUG -D LOGGING
```

---

## Build Modes

### Run mode (suitable for development)

- Automatically runs the artifact
- Great for testing!

```bash
obun -B run
```

### Production mode

- Only generates the artifact
- Does not run the file after

```bash
obun -B prod
```

---

## Watcher Mode

You can automatically rebuild your project as you edit files.
When combined with run mode (`-B run`), Obun will restart your program on every change.

```bash
obun -w
```

---

## CLI arguments

The first argument is treated as the input.
If the input is:

- A file: it becomes the entry
- A directory: Obun looks for `index.obun`

After that come the flags:

| Flag | What it does               |
| ---- | -------------------------- |
| `-o` | Manual output location     |
| `-D` | Define compile-time flag   |
| `-B` | Build mode (`run`, `prod`) |
| `-w` | Watcher mode               |

Example:

```bash
obun src/index.obun -o dist.py -D DEBUG -B run -w
```


