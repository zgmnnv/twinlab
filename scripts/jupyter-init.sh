#!/bin/bash
set -e

echo "🚀 Initializing Jupyter Lab..."

# Fix permissions for the work directory
echo "📁 Setting up permissions..."
chown -R ${NB_UID}:${NB_GID} /home/jovyan/work
chmod -R 755 /home/jovyan/work

# Create .jupyter directory if it doesn't exist
mkdir -p /home/jovyan/.jupyter
chown -R ${NB_UID}:${NB_GID} /home/jovyan/.jupyter

echo "✅ Permissions set!"

# Set up proper umask for file creation
echo "🔧 Setting up file creation permissions..."
umask 002

# Switch to jovyan user and start Jupyter
echo "👤 Switching to jovyan user..."
exec su jovyan -c "export PATH=/opt/conda/bin:$PATH && export UMASK=002 && jupyter notebook --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*' --NotebookApp.allow_root=True --ip=0.0.0.0 --port=8888 --no-browser"
