#!/usr/bin/env bash
# exit on error
set -o errexit

# Add Microsoft repository and keys
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install prerequisites
apt-get update
apt-get install -y --no-install-recommends \
    apt-transport-https \
    locales \
    unixodbc-dev \
    gnupg \
    curl

# Accept EULA and install ODBC Driver
ACCEPT_EULA=Y apt-get install -y msodbcsql17
ACCEPT_EULA=Y apt-get install -y mssql-tools

# Configure locale
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8

# Verify ODBC installation
odbcinst -j
ls -l /opt/microsoft/msodbcsql17/lib64/

# Install Python dependencies
pip install -r requirements.txt 