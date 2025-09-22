# Comandos Úteis - Sistema SADAE

## Gerenciamento do Sistema
```powershell
# Ver status dos serviços
docker compose ps

# Iniciar o sistema
docker compose up -d

# Parar o sistema
docker compose down

# Reiniciar um serviço específico
docker compose restart auth-service

# Ver logs de um serviço
docker compose logs auth-service

# Ver logs em tempo real
docker compose logs -f auth-service
```

## URLs dos Serviços
- Auth Service: http://localhost:8001/docs
- Crisis Service: http://localhost:8005/docs
- Monitoring Service: http://localhost:8002/docs
- Maintenance Service: http://localhost:8003/docs
- Billing Service: http://localhost:8004/docs

## Primeiros Passos
1. Criar usuário em: http://localhost:8001/docs (POST /register)
2. Fazer login (POST /login)
3. Copiar o token
4. Autorizar-se clicando no botão 🔒 "Authorize"
5. Explorar as funcionalidades de cada serviço

## Banco de Dados
- PostgreSQL rodando na porta 5432
- Redis rodando na porta 6379
- Dados persistentes em volumes Docker
