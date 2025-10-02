#!/bin/bash
set -e

echo "🚀 Initializing Jupyter Lab..."

# Set environment variables
export NB_UID=${NB_UID:-1000}
export NB_GID=${NB_GID:-1000}

# Fix ownership and permissions for the work directory
echo "📁 Setting up permissions..."
chown -R ${NB_UID}:${NB_GID} /home/jovyan/work
chmod -R 755 /home/jovyan/work

# Create and fix permissions for .jupyter directory
echo "🔧 Setting up Jupyter configuration directory..."
mkdir -p /home/jovyan/.jupyter
chown -R ${NB_UID}:${NB_GID} /home/jovyan/.jupyter
chmod -R 755 /home/jovyan/.jupyter

# Create and fix permissions for .local directory
mkdir -p /home/jovyan/.local/share/jupyter
chown -R ${NB_UID}:${NB_GID} /home/jovyan/.local
chmod -R 755 /home/jovyan/.local

# Set up proper umask for file creation
echo "🔧 Setting up file creation permissions..."
umask 002

echo "✅ Permissions set!"

# Switch to jovyan user and start Jupyter
echo "👤 Switching to jovyan user..."
exec su jovyan -c "export PATH=/opt/conda/bin:$PATH && export UMASK=002 && jupyter notebook --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*' --NotebookApp.allow_root=True --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.disable_check_xsrf=True"
