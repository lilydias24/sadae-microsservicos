"""
AI Support Assistant - Sistema de IA para Atendimento ao Cliente
Gera respostas inteligentes baseadas na base de conhecimento e contexto do ticket
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from difflib import SequenceMatcher


class AISupportAssistant:
    """Assistente de IA para suporte ao cliente"""
    
    # Palavras-chave comuns e suas categorias
    KEYWORD_CATEGORIES = {
        'billing': ['conta', 'fatura', 'pagamento', 'cobrança', 'valor', 'tarifa', 'preço', 'segunda via', '2ª via'],
        'technical': ['vazamento', 'pressão', 'água', 'esgoto', 'medidor', 'hidrômetro', 'reparo', 'manutenção'],
        'request': ['religação', 'ligação', 'corte', 'solicitação', 'pedido', 'serviço'],
        'emergency': ['emergência', 'urgente', 'vazamento', 'corte', 'sem água', 'falta de água'],
        'information': ['consulta', 'informação', 'como', 'dúvida', 'pergunta']
    }
    
    # Chit Chat - Respostas conversacionais para perguntas comuns
    CHIT_CHAT_RESPONSES = {
        'saudacoes': {
            'patterns': ['oi', 'olá', 'ola', 'oie', 'eai', 'e aí', 'bom dia', 'boa tarde', 'boa noite', 'hey', 'hi', 'hello'],
            'responses': [
                'Olá! 👋 Bem-vindo ao atendimento do SADAE. Como posso ajudá-lo hoje?',
                'Oi! 😊 Estou aqui para ajudar. Em que posso ser útil?',
                'Olá! 👋 Fico feliz em ajudar. O que você precisa?',
                'Oi! 😊 Como posso ajudar você hoje?'
            ]
        },
        'agradecimentos': {
            'patterns': ['obrigado', 'obrigada', 'valeu', 'grato', 'grata', 'thanks', 'thank you'],
            'responses': [
                'De nada! 😊 Fico feliz em ajudar. Precisa de mais alguma coisa?',
                'Por nada! 😊 Estou sempre aqui para ajudar. Mais alguma dúvida?',
                'Imagina! 😊 Fico feliz em poder ajudar. Precisa de mais informações?'
            ]
        },
        'despedidas': {
            'patterns': ['tchau', 'até', 'até logo', 'até mais', 'bye', 'falou', 'flw'],
            'responses': [
                'Tchau! 👋 Foi um prazer ajudar. Volte sempre que precisar!',
                'Até logo! 😊 Qualquer dúvida, estou aqui!',
                'Tchau! 👋 Tenha um ótimo dia!'
            ]
        },
        'status': {
            'patterns': ['tudo bem', 'tudo bom', 'como vai', 'como está', 'beleza', 'tranquilo'],
            'responses': [
                'Tudo ótimo! 😊 Pronto para ajudar você. E você, como está?',
                'Estou bem, obrigado! 😊 Como posso ajudar você hoje?',
                'Tudo certo! 😊 Em que posso ser útil?'
            ]
        }
    }
    
    # Perguntas comuns e respostas diretas
    COMMON_QUESTIONS = {
        'conta_agua': {
            'patterns': ['como consultar', 'ver conta', 'minha conta', 'consulta conta', 'consultar conta'],
            'response': '''💳 **Consulta de Conta de Água**

Para consultar sua conta, você pode:

1. **Acessar o Dashboard**
   - Vá em Dashboard > Faturamento
   - Informe seu CPF/CNPJ e número de cliente

2. **Visualizar Informações**
   - Faturas abertas e pagas
   - Histórico de consumo
   - Detalhes de cada fatura

3. **Baixar 2ª Via**
   - Clique em "Baixar 2ª Via" na fatura desejada
   - O documento será gerado em PDF

Precisa de ajuda com algum passo específico?'''
        },
        'segunda_via': {
            'patterns': ['segunda via', '2ª via', 'segunda via da fatura', 'baixar fatura', 'imprimir fatura'],
            'response': '''📄 **2ª Via de Fatura**

Para baixar a 2ª via da sua fatura:

1. Acesse **Dashboard > Faturamento**
2. Localize a fatura desejada
3. Clique no botão **"Baixar 2ª Via"**
4. O PDF será gerado automaticamente

A 2ª via pode ser usada para:
- Pagamento em bancos e lotéricas
- Comprovação de pagamento
- Declaração de imposto de renda

Conseguiu baixar? Precisa de mais ajuda?'''
        },
        'vazamento': {
            'patterns': ['vazamento', 'vazando', 'água vazando', 'vazamento de água', 'vazou'],
            'response': '''🚨 **Reportar Vazamento**

Se você identificou um vazamento, siga estes passos:

1. **Ações Imediatas**
   - Feche o registro principal da água
   - Sinalize a área para evitar acidentes
   - Evite contato com a água vazada

2. **Reportar o Vazamento**
   - Acesse **Serviços Públicos > Reportar Vazamento**
   - Informe a localização exata
   - Descreva a intensidade do vazamento
   - Adicione fotos se possível

3. **Urgência**
   - Vazamentos grandes são tratados como emergência
   - Nossa equipe será acionada imediatamente

É um vazamento urgente? Posso criar um ticket de emergência agora!'''
        },
        'religacao': {
            'patterns': ['religação', 'religar', 'religar água', 'ligar água', 'religação de água'],
            'response': '''🔧 **Solicitar Religação de Água**

Para solicitar a religação, você precisa:

1. **Regularizar Pendências**
   - Quitar todas as faturas em atraso
   - Pagar taxas de corte (se houver)
   - Verificar se não há débitos pendentes

2. **Documentos Necessários**
   - Número do imóvel/cliente
   - Comprovante de pagamento das pendências
   - CPF/CNPJ do titular
   - Endereço completo

3. **Solicitar**
   - Acesse **Atendimento > Novo Ticket**
   - Categoria: "Solicitação"
   - Assunto: "Religação de Água"

Deseja que eu crie um ticket para sua solicitação agora?'''
        },
        'tarifas': {
            'patterns': ['tarifa', 'preço', 'valor', 'quanto custa', 'quanto é', 'preço da água'],
            'response': '''💰 **Tarifas de Água e Esgoto**

As tarifas variam conforme:

1. **Faixa de Consumo**
   - Até 10m³: Tarifa social
   - 11-20m³: Tarifa residencial básica
   - 21-30m³: Tarifa residencial média
   - Acima de 30m³: Tarifa residencial alta

2. **Categoria**
   - Residencial
   - Comercial
   - Industrial
   - Pública

3. **Localização**
   - Diferentes regiões podem ter tarifas específicas

**Para consultar sua tarifa:**
- Acesse **Serviços Públicos > Informações**
- Use a calculadora de tarifas no app
- Consulte sua última fatura

Quer simular o valor da sua próxima fatura?'''
        },
        'horario_atendimento': {
            'patterns': ['horário', 'horario', 'funcionamento', 'atendimento', 'aberto', 'fecha'],
            'response': '''🕐 **Horário de Atendimento**

Nossos canais de atendimento:

**Atendimento Online (Chat)**
- 24 horas por dia, 7 dias por semana
- Respostas automáticas imediatas

**Atendimento Presencial**
- Segunda a Sexta: 8h às 17h
- Sábado: 8h às 12h

**Telefone**
- Segunda a Sexta: 8h às 18h
- Número: (XX) XXXX-XXXX

**Emergências**
- 24 horas por dia
- Vazamentos, cortes, problemas urgentes

Precisa de atendimento presencial ou telefônico?'''
        }
    }
    
    # Padrões de perguntas comuns
    QUESTION_PATTERNS = [
        (r'como (consultar|ver|acessar|baixar)', 'consulta'),
        (r'quanto (custa|vale|é)', 'valor'),
        (r'onde (pago|consigo|encontro)', 'localização'),
        (r'quando (será|vai|acontece)', 'prazo'),
        (r'por que (não|está)', 'problema'),
        (r'o que (fazer|acontece|é)', 'ação'),
    ]
    
    def __init__(self):
        self.confidence_threshold = 0.6  # Limiar mínimo de confiança para resposta
    
    def generate_response(
        self,
        user_message: str,
        ticket_context: Dict[str, Any],
        knowledge_base: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera uma resposta da IA baseada na mensagem do usuário, contexto do ticket e base de conhecimento
        
        Args:
            user_message: Mensagem do usuário
            ticket_context: Informações do ticket (categoria, título, descrição)
            knowledge_base: Lista de artigos da base de conhecimento
            conversation_history: Histórico de mensagens anteriores
            
        Returns:
            Dict com resposta, confiança, artigos relacionados e sugestões
        """
        if not user_message or len(user_message.strip()) < 3:
            return {
                'response': None,
                'confidence': 0.0,
                'reason': 'Mensagem muito curta ou vazia'
            }
        
        # Normalizar mensagem
        normalized_message = self._normalize_text(user_message)
        
        # 1. Verificar Chit Chat primeiro (saudações, agradecimentos, etc)
        chit_chat_response = self._check_chit_chat(normalized_message)
        if chit_chat_response:
            return {
                'response': chit_chat_response,
                'confidence': 0.95,  # Alta confiança para chit chat
                'relevant_articles': [],
                'suggestions': self._generate_chit_chat_suggestions(),
                'category': 'chit_chat'
            }
        
        # 2. Verificar perguntas comuns
        common_question_response = self._check_common_questions(normalized_message)
        if common_question_response:
            return {
                'response': common_question_response,
                'confidence': 0.90,  # Alta confiança para perguntas comuns
                'relevant_articles': [],
                'suggestions': self._generate_suggestions(ticket_context, []),
                'category': ticket_context.get('category', 'information')
            }
        
        # 3. Buscar na base de conhecimento
        relevant_articles = self._find_relevant_articles(
            normalized_message,
            ticket_context,
            knowledge_base
        )
        
        # Se não encontrou artigos relevantes, tentar resposta genérica
        if not relevant_articles or relevant_articles[0]['score'] < 0.3:
            return self._generate_generic_response(normalized_message, ticket_context)
        
        # Gerar resposta baseada no artigo mais relevante
        best_article = relevant_articles[0]
        response = self._generate_response_from_article(
            user_message,
            best_article['article'],
            ticket_context,
            conversation_history
        )
        
        # Calcular confiança
        confidence = min(best_article['score'], 0.95)  # Cap em 95%
        
        # Gerar sugestões de próximos passos
        suggestions = self._generate_suggestions(
            ticket_context,
            relevant_articles[:3]
        )
        
        return {
            'response': response,
            'confidence': confidence,
            'relevant_articles': [
                {
                    'id': art['article'].get('id'),
                    'title': art['article'].get('title'),
                    'score': art['score']
                }
                for art in relevant_articles[:3]
            ],
            'suggestions': suggestions,
            'category': ticket_context.get('category', 'information')
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação"""
        # Converter para minúsculas
        text = text.lower()
        # Remover acentos básicos (simplificado)
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e',
            'í': 'i',
            'ó': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ü': 'u',
            'ç': 'c'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        # Remover pontuação extra
        text = re.sub(r'[^\w\s]', ' ', text)
        # Remover espaços múltiplos
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _find_relevant_articles(
        self,
        message: str,
        ticket_context: Dict[str, Any],
        knowledge_base: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Encontra artigos relevantes da base de conhecimento"""
        scored_articles = []
        
        # Combinar contexto do ticket com a mensagem
        ticket_text = f"{ticket_context.get('title', '')} {ticket_context.get('description', '')} {message}"
        ticket_category = ticket_context.get('category', 'information')
        
        for article in knowledge_base:
            if not article.get('is_published', True):
                continue
            
            score = 0.0
            
            # 1. Match de categoria (peso alto)
            if article.get('category') == ticket_category:
                score += 0.3
            
            # 2. Similaridade de título
            title_similarity = self._text_similarity(
                message,
                article.get('title', '')
            )
            score += title_similarity * 0.3
            
            # 3. Similaridade de conteúdo
            content = article.get('content', '')
            content_similarity = self._text_similarity(
                message,
                content[:500]  # Primeiros 500 caracteres
            )
            score += content_similarity * 0.2
            
            # 4. Match de palavras-chave
            keywords = article.get('keywords', [])
            tags = article.get('tags', [])
            all_keywords = keywords + tags
            
            keyword_matches = sum(
                1 for kw in all_keywords
                if self._normalize_text(kw) in message or message in self._normalize_text(kw)
            )
            if all_keywords:
                score += min(keyword_matches / len(all_keywords), 1.0) * 0.15
            
            # 5. Match de tags específicas
            for tag in tags:
                tag_normalized = self._normalize_text(tag)
                if tag_normalized in message:
                    score += 0.05
            
            # 6. Bônus para artigos em destaque
            if article.get('is_featured', False):
                score += 0.05
            
            if score > 0.2:  # Limiar mínimo
                scored_articles.append({
                    'article': article,
                    'score': min(score, 1.0)
                })
        
        # Ordenar por score
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        return scored_articles[:5]  # Top 5
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos usando SequenceMatcher"""
        text1_norm = self._normalize_text(text1)
        text2_norm = self._normalize_text(text2)
        
        # Similaridade geral
        similarity = SequenceMatcher(None, text1_norm, text2_norm).ratio()
        
        # Bônus para palavras em comum
        words1 = set(text1_norm.split())
        words2 = set(text2_norm.split())
        if words1 and words2:
            common_words = words1.intersection(words2)
            word_similarity = len(common_words) / max(len(words1), len(words2))
            similarity = (similarity + word_similarity) / 2
        
        return similarity
    
    def _generate_response_from_article(
        self,
        user_message: str,
        article: Dict[str, Any],
        ticket_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None
    ) -> str:
        """Gera resposta baseada em um artigo da base de conhecimento"""
        article_content = article.get('content', '')
        article_title = article.get('title', '')
        
        # Extrair informações principais do artigo
        sentences = article_content.split('.')
        main_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]
        
        # Construir resposta personalizada
        response_parts = []
        
        # Saudação contextual
        if self._is_question(user_message):
            response_parts.append("Com base na sua pergunta, aqui está a informação:")
        else:
            response_parts.append("Com base no seu caso, posso ajudar com o seguinte:")
        
        # Conteúdo principal
        if main_sentences:
            response_parts.append(' '.join(main_sentences))
        else:
            # Fallback: usar conteúdo completo truncado
            response_parts.append(article_content[:300] + '...' if len(article_content) > 300 else article_content)
        
        # Adicionar referência ao artigo
        response_parts.append(f"\n\nPara mais detalhes, consulte: {article_title}")
        
        return ' '.join(response_parts)
    
    def _is_question(self, text: str) -> bool:
        """Verifica se o texto é uma pergunta"""
        question_words = ['como', 'quando', 'onde', 'por que', 'porque', 'qual', 'quais', 'o que', 'quanto']
        text_lower = self._normalize_text(text)
        return any(text_lower.startswith(word) for word in question_words) or '?' in text
    
    def _generate_generic_response(
        self,
        message: str,
        ticket_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Gera resposta genérica quando não há artigos relevantes"""
        category = ticket_context.get('category', 'information')
        
        generic_responses = {
            'billing': "Entendo sua dúvida sobre faturamento. Nossa equipe está analisando seu caso e entrará em contato em breve. Enquanto isso, você pode consultar sua conta na área do cliente.",
            'technical': "Recebi sua solicitação técnica. Nossa equipe especializada está verificando o problema e entrará em contato para resolver sua questão.",
            'request': "Sua solicitação foi registrada e está sendo processada. Nossa equipe entrará em contato em breve para dar continuidade ao seu pedido.",
            'emergency': "Entendo que é uma situação urgente. Nossa equipe de emergência foi acionada e entrará em contato imediatamente.",
            'information': "Obrigado pela sua mensagem. Nossa equipe está preparando uma resposta completa para sua dúvida e entrará em contato em breve."
        }
        
        response = generic_responses.get(category, generic_responses['information'])
        
        return {
            'response': response,
            'confidence': 0.4,
            'reason': 'Nenhum artigo relevante encontrado na base de conhecimento'
        }
    
    def _generate_suggestions(
        self,
        ticket_context: Dict[str, Any],
        relevant_articles: List[Dict[str, Any]]
    ) -> List[str]:
        """Gera sugestões de próximos passos"""
        suggestions = []
        
        category = ticket_context.get('category', 'information')
        
        if category == 'billing':
            suggestions.extend([
                "Consultar minha conta",
                "Baixar 2ª via de fatura",
                "Ver histórico de pagamentos"
            ])
        elif category == 'technical':
            suggestions.extend([
                "Reportar problema técnico",
                "Verificar status de reparo",
                "Agendar visita técnica"
            ])
        elif category == 'request':
            suggestions.extend([
                "Solicitar religação",
                "Verificar status da solicitação",
                "Consultar documentação necessária"
            ])
        
        # Adicionar sugestões baseadas nos artigos
        if relevant_articles:
            for article in relevant_articles[:2]:
                title = article['article'].get('title', '')
                if title and len(suggestions) < 5:
                    suggestions.append(f"Ver: {title}")
        
        return suggestions[:5]
    
    def _check_chit_chat(self, normalized_message: str) -> Optional[str]:
        """Verifica se a mensagem é chit chat e retorna resposta apropriada"""
        import random
        
        for category, data in self.CHIT_CHAT_RESPONSES.items():
            for pattern in data['patterns']:
                if pattern in normalized_message:
                    return random.choice(data['responses'])
        
        return None
    
    def _check_common_questions(self, normalized_message: str) -> Optional[str]:
        """Verifica se a mensagem corresponde a uma pergunta comum"""
        for question_key, question_data in self.COMMON_QUESTIONS.items():
            for pattern in question_data['patterns']:
                if pattern in normalized_message:
                    return question_data['response']
        
        return None
    
    def _generate_chit_chat_suggestions(self) -> List[str]:
        """Gera sugestões para chit chat"""
        return [
            "Consultar minha conta",
            "Baixar 2ª via de fatura",
            "Reportar vazamento",
            "Solicitar religação"
        ]
    
    def should_escalate_to_agent(
        self,
        user_message: str,
        confidence: float,
        conversation_history: List[Dict[str, Any]] = None
    ) -> bool:
        """Determina se a conversa deve ser escalada para um agente humano"""
        # Não escalar chit chat ou perguntas comuns (alta confiança)
        if confidence >= 0.85:
            return False
        
        # Escalar se confiança muito baixa
        if confidence < 0.3:
            return True
        
        # Escalar se muitas mensagens sem resolução
        if conversation_history:
            client_messages = [m for m in conversation_history if m.get('message_type') == 'client']
            if len(client_messages) > 5:
                return True
        
        # Escalar se palavras-chave de urgência
        urgent_keywords = ['urgente', 'emergência', 'não funciona', 'problema grave', 'preciso de ajuda']
        message_lower = self._normalize_text(user_message)
        if any(keyword in message_lower for keyword in urgent_keywords):
            return True
        
        return False

