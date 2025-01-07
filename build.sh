#!/usr/bin/env bash
# exit on error
set -o errexit

# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc
curl https://packages.microsoft.com/config/debian/11/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# Install prerequisites
apt-get update
apt-get install -y --no-install-recommends \
    apt-transport-https \
    locales \
    unixodbc-dev

# Install Microsoft ODBC Driver for SQL Server
ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Configure locale
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8

# Install Python dependencies
pip install -r requirements.txt 