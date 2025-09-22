# SADAE - Sistema de Análise de Dados de Abastecimento e Esgoto

Sistema completo de microsserviços para monitoramento e gestão de redes de abastecimento de água e esgoto, desenvolvido com Python (FastAPI) no backend e React no frontend.

## 🏗️ Arquitetura

O sistema utiliza arquitetura de microsserviços com os seguintes componentes:

### Core Services
- **API Gateway** (Port 8080): Ponto de entrada único para todas as requisições
- **Authentication Service** (Port 8000): Gerenciamento de usuários e autenticação JWT

### Domain Services
- **Monitoring Service** (Port 8000): Monitoramento de sensores em tempo real e detecção de anomalias
- **Maintenance Service** (Port 8000): Gestão de ordens de serviço e manutenções
- **Billing Service** (Port 8000): Faturamento, cobrança e gestão de hidrômetros inteligentes
- **Crisis Management Service** (Port 8000): Gestão de crises, simulações e rotas de evacuação

### Infrastructure
- **PostgreSQL**: Banco de dados dedicado para cada serviço
- **Redis**: Cache, dados em tempo real e WebSocket
- **React Frontend** (Port 3000): Interface web responsiva com TypeScript

## ✨ Funcionalidades Implementadas

### 📊 Módulo 1 - Monitoramento e Dados
- ✅ [RF001] Monitorar dados sensoriados em tempo real via WebSocket
- ✅ [RF002] Gerar relatórios de dados sensoriados em PDF/CSV
- ✅ [RF003] Gerar alertas automáticos para anomalias
- ✅ [RF004] Registrar observações manuais do operador

### 🔍 Módulo 2 - Análise e Detecção de Anomalias
- ✅ [RF005] Reportar vazamentos (interface pública para cidadãos)
- ✅ [RF006] Detectar anomalias automaticamente com algoritmos de ML
- ✅ [RF007] Registrar e confirmar anomalias pelo operador

### 🚨 Módulo 3 - Previsão e Alerta de Eventos Críticos
- ✅ [RF008] Emitir alertas automáticos de eventos críticos à Defesa Civil
- ✅ [RF009] Recalcular rotas de evacuação evitando áreas bloqueadas

### 🏢 Módulo 4 - Atendimento ao Público
- ✅ [RF010] Registrar reclamações e solicitações via portal público
- ✅ [RF011] Sistema de avaliação de atendimento pelos cidadãos

### 💰 Módulo 5 - Faturamento e Cobrança
- ✅ [RF012] Coletar leituras automáticas de hidrômetros inteligentes
- ✅ [RF013] Sistema de contestação de faturas pelos cidadãos
- ✅ [RF014] Gerenciar contestações com workflow de aprovação
- ✅ [RF015] Criar planos de negociação de débitos e parcelamentos

### 🔧 Módulo 6 - Gestão e Manutenção
- ✅ [RF016] Registrar manutenções com custos e tempo de execução
- ✅ [RF017] Gerar ordens de serviço a partir de anomalias
- ✅ [RF018] Relatórios detalhados de intervenções e KPIs
- ✅ [RF019] Sistema de notificações para equipes de campo

### 🎯 Módulo 7 - Simulação de Cenários
- ✅ [RF020] Simulador avançado de cenários de crise hídrica
- ✅ [RF021] Propor medidas de mitigação baseadas em simulações

## 👥 Tipos de Usuários

- **Operador**: Monitora dados em tempo real, gera alertas e observações
- **Cidadão**: Reporta problemas, acessa faturas e avalia atendimento
- **Gestor de Crise**: Gerencia emergências, executa simulações e coordena evacuações
- **Gestor de Manutenção**: Coordena equipes, gera ordens de serviço e relatórios
- **Gestor Financeiro**: Administra faturamento, contestações e negociações

## 🚀 Como Executar

### Pré-requisitos
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM disponível
- Portas 3000, 8080, 5432, 6379 livres

### Execução Rápida

