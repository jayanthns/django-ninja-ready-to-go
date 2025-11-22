# Package Manager Guide - Complete Beginner's Guide to `uv`

> **👋 New to Python package management?** This guide explains everything from scratch!

## Table of Contents

1. [What is a Package Manager?](#what-is-a-package-manager)
2. [Why We Use `uv`](#why-we-use-uv)
3. [How We Use `uv` in This Django Ninja Project](#how-we-use-uv-in-this-django-ninja-project)
4. [Understanding Key Concepts](#understanding-key-concepts)
5. [Getting Started](#getting-started)
6. [Common Tasks - Step by Step](#common-tasks---step-by-step)
7. [Understanding the Files](#understanding-the-files)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## How We Use `uv` in This Django Ninja Project

> **🎯 Skip here if you just want to know how to use it in THIS project!**

### Our Setup

This Django Ninja API project uses `uv.lock` workflow with:

- **68 total packages** (including all dependencies)
- **17 production packages** (Django, django-ninja, database drivers, etc.)
- **12 development packages** (pytest, black, flake8, etc.)
- **Make commands** for easy workflow (no need to remember uv commands!)

### Project-Specific Files

```bash
django-ninja-ready-to-go/
├── pyproject.toml          # Our dependencies list
├── uv.lock                 # Locked versions (68 packages)
├── Makefile                # Easy commands (make add-package, etc.)
├── venv/                   # Virtual environment (don't commit!)
└── apps/                   # Django apps
    ├── ping_app/
    ├── users_app/
    └── animals_app/
```

### Our Production Dependencies

**What's installed when you run `make install`:**

| Category            | Packages                                           | Why We Need Them                  |
| ------------------- | -------------------------------------------------- | --------------------------------- |
| **Web Framework**   | Django, django-ninja, uvicorn                      | Core API framework                |
| **Database**        | psycopg2-binary, django-redis                      | PostgreSQL & Redis support        |
| **Data Processing** | pandas, openpyxl, xlrd                             | File handling & data manipulation |
| **API Features**    | pydantic, aiohttp                                  | Data validation & async HTTP      |
| **Security**        | django-shinobi                                     | Permissions management            |
| **Utilities**       | python-dotenv, python-json-logger, email-validator | Configuration & logging           |

### Our Development Dependencies

**What's installed for testing and development:**

| Tool       | Purpose         | Command                        |
| ---------- | --------------- | ------------------------------ |
| **pytest** | Running tests   | `make pytest`                  |
| **black**  | Code formatting | `make black_check`             |
| **flake8** | Linting         | `make flake8`                  |
| **mypy**   | Type checking   | (configured in pyproject.toml) |
| **isort**  | Import sorting  | `make isort_check`             |

### Django-Specific Workflow

#### 1. Initial Setup (New Team Member)

```bash
# Clone the repo
git clone <your-repo-url>
cd django-ninja-ready-to-go

# One command to set everything up!
make init

# What this does:
# - Creates virtual environment (venv/)
# - Installs all 68 packages from uv.lock
# - Ready to run Django!
```

#### 2. Daily Development

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
# OR: venv\Scripts\activate  # Windows

# Run Django development server
make run
# OR: python manage.py runserver

# Run tests
make pytest

# Check code quality
make static-tests
```

#### 3. Adding a Package You Need

```bash
# Example: Need to send emails
make add-package PACKAGE=django-anymail VERSION=10.2

# ✅ Auto-updates: pyproject.toml, uv.lock
# ✅ Auto-installs: ready to import immediately!
# ✅ Team gets it too: when they pull and run `make install`
```

#### 4. Before Committing Code

```bash
# Always ensure dependencies are synced
make install

# Run tests to make sure nothing broke
make pytest

# Commit your changes INCLUDING uv.lock
git add pyproject.toml uv.lock
git commit -m "Add django-anymail for email support"
```

### Integration with Django Commands

Our Makefile integrates `uv` with Django:

```bash
# Django Management
make run              # python manage.py runserver
make migrate          # python manage.py migrate
make makemigrations   # python manage.py makemigrations
make shell            # python manage.py shell

# Package Management
make add-package PACKAGE=celery     # Add & install package
make install                         # Sync all packages

# Testing & Quality
make pytest           # Run all tests
make static-tests     # Run linting & formatting checks

# All commands use the venv automatically!
```

### Our Configuration: `pyproject.toml`

**Where our dependencies are defined:**

```toml
[project]
name = "django-ninja-ready-to-go"
version = "0.1.0"
description = "Django Ninja API Ready-to-Go Starter Template"
requires-python = ">=3.10"

dependencies = [
    "Django==4.2.16",
    "django-ninja==1.1.0",
    # ... 15 more production packages
]

[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "pytest-django==4.8.0",
    # ... 10 more dev packages
]

# Special: We set package=false because this is a Django app, not a library
[tool.uv]
package = false
```

### Quick Start for This Project

#### Scenario: You just joined the team

```bash
# 1️⃣ Clone and setup
git clone <repo-url>
cd django-ninja-ready-to-go
make init

# 2️⃣ Create database
make migrate

# 3️⃣ Run the server
make run

# 4️⃣ Run tests to verify everything works
make pytest

# ✅ You're done! API is running on http://localhost:8000
```

### Common Scenarios in This Project

#### Scenario 1: Need to add a new Django package

```bash
# Example: Add Django REST framework extensions
make add-package PACKAGE=drf-extensions VERSION=0.7.1

# Use it immediately in your Django code
from rest_framework_extensions.mixins import ...
```

#### Scenario 2: Need a testing utility

```bash
# Example: Add factory-boy for test fixtures
make add-dev-package PACKAGE=factory-boy VERSION=3.3.0

# Use in your tests
from factory import Factory
```

#### Scenario 3: Pull latest code with new dependencies

```bash
git pull

# Someone added packages - sync them
make install

# All new packages are now installed! ✅
```

#### Scenario 4: Monthly update cycle

```bash
# Check what's outdated
uv pip list --outdated

# Update everything to latest compatible versions
make update-deps

# Run full test suite
make pytest

# If tests pass:
git add uv.lock
git commit -m "chore: update dependencies"
```

### Why Our Makefile Makes It Easy

Instead of remembering complex `uv` commands, we have simple shortcuts:

| What You Want | Instead of typing...                                        | Just type...                                                 |
| ------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |
| Add package   | `uv add "django-cors-headers==4.3.1" && uv lock && uv sync` | `make add-package PACKAGE=django-cors-headers VERSION=4.3.1` |
| Install deps  | `uv sync --all-extras`                                      | `make install`                                               |
| Update all    | `uv lock --upgrade && uv sync --all-extras`                 | `make update-deps`                                           |
| See help      | (search documentation)                                      | `make help`                                                  |

### A Note on `venv` vs `.venv`

By default, `uv` looks for a virtual environment named `.venv`. However, this project uses `venv`.

**Our `Makefile` handles this automatically** by setting:

```makefile
export UV_PROJECT_ENVIRONMENT = $(shell pwd)/venv
```

If you run `uv` commands manually (without `make`), you might need to set this variable yourself or `uv` might create a new `.venv` directory that isn't used by the project. **We strongly recommend using the `make` commands.**

---

## What is a Package Manager?

Think of a package manager like an **app store for your code**. Just like you install apps on your phone, Python projects need to install "packages" (code libraries written by other developers).

**Example**: If you want to send emails from your Django app, instead of writing all the email code yourself, you can install a package like `django-anymail` that already does it.

### Why Can't I Just Download Code Manually?

You could, but:

- **Dependencies**: Each package might need OTHER packages to work
- **Versions**: You need specific versions that work together
- **Updates**: You need to know when updates are available
- **Team Work**: Your teammates need the exact same packages

A package manager solves all of this automatically! 🎉

---

## Why We Use `uv`

### The Evolution of Python Package Managers

```text
pip (slow & basic) → pip-tools (better) → uv (fastest! ⚡)
```

**`uv` is like pip on steroids:**

- ⚡ **10-100x faster** than pip
- 🔒 **Better dependency resolution** (fewer conflicts)
- 🎯 **Modern workflow** (like Rust's cargo or Node's npm)
- 🛠️ **All-in-one tool** (no need for multiple tools)

### Real Speed Difference

```bash
# Installing 68 packages:
pip install        → ~20-30 seconds
uv sync           → ~1-2 seconds  🚀
```

---

## Understanding Key Concepts

### 1. **Dependencies**

**What are dependencies?**
Code libraries your project needs to run.

**Example:**

```python
# You want to use Django
from django import ...  # ❌ Won't work without installing Django first

# After installing Django:
from django import ...  # ✅ Works!
```

### 2. **Production vs Development Dependencies**

**Production Dependencies**:

- Code needed to RUN your app
- Examples: Django, database drivers, API frameworks

**Development Dependencies**:

- Tools for BUILDING your app
- Examples: pytest (testing), black (code formatting), mypy (type checking)

**Why separate them?**

- Your production server doesn't need testing tools
- Keeps production installations faster and smaller

### 3. **Lock Files** (`uv.lock`)

**What is a lock file?**
A snapshot of EXACT versions of every package (and their dependencies).

**Why do we need it?**

**Without lock file:**

```text
You install Django "latest version" → Gets Django 4.2.16
Your teammate installs Django "latest version" → Gets Django 4.3.0 (newer!)
Result: Your code might break on their computer! 😱
```

**With lock file:**

```text
You install → Django 4.2.16 (from uv.lock)
Your teammate installs → Django 4.2.16 (from uv.lock)
Result: Everyone has identical packages! ✅
```

### 4. **`pyproject.toml`**

Think of this as your **shopping list**:

- Lists what packages you want
- Doesn't specify exact versions of dependencies

`uv` reads this file and creates `uv.lock` with exact versions.

---

## Getting Started

### Prerequisites

**What you need:**

- Python 3.10 or higher
- Terminal/Command line access
- This repository cloned to your computer

### First Time Setup

#### Step 1: Install `uv`

**On Mac/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify installation:**

```bash
uv --version
# Should show: uv 0.x.x
```

#### Step 2: Set Up Project

```bash
# Navigate to project directory
cd django-ninja-ready-to-go

# Initialize virtual environment and install all packages
make init

# Alternative: Do it manually
uv venv venv                # Create virtual environment
source venv/bin/activate    # Activate it (Mac/Linux)
# OR on Windows: venv\Scripts\activate

# IMPORTANT: Tell uv to use this venv (otherwise it looks for .venv)
export UV_PROJECT_ENVIRONMENT=$(pwd)/venv

uv sync --all-extras        # Install all packages
```

**What just happened?**

1. Created a virtual environment (isolated Python installation)
2. Installed all 68 packages from `uv.lock`
3. You're ready to code! 🎉

---

## Common Tasks - Step by Step

### Task 1: Adding a New Package

**Scenario**: You want to use the `requests` library to make HTTP calls.

**Step-by-step:**

1. **Add the package:**

   ```bash
   make add-package PACKAGE=requests VERSION=2.31.0
   ```

2. **What happens behind the scenes:**

   - Updates `pyproject.toml` with `requests==2.31.0`
   - Updates `uv.lock` with requests AND all its dependencies
   - **Automatically installs** the package
   - Ready to use immediately!

3. **Use it in your code:**

   ```python
   import requests
   response = requests.get('https://api.example.com')
   ```

**Without version (gets latest):**

```bash
make add-package PACKAGE=requests
```

### Task 2: Adding a Development Tool

**Scenario**: You want to use `ipython` for better Python shell.

```bash
make add-dev-package PACKAGE=ipython VERSION=8.29.0
```

**Difference from production package:**

- Goes into `[project.optional-dependencies].dev` section
- Won't be installed on production servers
- Only installed when you use `--all-extras` flag

### Task 3: Removing a Package

**Scenario**: You no longer need `requests`.

```bash
make remove-package PACKAGE=requests
```

**What happens:**

- Removes from `pyproject.toml`
- Updates `uv.lock`
- **Uninstalls** the package automatically
- Cleans up dependencies that nothing else needs

### Task 4: Upgrading All Packages

**Scenario**: Monthly maintenance to get latest versions.

```bash
make update-deps
```

**What happens:**

- Checks for newer versions of all packages
- Updates `uv.lock` with new versions
- Installs the updates
- **Important**: Test your app after upgrading!

### Task 5: Installing on a New Machine

**Scenario**: You cloned the repo on a new computer.

```bash
# Quick way:
make init

# Manual way:
uv venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
uv sync --all-extras
```

**Result**: Gets exact same packages as everyone else (from `uv.lock`)

### Task 6: Check What's Installed

```bash
# List all packages
uv pip list

# Check for outdated packages
uv pip list --outdated
```

---

## Manual Package Addition (Advanced)

> **🎓 Want to add packages by editing files directly instead of using `make` commands? Here's how!**

Sometimes you might want to manually edit `pyproject.toml` instead of using `make add-package`. This is useful when:

- Adding **multiple packages** at once
- Setting version ranges (e.g., `>=5.0,<6.0`)
- You prefer direct control

### The Manual Workflow

**3-Step Process:**

1. Edit `pyproject.toml`
2. Run `make compile-deps`
3. Commit both files

### Step 1: Edit `pyproject.toml`

Open [`pyproject.toml`](file:///Users/jayanth.ns/workspace/django-ninja-ready-to-go/pyproject.toml):

#### For Production Dependencies

```toml
[project]
dependencies = [
    "Django==4.2.16",
    "django-ninja==1.1.0",
    "uvicorn==0.30.6",
    # ... existing packages ...
    "celery==5.3.4",        # ← Add your new package here
]
```

#### For Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "pytest-django==4.8.0",
    # ... existing packages ...
    "ipython==8.29.0",      # ← Add your new dev package here
]
```

### Step 2: Regenerate Lock File

After editing, **you must regenerate `uv.lock`:**

```bash
make compile-deps
```

**What this command does:**

```bash
# Behind the scenes:
uv lock               # Reads pyproject.toml, creates uv.lock
uv sync --all-extras  # Installs all packages
```

### Step 3: Commit Both Files

```bash
git add pyproject.toml uv.lock
git commit -m "Add celery for background tasks"
```

---

### 💪 Exercise: Add Celery Step-by-Step

Let's practice adding **Celery** (a task queue) manually:

#### 1. Open `pyproject.toml`

```bash
vim pyproject.toml
# OR use your favorite editor
```

#### 2. Find the `dependencies` section

Looks like this:

```toml
dependencies = [
    "Django==4.2.16",
    "django-ninja==1.1.0",
    "uvicorn==0.30.6",
    "pydantic==2.9.2",
    # ... more packages
]
```

#### 3. Add Celery

```toml
dependencies = [
    "Django==4.2.16",
    "django-ninja==1.1.0",
    "uvicorn==0.30.6",
    "pydantic==2.9.2",
    "celery==5.3.4",        # ← ADD THIS LINE
    # ... rest of packages
]
```

**Tips:**

- Keep **alphabetical order** (optional but organized)
- Use exact version with `==` for stability
- Add a comment explaining why if needed

#### 4. Save and regenerate lock file

```bash
make compile-deps
```

**Expected output:**

```text
Locking dependencies from pyproject.toml...
Resolved 72 packages in 324ms
Installed 4 packages in 125ms
 + billiard==4.2.0      # ← Celery's dependency
 + celery==5.3.4        # ← Your package
 + kombu==5.3.4         # ← Another dependency
 + vine==5.1.0          # ← Another dependency
```

**Notice:** You added 1 package, but `uv` installed 4! That's because Celery needs those other packages to work. The lock file handles this automatically! 🎯

#### 5. Verify it worked

```bash
# Check celery is installed
uv pip show celery

# Test import
python -c "import celery; print(celery.__version__)"
# Output: 5.3.4

# List all packages
uv pip list | grep celery
```

#### 6. Commit your changes

```bash
git status
# You'll see:
#   modified:   pyproject.toml
#   modified:   uv.lock

git add pyproject.toml uv.lock
git commit -m "Add Celery 5.3.4 for background task processing"
```

---

### 🎯 Exercise: Add Multiple Packages at Once

**Scenario:** You're building an email feature and need 3 packages.

#### 1. Edit `pyproject.toml`

```toml
dependencies = [
    "Django==4.2.16",
    # ... existing packages ...
    "django-anymail==10.2",      # ← Email backend
    "sendgrid==6.11.0",           # ← SendGrid integration
    "premailer==3.10.0",          # ← HTML email styling
]
```

#### 2. Regenerate

```bash
make compile-deps
# Installs all 3 + their dependencies in one go!
```

#### 3. Verify

```bash
uv pip list | grep -E "anymail|sendgrid|premailer"
```

**Result:** All 3 packages installed with one command! ✅

---

### Comparison: Manual vs Make Command

| Aspect       | Manual Edit                         | `make add-package`    |
| ------------ | ----------------------------------- | --------------------- |
| **Speed**    | Best for 2+ packages                | Best for 1 package    |
| **Control**  | Full control (version ranges, etc.) | Simple exact versions |
| **Workflow** | Edit → Lock → Commit                | One command           |
| **Best for** | Experienced users                   | Beginners             |

**Example: Which to use?**

```bash
# Adding 1 package? Use make command:
make add-package PACKAGE=requests VERSION=2.31.0

# Adding 3+ packages? Manual is faster:
# Edit pyproject.toml with all 3
# Then: make compile-deps
```

---

### ✅ Best Practices for Manual Addition

#### 1. Use Exact Versions (Production)

```toml
# ✅ Good - Exact version, predictable
"Django==4.2.16"

# ⚠️ Okay - Range, but may break
"Django>=4.2,<5.0"

# ❌ Bad - No version, unpredictable!
"Django"
```

#### 2. Group Related Packages

```toml
dependencies = [
    # Core framework
    "Django==4.2.16",
    "django-ninja==1.1.0",

    # Task queue
    "celery==5.3.4",
    "django-celery-beat==2.5.0",
    "django-celery-results==2.5.1",

    # Database
    "psycopg2-binary==2.9.9",
    "django-redis==6.0.0",
]
```

#### 3. Add Comments for Context

```toml
dependencies = [
    "Django==4.2.16",
    "stripe==7.4.0",  # Payment processing - requires API key in .env
    "sentry-sdk==1.40.0",  # Error tracking - configured in settings.py
]
```

#### 4. Always Test After Adding

```bash
make compile-deps
make pytest           # Run tests
make static-tests     # Check code quality
python manage.py check  # Django system check
```

---

### 🚨 Common Mistakes to Avoid

#### Mistake 1: Forgetting to regenerate lock file

```bash
# ❌ WRONG
vim pyproject.toml    # Edit file
git commit -a         # Commit without regenerating!

# ✅ CORRECT
vim pyproject.toml
make compile-deps     # Regenerate lock file!
git add pyproject.toml uv.lock
git commit -m "Add packages"
```

**Why it matters:** Your teammates won't get the new packages!

#### Mistake 2: Editing `uv.lock` directly

```bash
# ❌ NEVER DO THIS
vim uv.lock  # Manually editing lock file

# ✅ DO THIS INSTEAD
vim pyproject.toml
make compile-deps
```

**Why:** `uv.lock` is auto-generated. Manual edits will be overwritten!

#### Mistake 3: Installing with pip

```bash
# ❌ WRONG
pip install celery  # Bypasses uv.lock!

# ✅ CORRECT
make add-package PACKAGE=celery
# OR
vim pyproject.toml
make compile-deps
```

**Why:** Pip doesn't update `uv.lock`, causing version mismatches!

---

### 🎓 Practice Exercise

Try this yourself:

**Task:** Add `django-cors-headers` for handling CORS in your API.

**Steps:**

1. Open `pyproject.toml`
2. Add `"django-cors-headers==4.3.1"` to dependencies
3. Run `make compile-deps`
4. Verify with `uv pip show django-cors-headers`
5. Import in Django: `from corsheaders import ...`
6. Commit both files

**Solution:**

```bash
# 1. Edit pyproject.toml
# Add: "django-cors-headers==4.3.1"

# 2. Regenerate
make compile-deps

# 3. Verify
uv pip show django-cors-headers

# 4. Commit
git add pyproject.toml uv.lock
git commit -m "Add django-cors-headers for CORS support"
```

---

### When You're Done

Remember:

- ✅ **Always run `make compile-deps`** after editing
- ✅ **Always commit both files** together
- ✅ **Test your changes** before pushing
- ✅ **Document why** you added packages (in commit message or comments)

Now you know both ways to add packages! Use whichever fits your workflow better. 🎉

---

## Understanding the Files

### 📄 `pyproject.toml`

**Location**: Project root
**What it is**: Main configuration file

**Key sections:**

```toml
[project]
name = "django-ninja-ready-to-go"
version = "0.1.0"
requires-python = ">=3.10"

# Production dependencies (17 packages)
dependencies = [
    "Django==4.2.16",
    "django-ninja==1.1.0",
    # ... more
]

# Development dependencies (12 packages)
[project.optional-dependencies]
dev = [
    "pytest==8.3.3",
    "black==24.8.0",
    # ... more
]
```

**When to edit manually:**

- Adding multiple packages at once
- Changing version constraints
- Updating project metadata

### 🔒 `uv.lock`

**Location**: Project root
**What it is**: Lock file with exact versions (68 packages total)

**Never edit this file manually!** It's auto-generated.

**What's inside:**

```toml
[[package]]
name = "django"
version = "4.2.16"
# ... exact metadata

[[package]]
name = "sqlparse"
version = "0.5.3"
# ... dependency of django
```

**Commit this file to Git!** Everyone needs it.

### 📁 `venv/` (Virtual Environment)

**What it is**: Isolated Python installation for this project

**Why we need it:**

- Different projects can use different package versions
- Doesn't mess with your system Python
- Easy to delete and recreate

**Important**:

- ✅ DO commit: `pyproject.toml`, `uv.lock`
- ❌ DON'T commit: `venv/` (already in `.gitignore`)

---

## Troubleshooting

### Problem: "command not found: uv"

**Solution:**

```bash
# Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal
```

### Problem: "No module named 'django'"

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate    # Mac/Linux
# OR
venv\Scripts\activate       # Windows

# Install packages
make install
```

### Problem: Package conflicts

**Solution:**

```bash
# Clean slate approach
rm -rf venv
rm uv.lock
make init
```

### Problem: "I modified pyproject.toml, now what?"

**Solution:**

```bash
# Regenerate lock file
make compile-deps
```

### Problem: Different packages on different computers

**Solution:**

```bash
# Always install from lock file
uv sync --all-extras

# NOT:
pip install django  # ❌ Bypasses lock file
```

---

## FAQ

### Q: What's the difference between `make install` and `uv sync`?

**A:** They're the same now! `make install` runs `uv sync --all-extras`.

---

### Q: Should I commit `uv.lock`?

**A:** **YES!** Always commit `uv.lock`. This ensures everyone has the same packages.

```bash
git add uv.lock
git commit -m "Update dependencies"
```

---

### Q: Can I still use `pip`?

**A:** Technically yes, but **don't**. It bypasses the lock file and causes version mismatches.

```bash
pip install requests  # ❌ Don't do this!
make add-package PACKAGE=requests  # ✅ Do this instead
```

---

### Q: How do I see what changed when I update dependencies?

**A:**

```bash
# Before updating
git diff uv.lock

# After updating
git diff uv.lock
# Shows what versions changed
```

---

### Q: What if I just want to add a package temporarily for testing?

**A:**

```bash
# Install without updating pyproject.toml
uv pip install requests

# To remove:
uv pip uninstall requests

# Note: Won't persist after uv sync
```

---

### Q: How do I know what packages I have installed?

**A:**

```bash
# List all installed packages
uv pip list

# Check a specific package
uv pip show django
```

---

### Q: What's the difference between `update-deps` and `compile-deps`?

**A:**

```bash
# compile-deps: Lock CURRENT versions from pyproject.toml
make compile-deps
# Use when: You edited pyproject.toml manually

# update-deps: UPGRADE to latest compatible versions
make update-deps
# Use when: You want to update all packages
```

---

### Q: Can I use this with Docker?

**A:** Yes! Here's a Dockerfile example:

```dockerfile
FROM python:3.10

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application
COPY . .
```

---

### Q: How do I export to old-style `requirements.txt`?

**A:**

```bash
make export-requirements
# Creates: requirements.txt and requirements-dev.txt
```

**When to use:**

- Legacy CI/CD systems
- Deployment platforms that only accept requirements.txt
- Sharing with teams not using uv

---

## Quick Reference Cheat Sheet

```bash
# 🚀 SETUP
make init                                    # First time setup

# 📦 ADDING PACKAGES
make add-package PACKAGE=requests VERSION=2.31.0    # Add production package
make add-dev-package PACKAGE=pytest                 # Add dev package

# 🗑️ REMOVING PACKAGES
make remove-package PACKAGE=requests           # Remove production package
make remove-dev-package PACKAGE=pytest         # Remove dev package

# ⬆️ UPDATING
make update-deps                              # Upgrade all packages
make compile-deps                             # Lock current versions

# 🔍 CHECKING
uv pip list                                   # List installed packages
uv pip list --outdated                        # Check for updates
uv pip show django                            # Show package details

# 🛠️ TROUBLESHOOTING
rm -rf venv && make init                      # Fresh reinstall
make export-requirements                      # Export to requirements.txt

# 📚 HELP
make help                                     # Show all make commands
```

---

## Advanced Tips

### Tip 1: Speed up installs with cache

`uv` automatically caches packages. To clear cache:

```bash
uv cache clean
```

### Tip 2: Install only production packages (no dev tools)

```bash
uv sync  # Without --all-extras flag
```

### Tip 3: See what would be installed without installing

```bash
uv sync --dry-run
```

### Tip 4: Pin Python version

In `pyproject.toml`:

```toml
requires-python = "==3.10.8"  # Exact version
# OR
requires-python = ">=3.10,<3.12"  # Range
```

---

## Getting Help

- **Official `uv` docs**: <https://github.com/astral-sh/uv>
- **This project's help**: `make help`
- **Check package on PyPI**: <https://pypi.org/project/[package-name]/>

---

## Summary: The `uv` Philosophy

1. **`pyproject.toml`** = Your shopping list (what you want)
2. **`uv.lock`** = Your receipt (what you got, with exact versions)
3. **`venv/`** = Your pantry (where packages are stored)
4. **`make add-package`** = Going shopping
5. **`uv sync`** = Stocking your pantry

**Key Rule**: Always work with the lock file for consistency! 🔒

---

## Happy coding! 🎉

> Last updated: After migration to uv.lock workflow
