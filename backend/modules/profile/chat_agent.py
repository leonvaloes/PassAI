"""
Profile Chat Agent - IA Conversacional para Configuração de Perfil
"""
import logging
from typing import Dict, List, Optional
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Estados da conversa"""
    INICIO = "INICIO"
    EXPERIENCIAS = "EXPERIENCIAS"
    EXPERIENCIA_DETALHES = "EXPERIENCIA_DETALHES"
    HABILIDADES = "HABILIDADES"
    EDUCACAO = "EDUCACAO"
    REVISAO = "REVISAO"
    COMPLETO = "COMPLETO"


class ProfileChatAgent:
    """
    Agente de IA para guiar conversa de configuração de perfil
    """
    
    def __init__(self, llm_router, db):
        self.llm = llm_router
        self.db = db
        
    def start_conversation(self, user_id: str) -> Dict:
        """Inicia uma nova conversa"""
        conversation = {
            "user_id": user_id,
            "state": ConversationState.INICIO,
            "messages": [],
            "extracted_data": {
                "nome": "",
                "email": "",
                "telefone": "",
                "linkedin": "",
                "github": "",
                "cidade": "",
                "estado": "",
                "cargo_atual": "",
                "experiencias": [],
                "habilidades": [],
                "educacao": []
            },
            "current_experience_index": -1,
            "pending_fields": ["nome", "email", "telefone"]
        }
        
        # Salva no MongoDB
        conv_id = self.db.db.profile_conversations.insert_one(conversation).inserted_id
        
        initial_message = (
            "👋 Olá! Sou seu assistente de configuração de perfil profissional.\n\n"
            "Vou te fazer algumas perguntas para montar seu currículo perfeito. "
            "Não se preocupe, você pode editar tudo depois!\n\n"
            "Vamos começar pelo básico: **Qual é o seu nome completo?**"
        )
        
        self._add_message(conv_id, "ai", initial_message)
        
        return {
            "conversation_id": str(conv_id),
            "message": initial_message,
            "state": ConversationState.INICIO,
            "progress": 5
        }
    
    def process_message(self, conversation_id: str, user_message: str) -> Dict:
        """Processa mensagem do usuário e retorna resposta da IA"""
        # Carrega conversa
        conv = self.db.db.profile_conversations.find_one({"_id": conversation_id})
        if not conv:
            return {"error": "Conversa não encontrada"}
        
        # Adiciona mensagem do usuário
        self._add_message(conversation_id, "user", user_message)
        
        # Processa baseado no estado
        state = conv["state"]
        
        if state == ConversationState.INICIO:
            response = self._process_basic_info(conversation_id, conv, user_message)
        elif state == ConversationState.EXPERIENCIAS:
            response = self._process_experience_start(conversation_id, conv, user_message)
        elif state == ConversationState.EXPERIENCIA_DETALHES:
            response = self._process_experience_details(conversation_id, conv, user_message)
        elif state == ConversationState.HABILIDADES:
            response = self._process_skills(conversation_id, conv, user_message)
        elif state == ConversationState.EDUCACAO:
            response = self._process_education(conversation_id, conv, user_message)
        elif state == ConversationState.REVISAO:
            response = self._process_review(conversation_id, conv, user_message)
        else:
            response = {"message": "Conversa finalizada!", "state": ConversationState.COMPLETO}
        
        # Adiciona resposta da IA
        self._add_message(conversation_id, "ai", response["message"])
        
        return response
    
    def _process_basic_info(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Processa coleta de informações básicas"""
        pending = conv.get("pending_fields", [])
        extracted = conv["extracted_data"]
        
        if not pending:
            # Terminou dados básicos, vai para experiências
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {"state": ConversationState.EXPERIENCIAS}}
            )
            return {
                "message": (
                    f"✅ Perfeito, {extracted['nome'].split()[0]}!\n\n"
                    "Agora vamos falar sobre suas **experiências profissionais**.\n\n"
                    "Quantas empresas você trabalhou nos últimos anos? (Digite um número)"
                ),
                "state": ConversationState.EXPERIENCIAS,
                "progress": 20
            }
        
        # Extrai informação usando LLM
        current_field = pending[0]
        extraction_prompt = self._build_extraction_prompt(current_field, message)
        
        try:
            extracted_value = self.llm.llm.generate(extraction_prompt, temperature=0.3, max_tokens=200)
            extracted_value = extracted_value.strip().strip('"\'')
            
            # Salva valor extraído
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {
                    "$set": {f"extracted_data.{current_field}": extracted_value},
                    "$pull": {"pending_fields": current_field}
                }
            )
            
            # Próxima pergunta
            remaining = [f for f in pending if f != current_field]
            
            if not remaining:
                # Terminou básicos
                return self._process_basic_info(conv_id, self.db.db.profile_conversations.find_one({"_id": conv_id}), "")
            
            next_field = remaining[0]
            next_question = self._get_question_for_field(next_field, extracted_value)
            
            return {
                "message": next_question,
                "state": ConversationState.INICIO,
                "progress": 5 + (15 * (3 - len(remaining)) // 3)
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair {current_field}: {e}")
            return {
                "message": f"Desculpe, não entendi. Pode repetir o seu {current_field}?",
                "state": ConversationState.INICIO,
                "progress": 5
            }
    
    def _process_experience_start(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Inicia coleta de experiências"""
        # Extrai número de empresas
        try:
            num_empresas = int(message.strip())
        except:
            return {
                "message": "Por favor, digite apenas um número (ex: 2)",
                "state": ConversationState.EXPERIENCIAS,
                "progress": 20
            }
        
        if num_empresas == 0:
            # Pula para habilidades
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {"state": ConversationState.HABILIDADES}}
            )
            return {
                "message": (
                    "Entendido! Vamos então para suas **habilidades técnicas**.\n\n"
                    "Liste as tecnologias e ferramentas que você domina (ex: Java, React, AWS, PostgreSQL...)"
                ),
                "state": ConversationState.HABILIDADES,
                "progress": 60
            }
        
        # Inicia primeira experiência
        self.db.db.profile_conversations.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "state": ConversationState.EXPERIENCIA_DETALHES,
                    "current_experience_index": 0,
                    "total_experiences": num_empresas
                }
            }
        )
        
        return {
            "message": (
                f"Ótimo! Vamos detalhar cada uma. Começando pela **empresa mais recente**:\n\n"
                f"Qual o nome da empresa?"
            ),
            "state": ConversationState.EXPERIENCIA_DETALHES,
            "progress": 25
        }
    
    def _process_experience_details(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Coleta detalhes de uma experiência específica"""
        idx = conv["current_experience_index"]
        total = conv.get("total_experiences", 1)
        experiences = conv["extracted_data"]["experiencias"]
        
        # Se não existe experiência atual, cria uma nova
        if idx >= len(experiences):
            experiences.append({
                "empresa": "",
                "cargo": "",
                "periodo": "",
                "descricao": "",
                "realizacoes": [],
                "tecnologias": []
            })
        
        current_exp = experiences[idx]
        
        # Determina qual campo preencher
        if not current_exp["empresa"]:
            current_exp["empresa"] = message.strip()
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {f"extracted_data.experiencias.{idx}": current_exp}}
            )
            return {
                "message": f"Legal! E qual era seu cargo na {current_exp['empresa']}?",
                "state": ConversationState.EXPERIENCIA_DETALHES,
                "progress": 25 + (30 * idx // total)
            }
        
        if not current_exp["cargo"]:
            current_exp["cargo"] = message.strip()
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {f"extracted_data.experiencias.{idx}": current_exp}}
            )
            return {
                "message": "Quando você trabalhou lá? (ex: Janeiro 2022 - Dezembro 2024)",
                "state": ConversationState.EXPERIENCIA_DETALHES,
                "progress": 25 + (30 * idx // total)
            }
        
        if not current_exp["periodo"]:
            current_exp["periodo"] = message.strip()
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {f"extracted_data.experiencias.{idx}": current_exp}}
            )
            return {
                "message": (
                    f"Perfeito! Agora me conte sobre os **principais projetos** que você desenvolveu na {current_exp['empresa']}.\n\n"
                    "Liste os projetos/sistemas principais (pode ser em formato de lista ou texto corrido):"
                ),
                "state": ConversationState.EXPERIENCIA_DETALHES,
                "progress": 25 + (30 * idx // total)
            }
        
        if not current_exp["realizacoes"]:
            # Usa LLM para extrair projetos da descrição
            projects = self._extract_projects_from_text(message)
            current_exp["realizacoes"] = projects
            current_exp["descricao"] = message[:200]  # Resumo
            
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {f"extracted_data.experiencias.{idx}": current_exp}}
            )
            
            # Próxima empresa ou finaliza
            if idx + 1 < total:
                self.db.db.profile_conversations.update_one(
                    {"_id": conv_id},
                    {"$set": {"current_experience_index": idx + 1}}
                )
                return {
                    "message": (
                        f"✅ Experiência na {current_exp['empresa']} registrada!\n\n"
                        f"Agora vamos para a empresa {idx + 2}/{total}. Qual o nome?"
                    ),
                    "state": ConversationState.EXPERIENCIA_DETALHES,
                    "progress": 30 + (30 * (idx + 1) // total)
                }
            else:
                # Terminou experiências
                self.db.db.profile_conversations.update_one(
                    {"_id": conv_id},
                    {"$set": {"state": ConversationState.HABILIDADES}}
                )
                return {
                    "message": (
                        f"✅ Todas as experiências registradas!\n\n"
                        "Agora, quais são suas **habilidades técnicas**?\n\n"
                        "Liste as tecnologias que você domina (ex: Java, Python, React, AWS, Docker...):"
                    ),
                    "state": ConversationState.HABILIDADES,
                    "progress": 60
                }
        
        return {"message": "Erro no fluxo", "state": ConversationState.EXPERIENCIA_DETALHES, "progress": 30}
    
    def _process_skills(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Processa habilidades"""
        # Extrai lista de habilidades
        skills = self._extract_skills_from_text(message)
        
        self.db.db.profile_conversations.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "extracted_data.habilidades": skills,
                    "state": ConversationState.EDUCACAO
                }
            }
        )
        
        return {
            "message": (
                f"✅ Registrei {len(skills)} habilidades!\n\n"
                "Por último, sobre sua **formação acadêmica**:\n\n"
                "Qual curso você fez? (ex: Bacharelado em Ciência da Computação - USP)"
            ),
            "state": ConversationState.EDUCACAO,
            "progress": 80
        }
    
    def _process_education(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Processa educação"""
        # Extrai educação
        education = self._extract_education_from_text(message)
        
        self.db.db.profile_conversations.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "extracted_data.educacao": [education],
                    "state": ConversationState.REVISAO
                }
            }
        )
        
        # Monta resumo para revisão
        extracted = conv["extracted_data"]
        extracted["educacao"] = [education]
        
        summary = self._build_profile_summary(extracted)
        
        return {
            "message": (
                "✅ Perfil completo! Aqui está um resumo:\n\n"
                f"{summary}\n\n"
                "Está tudo certo? Digite **SIM** para salvar ou **NÃO** para editar."
            ),
            "state": ConversationState.REVISAO,
            "progress": 95
        }
    
    def _process_review(self, conv_id: str, conv: Dict, message: str) -> Dict:
        """Processa revisão final"""
        if message.strip().upper() in ["SIM", "S", "YES", "OK"]:
            # Salva perfil final
            extracted = conv["extracted_data"]
            
            # Upsert no user_profiles
            self.db.db.user_profiles.update_one(
                {"profile_name": extracted["nome"].split()[0]},  # Primeiro nome como ID
                {"$set": extracted},
                upsert=True
            )
            
            self.db.db.profile_conversations.update_one(
                {"_id": conv_id},
                {"$set": {"state": ConversationState.COMPLETO}}
            )
            
            return {
                "message": (
                    "🎉 **Perfil salvo com sucesso!**\n\n"
                    "Agora você pode gerar currículos personalizados para cada vaga!\n\n"
                    "Boa sorte na sua jornada profissional! 🚀"
                ),
                "state": ConversationState.COMPLETO,
                "progress": 100
            }
        else:
            return {
                "message": (
                    "Sem problemas! O que você gostaria de editar?\n"
                    "(Digite 'nome', 'experiencias', 'habilidades' ou 'educacao')"
                ),
                "state": ConversationState.REVISAO,
                "progress": 95
            }
    
    # Métodos auxiliares
    
    def _add_message(self, conv_id: str, role: str, content: str):
        """Adiciona mensagem à conversa"""
        from datetime import datetime
        self.db.db.profile_conversations.update_one(
            {"_id": conv_id},
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
    
    def _build_extraction_prompt(self, field: str, message: str) -> str:
        """Constrói prompt para extrair campo específico"""
        prompts = {
            "email": f"Extraia APENAS o email desta mensagem: '{message}'. Responda só o email, nada mais.",
            "telefone": f"Extraia APENAS o telefone desta mensagem: '{message}'. Formato: (XX) XXXXX-XXXX",
            "linkedin": f"Extraia APENAS o LinkedIn desta mensagem: '{message}'. Pode ser URL ou username.",
            "github": f"Extraia APENAS o GitHub desta mensagem: '{message}'. Pode ser URL ou username.",
            "cidade": f"Extraia APENAS a cidade desta mensagem: '{message}'.",
            "estado": f"Extraia APENAS o estado/UF desta mensagem: '{message}'.",
            "cargo_atual": f"Extraia APENAS o cargo desta mensagem: '{message}'."
        }
        return prompts.get(field, f"Extraia {field} de: {message}")
    
    def _get_question_for_field(self, field: str, previous_answer: str) -> str:
        """Retorna pergunta apropriada para cada campo"""
        questions = {
            "email": f"Ótimo, {previous_answer}! Qual é o seu **email** de contato?",
            "telefone": "E o seu **telefone**? (com DDD)",
            "linkedin": "Você tem **LinkedIn**? (pode colar o link ou só o username)",
            "github": "E **GitHub**? (opcional, deixe em branco se não tiver)",
            "cidade": "Em qual **cidade** você mora?",
            "estado": "E o **estado**?",
            "cargo_atual": "Qual é o seu **cargo atual**?"
        }
        return questions.get(field, f"Me fale sobre {field}:")
    
    def _extract_projects_from_text(self, text: str) -> List[str]:
        """Extrai projetos de texto livre usando LLM"""
        prompt = f"""
Extraia os projetos/sistemas mencionados neste texto e liste-os em formato JSON array.
Cada item deve ser uma descrição clara do projeto.

Texto: {text}

Responda APENAS um JSON array, exemplo: ["Projeto 1: descrição", "Projeto 2: descrição"]
"""
        try:
            response = self.llm.llm.generate(prompt, temperature=0.3, max_tokens=500)
            projects = json.loads(response)
            return projects if isinstance(projects, list) else [text]
        except:
            # Fallback: quebra por linhas ou pontos
            return [p.strip() for p in text.split('\n') if p.strip()] or [text]
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extrai habilidades de texto"""
        # Separadores comuns
        separators = [',', ';', '\n', ' - ']
        for sep in separators:
            if sep in text:
                return [s.strip() for s in text.split(sep) if s.strip()]
        
        # Fallback: extrai palavras-chave comuns
        common_tech = ["Java", "Python", "JavaScript", "React", "Angular", "Vue", "Spring", "Django", 
                       "Node", "AWS", "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "MySQL"]
        found = [tech for tech in common_tech if tech.lower() in text.lower()]
        return found if found else [text]
    
    def _extract_education_from_text(self, text: str) -> Dict:
        """Extrai educação de texto"""
        return {
            "instituicao": text.split('-')[1].strip() if '-' in text else "Universidade",
            "curso": text.split('-')[0].strip() if '-' in text else text,
            "periodo": ""
        }
    
    def _build_profile_summary(self, data: Dict) -> str:
        """Constrói resumo do perfil para revisão"""
        summary = f"**👤 {data['nome']}**\n"
        summary += f"📧 {data['email']}\n"
        summary += f"📱 {data['telefone']}\n\n"
        
        summary += f"**💼 Experiências:** {len(data['experiencias'])} empresas\n"
        for exp in data['experiencias']:
            summary += f"  • {exp['empresa']} - {exp['cargo']} ({exp['periodo']})\n"
        
        summary += f"\n**🛠️ Habilidades:** {len(data['habilidades'])} tecnologias\n"
        summary += f"  {', '.join(data['habilidades'][:10])}\n"
        
        if data['educacao']:
            edu = data['educacao'][0]
            summary += f"\n**🎓 Formação:** {edu['curso']}\n"
        
        return summary