\`\`\`bash
# Dar permissão aos scripts
chmod +x start.sh stop.sh

# Iniciar todo o sistema
./start.sh

# Para limpar dados antigos (primeira execução)
./start.sh --clean
\`\`\`

### Execução Manual

\`\`\`bash
# Clonar o repositório
git clone <repository-url>
cd sadae-system

# Copiar configurações de ambiente
cp .env.example .env

# Iniciar todos os serviços
docker-compose up -d --build

# Verificar status
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f
\`\`\`

### 🌐 URLs dos Serviços

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Documentação da API**: http://localhost:8080/docs
- **Serviços Públicos**: http://localhost:3000/public

### 🔑 Credenciais de Demonstração

| Usuário | Login | Senha | Permissões |
|---------|-------|-------|------------|
| Operador | `operator` | `password123` | Monitoramento, Alertas |
| Manutenção | `maintenance` | `password123` | Ordens de Serviço, Equipes |
| Financeiro | `financial` | `password123` | Faturamento, Contestações |
| Gestor de Crise | `crisis` | `password123` | Simulações, Evacuações |
| Cidadão | `citizen` | `password123` | Serviços Públicos |

## 🏗️ Estrutura do Projeto

\`\`\`
sadae-system/
├── 📄 docker-compose.yml          # Orquestração dos serviços
├── 📄 start.sh / stop.sh          # Scripts de inicialização
├── 📁 shared/                     # Código compartilhado
│   ├── models.py                  # Modelos de dados
│   ├── database.py                # Configuração de BD
│   ├── auth.py                    # Autenticação JWT
│   └── utils.py                   # Utilitários
├── 📁 services/
│   ├── 🌐 api-gateway/            # Gateway principal
│   ├── 🔐 auth-service/           # Autenticação
│   ├── 📊 monitoring-service/     # Monitoramento
│   ├── 🔧 maintenance-service/    # Manutenção
│   ├── 💰 billing-service/        # Faturamento
│   └── 🚨 crisis-service/         # Gestão de crises
└── 📁 frontend/                   # Aplicação React
    ├── src/
    │   ├── components/            # Componentes reutilizáveis
    │   ├── pages/                 # Páginas da aplicação
    │   ├── contexts/              # Context API (Auth, WebSocket)
    │   └── services/              # Integração com APIs
    └── public/
\`\`\`

## 🛠️ Desenvolvimento Local

### Backend Services

\`\`\`bash
# Instalar dependências Python
cd services/auth-service
pip install -r requirements.txt

# Executar serviço individual
uvicorn main:app --reload --port 8001

# Executar testes
pytest tests/
\`\`\`

### Frontend

\`\`\`bash
cd frontend
npm install
npm start

# Executar testes
npm test

# Build para produção
npm run build
\`\`\`

## 📊 Monitoramento e Logs

\`\`\`bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f monitoring-service

# Monitorar recursos
docker stats

# Verificar saúde dos serviços
curl http://localhost:8080/health
\`\`\`

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Edite o arquivo `.env` para personalizar:

- **Banco de dados**: Credenciais PostgreSQL
- **JWT**: Chave secreta e tempo de expiração
- **Redis**: URL de conexão
- **APIs externas**: Chaves para serviços de clima/mapas

### Escalabilidade

\`\`\`bash
# Escalar serviços específicos
docker-compose up -d --scale monitoring-service=3

# Usar load balancer
# Configurar nginx ou traefik como proxy reverso
\`\`\`

## 🧪 Recursos de Teste

### Simuladores Incluídos

- **Sensor Simulator**: Gera dados realistas de sensores
- **Meter Simulator**: Simula leituras de hidrômetros
- **Crisis Scenarios**: Cenários pré-configurados de teste

### Dados de Demonstração

O sistema inclui dados de exemplo:
- 50+ sensores distribuídos geograficamente
- 1000+ clientes com histórico de consumo
- Cenários de crise pré-configurados
- Equipes de manutenção e ordens de serviço

## 🔒 Segurança

- **Autenticação JWT** com refresh tokens
- **RBAC** (Role-Based Access Control)
- **Rate limiting** no API Gateway
- **Validação de entrada** em todos os endpoints
- **CORS** configurado adequadamente
- **Logs de auditoria** para ações críticas

## 📈 Performance

- **Cache Redis** para dados frequentes
- **WebSocket** para atualizações em tempo real
- **Paginação** em todas as listagens
- **Índices otimizados** no banco de dados
- **Compressão gzip** nas respostas HTTP

## 🚀 Deploy em Produção

### Docker Swarm

\`\`\`bash
# Inicializar swarm
docker swarm init

# Deploy da stack
docker stack deploy -c docker-compose.prod.yml sadae
\`\`\`

### Kubernetes

\`\`\`bash
# Aplicar manifests
kubectl apply -f k8s/

# Verificar pods
kubectl get pods -n sadae
\`\`\`

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Suporte

- **Documentação**: http://localhost:8080/docs
- **Issues**: GitHub Issues
- **Email**: suporte@sadae.com.br

---

**SADAE v1.0.0** - Sistema completo de gestão de abastecimento de água desenvolvido com arquitetura de microsserviços moderna.
\`\`\`

```json file="" isHidden
