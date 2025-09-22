#!/bin/bash

echo "🚀 Iniciando SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto"
echo "=================================================================="

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verificar se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "✅ Docker e Docker Compose encontrados"

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env com configurações padrão..."
    cat > .env << EOL
# Database
POSTGRES_USER=sadae_user
POSTGRES_PASSWORD=sadae_password_2024
POSTGRES_DB=sadae_db

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET_KEY=sadae-super-secret-jwt-key-for-production-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8080

# Services URLs (internal Docker network)
AUTH_SERVICE_URL=http://auth-service:8000
MONITORING_SERVICE_URL=http://monitoring-service:8000
MAINTENANCE_SERVICE_URL=http://maintenance-service:8000
BILLING_SERVICE_URL=http://billing-service:8000
CRISIS_SERVICE_URL=http://crisis-service:8000

# Database URLs for services
AUTH_DATABASE_URL=postgresql://sadae_user:sadae_password_2024@postgres:5432/auth_db
MONITORING_DATABASE_URL=postgresql://sadae_user:sadae_password_2024@postgres:5432/monitoring_db
MAINTENANCE_DATABASE_URL=postgresql://sadae_user:sadae_password_2024@postgres:5432/maintenance_db
BILLING_DATABASE_URL=postgresql://sadae_user:sadae_password_2024@postgres:5432/billing_db
CRISIS_DATABASE_URL=postgresql://sadae_user:sadae_password_2024@postgres:5432/crisis_db
EOL
    echo "✅ Arquivo .env criado"
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Limpar volumes antigos se solicitado
if [ "$1" = "--clean" ]; then
    echo "🧹 Limpando volumes antigos..."
    docker-compose down -v
    docker system prune -f
fi

# Construir e iniciar os serviços
echo "🔨 Construindo e iniciando os serviços..."
docker-compose up -d --build

# Aguardar os serviços iniciarem
echo "⏳ Aguardando os serviços iniciarem..."
sleep 30

# Verificar status dos serviços
echo "🔍 Verificando status dos serviços..."
docker-compose ps

# Executar seed data para usuários de teste
echo "🌱 Criando usuários de demonstração..."
docker-compose exec auth-service python seed_data.py || echo "⚠️  Seed data já executado ou falhou"

echo ""
echo "🎉 SADAE iniciado com sucesso!"
echo "=================================================================="
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API Gateway: http://localhost:8080"
echo "📚 Documentação da API: http://localhost:8080/docs"
echo ""
echo "👥 Credenciais de demonstração:"
echo "   Operador: operator / password123"
echo "   Manutenção: maintenance / password123"
echo "   Financeiro: financial / password123"
echo "   Gestor de Crise: crisis / password123"
echo "   Cidadão: citizen / password123"
echo ""
echo "📋 Para ver os logs: docker-compose logs -f"
echo "🛑 Para parar: docker-compose down"
echo "=================================================================="
