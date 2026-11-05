# SADAE - Sistema de Apoio ao Departamento de Água e Esgoto

> Sistema de gerenciamento de serviços de água e esgoto com arquitetura de microserviços e padrões de projeto.
## Sobre o Projeto

O Sistema SADAE é uma aplicação web full-stack desenvolvida para gerenciar serviços de água e esgoto, incluindo:

- **Faturamento**: Gerenciamento completo de faturas, contestações e negociações
- **Autenticação**: Sistema de autenticação e autorização baseado em JWT
- **Monitoramento**: Monitoramento em tempo real de sensores e detecção de anomalias
- **Manutenção**: Controle de manutenções preventivas e corretivas
- **Suporte**: Sistema de atendimento ao cliente com tickets e base de conhecimento
- **Usuários**: Gestão de diferentes perfis de usuário (Cidadão, Operador, Gestores)

## Tecnologias

### Frontend
- **React 18** com TypeScript
- **Tailwind CSS** para estilização
- **React Router** para navegação
- **React Query** para gerenciamento de estado do servidor
- **Socket.io Client** para comunicação em tempo real
- **Recharts** para visualização de dados
- **React Hook Form** para formulários

### Backend
- **FastAPI** (Python) - Framework web assíncrono
- **SQLAlchemy** - ORM para banco de dados
- **PostgreSQL** - Banco de dados relacional
- **Redis** - Cache e mensageria em tempo real
- **JWT** - Autenticação baseada em tokens
- **Docker & Docker Compose** - Containerização e orquestração

### Arquitetura
- **Microserviços**: Arquitetura distribuída com serviços independentes
- **API Gateway**: Roteamento centralizado de requisições
- **WebSocket**: Comunicação bidirecional em tempo real

## Pré-requisitos

- **Docker Desktop** instalado e rodando
- **Docker Compose** (geralmente incluído no Docker Desktop)
- **PowerShell** (Windows) ou terminal compatível
- **Git** (opcional, para clonar o repositório)

## Instalação e Execução

### Opção 1: Script Automatizado

No Windows, execute o script de setup:

```powershell
.\setup.ps1
```

O script irá:
1. Verificar pré-requisitos (Docker, Docker Compose)
2. Verificar portas disponíveis
3. Limpar containers existentes
4. Construir e iniciar todos os serviços
5. Aguardar serviços ficarem prontos
6. Carregar dados iniciais (seeds)

### Opção 2: Manual

```bash
# Construir e iniciar todos os serviços
docker-compose up --build -d

# Carregar usuários iniciais
docker exec rpiv_project04-auth-service-1 python seed_data.py

# Carregar dados do sistema
docker exec rpiv_project04-core-service-1 python seed_data.py
```

## Estrutura do Projeto

```
rpiv_project04/
├── frontend/                 # Aplicação React/TypeScript
│   ├── src/
│   │   ├── components/      # Componentes reutilizáveis
│   │   ├── pages/           # Páginas da aplicação
│   │   ├── services/        # Serviços de API
│   │   ├── contexts/        # Contextos React
│   │   └── utils/           # Utilitários
│   └── Dockerfile
├── services/
│   ├── api-gateway/         # Gateway de API
│   ├── auth-service/        # Serviço de autenticação
│   ├── core-service/        # Serviço principal (billing, maintenance, support)
│   ├── monitoring-service/  # Serviço de monitoramento
│   └── support-service/     # Serviço de suporte
├── shared/                  # Módulos compartilhados
├── docker-compose.yml       # Configuração Docker Compose
└── setup.ps1                # Script de setup automatizado
```

## URLs e Endpoints

### Aplicação Web
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs

### Serviços Individuais
- **Auth Service**: http://localhost:8001
- **Core Service**: http://localhost:8002
- **Core Service Docs**: http://localhost:8002/docs
- **Monitoring Service**: http://localhost:8003

### Bancos de Dados
- **PostgreSQL** (Auth): porta 5432 (interno)
- **PostgreSQL** (Core): porta 5432 (interno)
- **PostgreSQL** (Monitoring): porta 5432 (interno)
- **Redis**: http://localhost:6379

## Credenciais de Acesso

