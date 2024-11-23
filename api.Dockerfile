# ===== FIRST STAGE (INSTALL DEPS) =====
# Use the official Python image
FROM python:3.13-slim AS builder

# set working directory
WORKDIR /app

# create virtual env, then install required packages from requirements.txt
COPY requirements.txt /app
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ===== SECOND STAGE (COPY FILES) =====
FROM python:3.13-slim

# copy over the installed packages, and update PATH to include the env
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# copy the rest of the files into there
COPY . /app

# start API (note: port needs to match the "internal" port in compose.yaml)
WORKDIR /app
ENV PYTHONPATH=/app
CMD ["fastapi", "run", "api/main.py", "--host", "0.0.0.0", "--port", "8595"]
