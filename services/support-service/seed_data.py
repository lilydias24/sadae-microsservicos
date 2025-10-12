import os
import sys
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from database import get_database_url, create_engine
from database_models import SupportAgent, KnowledgeBaseArticle, SupportTicket, TicketMessage

def create_sample_data():
    """Create sample data for support service"""
    
    # Create database connection
    DATABASE_URL = get_database_url("support")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create sample support agents
        agents = [
            SupportAgent(
                user_id=100,  # Assuming these user IDs exist in auth service
                name="Ana Silva",
                email="ana.silva@sadae.gov.br",
                department="Atendimento Geral",
                specialties='["billing", "technical"]',
                is_active=True,
                max_concurrent_tickets=15,
                current_ticket_count=3,
                total_tickets_resolved=245,
                average_rating=4.7,
                average_response_time=2.3
            ),
            SupportAgent(
                user_id=101,
                name="Carlos Oliveira",
                email="carlos.oliveira@sadae.gov.br",
                department="Suporte Técnico",
                specialties='["technical", "emergency"]',
                is_active=True,
                max_concurrent_tickets=12,
                current_ticket_count=5,
                total_tickets_resolved=189,
                average_rating=4.5,
                average_response_time=1.8
            ),
            SupportAgent(
                user_id=102,
                name="Mariana Santos",
                email="mariana.santos@sadae.gov.br",
                department="Atendimento Comercial",
                specialties='["billing", "complaint"]',
                is_active=True,
                max_concurrent_tickets=20,
                current_ticket_count=8,
                total_tickets_resolved=298,
                average_rating=4.8,
                average_response_time=3.1
            )
        ]
        
        for agent in agents:
            existing = db.query(SupportAgent).filter(SupportAgent.user_id == agent.user_id).first()
            if not existing:
                db.add(agent)
        
        # Create sample knowledge base articles
        articles = [
            KnowledgeBaseArticle(
                title="Como ler sua conta de água",
                content="""
                Para entender sua conta de água, observe os seguintes elementos:
                
                1. **Período de Consumo**: Indica o período de medição do consumo
                2. **Leitura Anterior e Atual**: Valores registrados no hidrômetro
                3. **Consumo em m³**: Diferença entre as leituras
                4. **Valor a Pagar**: Total devido incluindo taxas e impostos
                
                **Dicas importantes:**
                - Verifique se há vazamentos verificando o hidrômetro com todos os registros fechados
                - Compare o consumo com meses anteriores para identificar alterações
                - Em caso de dúvidas, entre em contato conosco
                """,
                category="billing",
                author_id=100,
                author_name="Ana Silva",
                view_count=1250,
                helpful_count=892,
                not_helpful_count=23,
                is_featured=True,
                is_published=True
            ),
            KnowledgeBaseArticle(
                title="Falta de água em sua região",
                content="""
                Se você está enfrentando falta de água, siga estes passos:
                
                1. **Verifique se é um problema local**: Confirme com vizinhos se também estão sem água
                2. **Consulte nossos canais oficiais**: Site e redes sociais para informações sobre manutenção
                3. **Verifique seu registro**: Certifique-se de que está aberto
                4. **Reporte o problema**: Se não há manutenção programada, abra um chamado
                
                **Manutenções programadas:**
                - São comunicadas com antecedência
                - Geralmente ocorrem durante a madrugada
                - Podem durar de 4 a 8 horas
                
                **Em emergências:**
                - Ligue para nosso telefone de emergência: 0800-123-4567
                - Disponível 24 horas por dia
                """,
                category="technical",
                author_id=101,
                author_name="Carlos Oliveira",
                view_count=2341,
                helpful_count=1876,
                not_helpful_count=45,
                is_featured=True,
                is_published=True
            ),
            KnowledgeBaseArticle(
                title="Como contestar sua conta",
                content="""
                Para contestar valores em sua conta de água:
                
                1. **Reúna documentação**:
                   - Cópia da conta contestada
                   - Fotos do hidrômetro
                   - Comprovante de vazamentos (se aplicável)
                
                2. **Prazos para contestação**:
                   - Até 30 dias após o vencimento
                   - Contestações após este prazo podem não ser aceitas
                
                3. **Canais para contestação**:
                   - Portal online do cidadão
                   - Presencialmente nas unidades de atendimento
                   - Por telefone: 0800-987-6543
                
                4. **Análise**:
                   - Prazo de resposta: até 15 dias úteis
                   - Vistoria técnica pode ser necessária
                   - Você será notificado do resultado
                """,
                category="billing",
                author_id=102,
                author_name="Mariana Santos",
                view_count=987,
                helpful_count=743,
                not_helpful_count=31,
                is_featured=False,
                is_published=True
            ),
            KnowledgeBaseArticle(
                title="Vazamentos: como identificar e proceder",
                content="""
                **Identificando vazamentos:**
                
                1. **Teste do hidrômetro**: Com todos os registros fechados, verifique se o ponteiro se move
                2. **Sinais visuais**: Manchas de umidade, poças, rachaduras
                3. **Conta alta**: Aumento inexplicável no consumo
                
                **Tipos de vazamento:**
                - **Internos**: Responsabilidade do proprietário
                - **Externos**: Responsabilidade da SADAE
                - **Na via pública**: Ligue 0800-123-4567
                
                **Procedimentos:**
                1. Feche o registro imediatamente
                2. Se for vazamento interno, contrate um encanador
                3. Se for externo, abra um chamado urgente
                4. Guarde comprovantes para análise de conta
                
                **Dica importante:** Vazamentos podem gerar multas ambientais além do desperdício de água.
                """,
                category="technical",
                author_id=101,
                author_name="Carlos Oliveira",
                view_count=1567,
                helpful_count=1234,
                not_helpful_count=28,
                is_featured=True,
                is_published=True
            ),
            KnowledgeBaseArticle(
                title="Parcelamento de débitos",
                content="""
                **Condições para parcelamento:**
                
                - Débito mínimo de R$ 100,00
                - Máximo de 12 parcelas
                - Entrada mínima de 20% do valor total
                - Juros de 1% ao mês
                
                **Documentos necessários:**
                - CPF ou CNPJ
                - Comprovante de residência
                - Contas em débito
                
                **Como solicitar:**
                1. Portal online (mais rápido)
                2. Unidades de atendimento
                3. Central telefônica
                
                **Importante:**
                - Não interrompa os pagamentos
                - Inadimplência cancela o parcelamento
                - Novas contas devem ser pagas em dia
                """,
                category="billing",
                author_id=102,
                author_name="Mariana Santos",
                view_count=2134,
                helpful_count=1876,
                not_helpful_count=67,
                is_featured=False,
                is_published=True
            )
        ]
        
        for article in articles:
            existing = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.title == article.title).first()
            if not existing:
                db.add(article)
        
        # Create sample tickets (optional - these could be created by users)
        sample_tickets = [
            SupportTicket(
                ticket_number="TK-20240922-0001",
                title="Conta com valor muito alto",
                description="Minha conta veio com um valor muito alto este mês. Normalmente pago cerca de R$ 45,00 e desta vez veio R$ 180,00. Não houve mudança no consumo da casa.",
                category="billing",
                priority="medium",
                status="open",
                client_id=1,
                client_name="João Silva",
                client_email="joao.silva@email.com",
                created_at=datetime.utcnow()
            ),
            SupportTicket(
                ticket_number="TK-20240922-0002",
                title="Sem água há 2 dias",
                description="Estou sem água em casa há 2 dias. Já verifiquei com os vizinhos e eles também estão sem água. Não encontrei informações sobre manutenção no site.",
                category="technical",
                priority="high",
                status="in_progress",
                client_id=2,
                client_name="Maria Santos",
                client_email="maria.santos@email.com",
                assigned_agent_id=101,
                assigned_agent_name="Carlos Oliveira",
                created_at=datetime.utcnow()
            )
        ]
        
        for ticket in sample_tickets:
            existing = db.query(SupportTicket).filter(SupportTicket.ticket_number == ticket.ticket_number).first()
            if not existing:
                db.add(ticket)
        
        db.commit()
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()