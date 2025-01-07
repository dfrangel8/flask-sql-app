#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias del sistema
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
apt-get install -y unixodbc-dev

# Instalar dependencias de Python
pip install -r requirements.txt 