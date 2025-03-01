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

# install curl for healthcheck
RUN apt-get update && apt-get install -y curl

# copy the rest of the files into there
COPY admin_tools/ /app/admin_tools/
COPY api/ /app/api/
COPY common/ /app/common/
COPY ui/ /app/ui/

# start API (note: port needs to match the "internal" port in compose.yaml)
WORKDIR /app
ENV PYTHONPATH=/app
CMD ["fastapi", "run", "api/main.py", "--host", "0.0.0.0", "--port", "8595"]
