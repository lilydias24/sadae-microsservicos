#!/bin/bash

echo "🛑 Parando SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto"
echo "=================================================================="

# Parar todos os containers
docker-compose down

echo "✅ Todos os serviços foram parados"

# Opção para limpar volumes
if [ "$1" = "--clean" ]; then
    echo "🧹 Limpando volumes e dados..."
    docker-compose down -v
    docker system prune -f
    echo "✅ Volumes e dados limpos"
fi

echo "=================================================================="
