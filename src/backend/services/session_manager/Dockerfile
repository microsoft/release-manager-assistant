FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates azure-cli

WORKDIR /src

# Copy the session_manager directory.
COPY ./services/session_manager /src/session_manager

# Copy the common module directory.
COPY ./common /src/session_manager/common

# Install dependencies.
RUN pip install --no-cache-dir --upgrade -r /src/session_manager/requirements.txt

EXPOSE 5000

CMD ["python3", "/src/session_manager/app.py"]