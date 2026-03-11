# **gradescope-fake-assignment**

Create a dummy PDF template and a combined PDF of submissions from a class roster. Each student has a submission with their name on it, otherwise identical to the template. This makes it easy to provide grades within Gradescope for assignments that do not otherwise have submissions.

---

## **Quick Start**

### **1. Sync Dependencies (Developers)**
Use `uv` to create/update the project environment:
```bash
make sync
```

---

### **2. Run Quality Checks**
Run linting, type-checking, and smoke checks:
```bash
make check
```

Run only the built-in smoke checks against sample roster inputs:
```bash
make test
```

This validates a successful roster run and malformed-roster error handling.

---

### **3. Build the Executable**
Create a standalone executable with PyInstaller:
```bash
make build
```

The executable will be created in `./dist/` as `gradescope_fake_assignment`.
Users can run that binary directly on the same OS/architecture without setting up `uv`, a virtual environment, or project dependencies.

---

### **4. Install the Executable**
Install the executable to `/usr/local/bin` for system-wide use:
```bash
make install
```

Once installed, you can run the program directly:
```bash
gradescope_fake_assignment "Assignment 1" ./tests/resources/test-roster.csv --format standard --output_dir ./output
```

---

### **5. Clean Up**
Remove all temporary files, build artifacts, and cache:
```bash
make clean
```

This cleans:
- `build/` and `dist/` directories
- Python cache files (`__pycache__/`, `*.pyc`, etc.)
- QA caches (e.g., `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`)
- Temporary outputs (`output/` directory)

---

## **Development Instructions**

For developers who need to work with the project directly:

### **1. Sync the Environment**
The project uses `uv` for dependency and environment management. Sync dependencies with:
```bash
uv sync --python 3.13
```

### **2. Manual Execution**
If you need to run the program manually (e.g., without building the executable):
```bash
uv run --python 3.13 python -m gradescope_fake_assignment "Assignment 1" ./tests/resources/test-roster.csv --format standard --output_dir ./output
```

### **3. Manual Build**
To manually create the executable without `make`:
```bash
uv run --python 3.13 pyinstaller --onefile src/gradescope_fake_assignment/__main__.py --name gradescope_fake_assignment
```

The executable will be created in the `./dist/` directory.

### **4. Manual Installation**
To install manually without `make`:
```bash
sudo mv ./dist/gradescope_fake_assignment /usr/local/bin/
```

### **5. Manual Quality/Test Commands**

```bash
make format
make lint
make lint-fix
make typecheck
make test
make coverage
make check
```

### **Examples**
1. Run the program with a valid test roster:
   ```bash
   uv run --python 3.13 python -m gradescope_fake_assignment "Assignment 1" ./tests/resources/test-roster.csv --format standard --output_dir ./output
   ```

2. Run with a malformed roster file to test error handling:
   ```bash
   uv run --python 3.13 python -m gradescope_fake_assignment "Assignment 1" ./tests/resources/test-roster-bad-columns.csv --format standard --output_dir ./output
   ```

---

## **Directory Structure**
Here’s an overview of the project layout:

```plaintext
project-root/
├── Makefile              # Sync, smoke-test, build, install, and clean tasks
├── README.md             # Project documentation
├── pyproject.toml        # Dependency and project configuration
├── uv.lock               # Dependency lock file
├── src/
│   └── gradescope_fake_assignment/
│       ├── __init__.py
│       └── __main__.py
├── tests/
│   ├── resources/
│   │   ├── test-roster.csv
│   │   ├── bad-file-invalid.csv
│   │   └── test-roster-bad-columns.csv
│   └── __init__.py
├── dist/                 # Generated executables (ignored by git)
├── output/               # Temporary output files (ignored by git)
├── build/                # Build artifacts (ignored by git)
└── .gitignore            # Excluded files and directories
```
