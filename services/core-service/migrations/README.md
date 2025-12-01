# Migração: Fix ticket_number Length

## Problema
O campo `ticket_number` na tabela `support_tickets` estava definido como `VARCHAR(20)`, mas a função `generate_ticket_number()` estava gerando números de ticket maiores que 20 caracteres, causando erro SQL.

## Solução
1. ✅ Atualizado o modelo do banco de dados (`database_models.py`) para `VARCHAR(30)`
2. ✅ Ajustada a função `generate_ticket_number()` para gerar números menores (18 caracteres)
3. ⚠️ **É necessário atualizar o banco de dados existente**

## Como aplicar a migração

### Opção 1: Usando o script Python (Recomendado)
```bash
cd services/core-service
python migrations/fix_ticket_number.py
```

### Opção 2: Executando SQL diretamente
Conecte-se ao banco de dados PostgreSQL e execute:

```sql
ALTER TABLE support_tickets 
ALTER COLUMN ticket_number TYPE VARCHAR(30);
```

### Opção 3: Via Docker (se estiver usando Docker)
```bash
docker exec -i core-db psql -U core_user -d core_db < services/core-service/migrations/fix_ticket_number_length.sql
```

Ou conecte-se ao container do banco:
```bash
docker exec -it core-db psql -U core_user -d core_db
```

E então execute:
```sql
ALTER TABLE support_tickets ALTER COLUMN ticket_number TYPE VARCHAR(30);
```

## Verificação
Após executar a migração, verifique se funcionou:

```sql
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'support_tickets' 
AND column_name = 'ticket_number';
```

Deve retornar `character_maximum_length = 30`.

## Nota
A função `generate_ticket_number()` agora gera números no formato `TKT-YYMMDD-XXXXXX` (18 caracteres), que cabe perfeitamente no campo de 30 caracteres.

