#!/usr/bin/env python3
"""
Script para corrigir a autenticação no support-service
"""

import re

def fix_auth_file():
    """Corrige as definições de autenticação no main.py"""
    file_path = 'services/support-service/main.py'
    
    # Ler o arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Padrão para encontrar as linhas problemáticas
    pattern = r'authorization: str = Depends\(lambda request: request\.headers\.get\("Authorization"\)\),'
    replacement = r'credentials: HTTPAuthorizationCredentials = Depends(security),'
    
    # Substituir todas as ocorrências
    content = re.sub(pattern, replacement, content)
    
    # Padrão para corrigir as chamadas da função
    pattern2 = r'await verify_user_token\(authorization\)'
    replacement2 = r'await verify_user_token(f"Bearer {credentials.credentials}")'
    
    content = re.sub(pattern2, replacement2, content)
    
    # Escrever o arquivo de volta
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Arquivo corrigido!")

if __name__ == "__main__":
    fix_auth_file()