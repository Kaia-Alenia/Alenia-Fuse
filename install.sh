#!/bin/bash
set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}✦ Instalando Alenia Fuse CLI vía Python...${NC}"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no está instalado o no se encuentra en el PATH."
    exit 1
fi

echo "Instalando Alenia Fuse..."
python3 -m pip install -e .

echo -e "${GREEN}✔ ¡Instalación completa!${NC}"
echo -e "Puedes ejecutar el CLI desde cualquier lugar escribiendo: ${CYAN}fuse${NC}"
