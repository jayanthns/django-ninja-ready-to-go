# Django Ninja POC

## Prerequisites

- `Django`
- `Django Rest Framework`
- `Django-Ninja`
- `PostgreSQL` *(optional for local development)*

## Getting Started

### 1. Clone this repository

```bash
git clone <placeholder link>
```

### 2. Navigate to the project directory

```bash
cd <folder-name>
```

### 3. Create a virtual environment and install dependencies

#### Manually

```bash
python3 -m venv venv
```

#### Activate the virtual environment

```bash
source venv/bin/activate
```

#### Using Makefile

```bash
make init
```

### 4. Set up environment variables

Create a `.env` file and copy the contents from `.env.copy` to `.env`.

### 5. Running the service

```bash
make run_uvicorn
```

### 6. Running via Docker

```bash
make run_docker_compose
```

---

### 🎉 Happy Coding!
