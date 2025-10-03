# FastAPI Project

This project is built with [FastAPI](https://fastapi.tiangolo.com/), a modern, fast (high-performance) web framework for building APIs with Python. Follow the steps below to set up, run, and maintain the project.

## Prerequisites

- Python 3.8 or higher
- Git

## Project Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Muzammilzia/Talent-Scan-FastAPI.git
   cd Talent-Scan-FastAPI
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   or
   py -3 -m venv venv
   ```

3. **Activate the virtual environment**:  
   - On Mac:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. **Install the project dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Project

With the virtual environment activated, run the following command to start the FastAPI server:
```bash
fastapi dev app/main.py
```
- `main` is the filename where the FastAPI `app` instance is defined.
- `--reload` enables auto-reload for development.

The application should be accessible at `http://127.0.0.1:8000`.

## Adding New Packages

1. **Install the new package**:
   ```bash
   pip install <package-name>
   ```

2. **Update `requirements.txt`**: After installing a new package, update the `requirements.txt` file to ensure others can install the latest dependencies:
   ```bash
   pip freeze > requirements.txt
   ```

3. **Commit the updated `requirements.txt`**:
   ```bash
   git add requirements.txt
   git commit -m "Added <package-name> to requirements"
   git push origin <branch-name>
   ```

