FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli nodejs npm

WORKDIR /src

# Copy the orchestrator directory.
COPY ./services/orchestrator /src/orchestrator

# Copy the common module directory.
COPY ./common /src/orchestrator/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/orchestrator/requirements.txt

EXPOSE 5002

CMD ["python3", "/src/orchestrator/app.py"]