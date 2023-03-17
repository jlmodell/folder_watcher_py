# Use the official Python 3.11 slim image as the base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy the contents of the current directory to /app in the container
COPY . /app

# Create a virtual environment for the application
RUN python -m venv venv

# Activate the virtual environment
SHELL ["/bin/bash", "-c"]
RUN source venv/bin/activate

# Install the dependencies required to build and run the application
RUN pip install --no-cache-dir -r requirements.txt && \
    pyinstaller -F main.py && \
    mv dist/main /app/main && \
    rm -rf build dist *.spec

# Set the entry point for the container to run the application
ENTRYPOINT ["/bin/bash", "-c", "/app/main /mnt/busse/it/qc_db/2023\ Database/Release\ Reports\ 2023"]
