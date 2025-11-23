#!/usr/bin/env python3
"""
Script para atualizar o tamanho da coluna ticket_number na tabela support_tickets
Executa: python fix_ticket_number.py
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import engine
    from sqlalchemy import text
    
    print("🔍 Conectando ao banco de dados...")
    
    with engine.connect() as conn:
        # Check current column size
        result = conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'support_tickets' 
            AND column_name = 'ticket_number'
        """))
        
        row = result.fetchone()
        if row:
            current_size = row[2]
            print(f"📊 Tamanho atual da coluna ticket_number: {current_size}")
            
            if current_size and current_size < 30:
                print("🔧 Atualizando coluna ticket_number para VARCHAR(30)...")
                conn.execute(text("""
                    ALTER TABLE support_tickets 
                    ALTER COLUMN ticket_number TYPE VARCHAR(30)
                """))
                conn.commit()
                print("✅ Coluna atualizada com sucesso!")
            else:
                print(f"✅ Coluna já está com tamanho adequado ({current_size})")
        else:
            print("⚠️  Tabela support_tickets não encontrada. Execute as migrações primeiro.")
            
        # Verify the change
        result = conn.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'support_tickets' 
            AND column_name = 'ticket_number'
        """))
        
        row = result.fetchone()
        if row:
            print(f"✅ Verificação: ticket_number agora é {row[1]}({row[2]})")
            
except Exception as e:
    print(f"❌ Erro ao atualizar banco de dados: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

