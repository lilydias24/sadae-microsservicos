# 🌊 Sistema SADAE - Sistema de Água e Esgoto

> Sistema completo de gerenciamento de faturamento e serviços de água e esgoto com interface moderna e responsiva.

## 🎯 Sobre o Projeto

O Sistema SADAE é uma aplicação web full-stack desenvolvida para gerenciar serviços de água e esgoto, incluindo faturamento, contestações, negociações e controle administrativo. O projeto foi completamente modernizado com uma interface responsiva, componentes reutilizáveis.

### ✨ Status Atual
- ✅ Frontend modernizado com design responsivo
- ✅ Sistema de componentes reutilizáveis
- ✅ Filtros avançados e busca em tempo real
- ✅ Modais funcionais para detalhes, contestações e negociações
- ✅ Estados de carregamento com skeleton
- ✅ Validações e tratamento de erros
- ✅ **Chain of Responsibility Pattern** implementado em todo o backend
- ✅ Sistema de autenticação e autorização em cadeia
- ✅ Validação inteligente de contestações e negociações
- ✅ Notificações multi-canal com fallback automático
- ✅ Processamento de ordens de serviço com auto-aprovação
- 🔄 Backend em desenvolvimento
- 🔄 Integração com API real (usando mock data)

## 🏗️ Arquitetura e Design Patterns

### Chain of Responsibility Pattern

O projeto implementa extensivamente o padrão **Chain of Responsibility** para desacoplar remetentes de receptores de solicitações. Este padrão permite que múltiplos objetos tenham a chance de processar uma requisição, organizados em uma cadeia.

**Onde foi aplicado:**

1. **🔐 API Gateway - Autenticação e Autorização**
   - Validação de token JWT
   - Verificação de expiração
   - Validação de roles e permissões
   - Controle de acesso a recursos
   - Rate limiting

2. **💰 Core Service - Billing**
   - Validação automática de contestações de faturas
   - Sistema de pontuação para auto-aprovação
   - Análise de evidências e histórico de consumo
   - Processamento de negociações de dívidas
   - Análise de crédito e definição de condições

3. **📢 Sistema de Notificações Multi-Canal**
   - Email → SMS → Push → WhatsApp → Webhook
   - Fallback automático entre canais
   - Priorização por urgência
   - Tracking completo de tentativas

4. **🔧 Core Service - Maintenance**
   - Classificação de ordens de serviço
   - Alocação automática de equipes
   - Estimativa de recursos e custos
   - Auto-aprovação baseada em regras

**Documentação completa:** [docs/CHAIN_OF_RESPONSIBILITY.md](docs/CHAIN_OF_RESPONSIBILITY.md)

### Benefícios da Implementação

✅ **Baixo Acoplamento**: Remetentes e receptores não se conhecem diretamente  
✅ **Flexibilidade**: Fácil adicionar ou remover handlers da cadeia  
✅ **Responsabilidade Única**: Cada handler tem uma função específica  
✅ **Rastreabilidade**: Histórico completo de processamento  
✅ **Testabilidade**: Handlers podem ser testados individualmente  

## 🚀 Comandos

### Iniciar o Sistema
```bash
# Construir e iniciar todos os serviços
docker-compose up --build -d

# Carregar dados iniciais (usuários)
docker exec sistemasadae-auth-service-1 python seed_data.py
```

### Comandos de Desenvolvimento
```bash
# Ver logs de um serviço específico
docker-compose logs -f api-gateway
docker-compose logs -f core-service
docker-compose logs -f auth-service

# Reiniciar um serviço
docker-compose restart api-gateway

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpar dados)
docker-compose down -v
```

## 👤 Credenciais de Teste

### Usuários Padrão
```
Operador:
- Email: operador@sadae.com
- Senha: operador123

Gestor Financeiro:
- Email: financeiro@sadae.com
- Senha: financeiro123

Gestor de Manutenção:
- Email: manutencao@sadae.com
- Senha: manutencao123
```

## 📁 Estrutura do Projeto

```
Sistema SADAE/
├── frontend/                  # React + TypeScript
│   ├── src/
│   │   ├── components/       # Componentes reutilizáveis
│   │   ├── pages/           # Páginas da aplicação
│   │   ├── contexts/        # Context API (Auth, Toast, WebSocket)
│   │   └── services/        # Integração com API
│   └── ...
│
├── services/
│   ├── api-gateway/         # Gateway de API
│   │   ├── main.py
│   │   └── auth_chain.py    # 🔗 Chain of Responsibility - Auth
│   │
│   ├── auth-service/        # Autenticação JWT
│   │   ├── main.py
│   │   └── database_models.py
│   │
│   └── core-service/        # Serviço principal
│       ├── main.py
│       ├── routers/         # Routers FastAPI
│       └── business/        # Lógica de negócio
│           ├── billing_validation_chain.py    # 🔗 Validação de Billing
│           └── maintenance_chain.py           # 🔗 Ordens de Serviço
│
├── shared/                  # Módulos compartilhados
│   ├── chain_of_responsibility.py  # 🔗 Base do padrão
│   ├── notification_chain.py       # 🔗 Notificações multi-canal
│   ├── auth.py
│   ├── database.py
│   └── utils.py
│
├── docs/
│   └── CHAIN_OF_RESPONSIBILITY.md  # 📖 Documentação completa
│
└── docker-compose.yml
```


## 🛠️ Tecnologias Utilizadas

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Context API
- Axios

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication
- WebSockets

### DevOps
- Docker
- Docker Compose
- Nginx (planejado)
