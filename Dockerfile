# # Use the official Python 3 image as the base image
# FROM python:3 AS builder

# # Set the working directory to /app
# WORKDIR /app

# # Copy the contents of the current directory to /app in the container
# COPY . /app

# # Activate the virtual environment and install dependencies
# RUN pip install --no-cache-dir -r requirements.txt && \
#     pyinstaller -F main.py && \
#     rm -rf build

# # Final Dockerfile
# # Use the official Alpine image as the base image
# FROM alpine:latest

# # Install the necessary runtime dependencies for your application
# RUN apk add --no-cache libc6-compat libgcc libstdc++ && \
#     ln -s /lib/libc.musl-x86_64.so.1 /lib/ld-linux-x86-64.so.2

# # Copy the built application from the builder container
# COPY --from=builder /app/dist/main /app/main

# # Set the entry point for the container to run the application
# ENTRYPOINT ["/bin/sh", "-c", "/app/main /mnt/busse/it/qc_db/2023\ Database/Release\ Reports\ 2023"]

# Use the official Ubuntu image as the base image
FROM ubuntu:latest

# Install the necessary runtime dependencies for your application
RUN apt-get update && \
    apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the built application from the host into the container
COPY dist/main /app/main

# Set the entry point for the container to run the application
ENTRYPOINT ["/bin/bash", "-c", "/app/main /mnt/busse/it/qc_db/2023\ Database/Release\ Reports\ 2023"]