### Usuário Operador (Principal)
- **Email**: `operador@sadae.com`
- **Senha**: `operador123`

### Outros Usuários Disponíveis
- **Cidadão**: 
  - Email: `cidadao@email.com`
  - Senha: `cidadao123`
- **Suporte**: 
  - Email: `suporte@sadae.com`
  - Senha: `suporte123`
- **Gestor de Crise**: 
  - Email: `gestor.crise@sadae.com`
  - Senha: `crise123`
- **Gestor de Manutenção**: 
  - Email: `gestor.manutencao@sadae.com`
  - Senha: `manutencao123`
- **Gestor Financeiro**: 
  - Email: `gestor.financeiro@sadae.com`
  - Senha: `financeiro123`


## Status Atual

### Funcionalidades Implementadas
- Frontend modernizado com design responsivo
- Sistema de componentes reutilizáveis
- Filtros avançados e busca em tempo real
- Modais funcionais para detalhes, contestações e negociações
- Estados de carregamento com skeleton
- Validações e tratamento de erros
- Sistema de autenticação completo
- Monitoramento em tempo real com WebSocket
- Detecção de anomalias
- Sistema de billing completo
- Gestão de manutenções
- Sistema de suporte ao cliente


### Em Desenvolvimento
- 🔄 Backend em desenvolvimento
- 🔄 Integração com API real (usando mock data)
- Integração completa frontend-backend
- Testes automatizados
- Documentação de API completa

## Problemas comuns

### Portas em Uso
Se as portas estiverem em uso, você pode:
1. Parar os containers existentes: `docker-compose down`
2. Verificar processos usando as portas e encerrá-los
3. Modificar as portas no `docker-compose.yml`

### Serviços Não Iniciam
1. Verifique os logs: `docker-compose logs [servico]`
2. Verifique se o Docker está rodando: `docker info`
3. Verifique espaço em disco disponível
4. Tente reconstruir: `docker-compose up --build -d`

### Seeds Não Executam
1. Aguarde os serviços ficarem prontos (pode levar alguns minutos)
2. Execute manualmente: `docker exec [container] python seed_data.py`
3. Verifique se os bancos de dados estão rodando: `docker-compose ps`


## Comandos Úteis

### Gerenciamento de Containers

```bash
# Ver status dos serviços
docker-compose ps

# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f [servico]

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpar dados)
docker-compose down -v

# Reiniciar um serviço específico
docker-compose restart [servico]

# Reconstruir um serviço específico
docker-compose up --build -d [servico]
```

### Executar Seeds Manualmente

```bash
# Carregar usuários
docker exec rpiv_project04-auth-service-1 python seed_data.py

# Carregar dados do sistema
docker exec rpiv_project04-core-service-1 python seed_data.py
```

### Acessar Container

```bash
# Listar containers em execução
docker ps

# Acessar shell de um container
docker exec -it [container-name] /bin/bash

# Executar comando Python em um container
docker exec [container-name] python [script.py]
```


## Minha contribuição

Atuei principalmente no **módulo de atendimento** e nos **relatórios**, do front-end
ao backend:

- páginas de suporte, chat de atendimento e widget de chat (React + TypeScript), com
  avaliação dos atendimentos;
- fluxo de tickets e registro de observações;
- página de relatórios e ajustes nas rotas de suporte, manutenção, monitoramento e
  faturamento do `core-service`;
- integração das rotas no `api-gateway` e ajustes no contexto de autenticação do front-end.

## Sobre este repositório

Cópia, com histórico, do repositório original do grupo no GitLab da UNIPAMPA
(componente Resolução de Problemas IV, 2025/2). A branch `main` contém a versão
integrada pelo grupo; as demais são o trabalho individual de cada integrante
(a minha é `Emy_branch`). Os e-mails dos colaboradores foram anonimizados no histórico.

## Licença

Este projeto é parte do trabalho acadêmico do componente RPIV.

## Contribuidores

Equipe do projeto SADAE - Sistema de Água e Esgoto.

---

**Nota**: Este é um sistema em desenvolvimento. Para mais informações, consulte a documentação de cada serviço ou entre em contato com a equipe de desenvolvimento.
