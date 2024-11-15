# ===== FIRST STAGE (INSTALL DEPS) =====
# Use the official Python image
FROM python:3.13-slim AS builder

# set working directory
WORKDIR /app

# install required packages from requirements.txt
COPY requirements.txt /app
RUN pip install --user --no-warn-script-location -r requirements.txt

# ===== SECOND STAGE (COPY FILES) =====
FROM python:3.13-slim

# copy over the installed packages
COPY --from=builder /root/.local /root/.local

# copy the rest of the files into there
COPY . /app


# update PATH environment variable
ENV PATH=/root/.local:/root/.local/bin:$PATH

# start API
WORKDIR /app
ENV PYTHONPATH=/app
CMD ["streamlit", "run", "ui/main.py", "--server.address", "0.0.0.0", "--server.port", "8095"]
