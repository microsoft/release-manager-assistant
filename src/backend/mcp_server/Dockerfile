FROM mcr.microsoft.com/azurelinux/base/python:3.12

RUN tdnf -y update && tdnf -y install build-essential curl ca-certificates

WORKDIR /src

# Copy the mcp directory (including services and synthetic datasets)
COPY ./mcp_server /src/mcp_server

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /src/mcp_server/requirements.txt

EXPOSE 12321

CMD ["python3", "/src/mcp_server/app.py"]