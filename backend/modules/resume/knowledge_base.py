"""
Knowledge Base - RAG system with video processing
"""
import logging
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from database.models import ATSType
from database.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    RAG Knowledge Base for Resume Optimization
    
    Features:
    - Video processing (Whisper transcription)
    - Semantic chunking
    - Rule extraction via LLM
    - Vector search with ChromaDB
    - ATS-specific knowledge retrieval
    """
    
    def __init__(
        self,
        chroma_path: str = "data/chromadb",
        embedding_model: str = "all-MiniLM-L6-v2",
        whisper_model=None,
        llm_router=None
    ):
        """
        Initialize Knowledge Base
        
        Args:
            chroma_path: Path to ChromaDB storage
            embedding_model: SentenceTransformers model name
            whisper_model: ASR instance for video transcription
            llm_router: LLM for rule extraction
        """
        self.chroma_path = Path(chroma_path)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        self.whisper_model = whisper_model
        self.llm_router = llm_router
        self.db = get_mongodb()
        
        # Initialize ChromaDB
        logger.info("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create/get collection
        self.collection = self.client.get_or_create_collection(
            name="rh_knowledge",
            metadata={"description": "ATS and resume knowledge from RH videos"}
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        
        logger.info("✅ Knowledge Base initialized")
    
    def process_video(
        self,
        video_path: str,
        ats_type: Optional[ATSType] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Process a video: transcribe, chunk, extract rules, embed
        
        Args:
            video_path: Path to video file
            ats_type: Optional ATS type this video is about
            metadata: Additional metadata
        
        Returns:
            {
                "success": bool,
                "chunks_created": int,
                "rules_extracted": int
            }
        """
        logger.info(f"Processing video: {video_path}")
        
        if not self.whisper_model:
            raise ValueError("Whisper model required for video processing")
        
        try:
            # 1. Transcribe video
            logger.info("Transcribing video...")
            transcript = self._transcribe_video(video_path)
            
            # 2. Semantic chunking
            logger.info("Chunking transcript...")
            chunks = self._chunk_text(transcript, max_tokens=500)
            
            # 3. Extract rules (LLM)
            logger.info("Extracting rules...")
            rules = self._extract_rules(chunks)
            
            # 4. Create embeddings and store
            logger.info(f"Creating embeddings for {len(chunks)} chunks...")
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                # Create embedding
                embedding = self.embedder.encode(chunk).tolist()
                
                # Prepare metadata
                chunk_metadata = {
                    "source": Path(video_path).name,
                    "chunk_index": i,
                    "ats_type": ats_type.value if ats_type else "general"
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                # Store in ChromaDB
                chunk_id = f"{Path(video_path).stem}_chunk_{i}"
                
                self.collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[chunk_metadata],
                    ids=[chunk_id]
                )
                
                chunk_ids.append(chunk_id)
                
                # Store in MongoDB for tracking
                self.db.kb_chunks.insert_one({
                    "source": Path(video_path).name,
                    "chunk_text": chunk,
                    "chunk_index": i,
                    "ats_type": ats_type.value if ats_type else None,
                    "extracted_rules": [],
                    "vector_id": chunk_id
                })
            
            # 5. Store extracted rules
            for rule in rules:
                # Find best matching chunk
                rule_embedding = self.embedder.encode(rule["text"]).tolist()
                results = self.collection.query(
                    query_embeddings=[rule_embedding],
                    n_results=1
                )
                
                if results["ids"]:
                    chunk_id = results["ids"][0][0]
                    
                    # Update MongoDB with rule
                    self.db.kb_chunks.update_one(
                        {"vector_id": chunk_id},
                        {"$push": {"extracted_rules": rule["text"]}}
                    )
            
            logger.info(f"✅ Video processed: {len(chunks)} chunks, {len(rules)} rules")
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "rules_extracted": len(rules),
                "chunk_ids": chunk_ids
            }
        
        except Exception as e:
            logger.error(f"Video processing failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _transcribe_video(self, video_path: str) -> str:
        """Transcribe video using Whisper"""
        # Extract audio from video (simplified - assumes audio file or video with audio track)
        # For real implementation, might need ffmpeg
        
        # Use existing Whisper model
        result = self.whisper_model.transcribe(video_path)
        
        if "text" in result:
            return result["text"]
        else:
            raise ValueError("Transcription failed")
    
    def _chunk_text(
        self,
        text: str,
        max_tokens: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Semantic chunking of text
        
        Strategy:
        - Split by sentences
        - Group into chunks of ~max_tokens
        - Maintain overlap for context
        """
        # Simple sentence splitting
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            # Rough token estimate (words * 1.3)
            sentence_tokens = len(sentence.split()) * 1.3
            
            if current_length + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s.split()) * 1.3 for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _extract_rules(self, chunks: List[str]) -> List[Dict]:
        """
        Extract ATS rules from chunks using LLM
        
        Returns:
            [{"text": "rule description", "category": "formatting|keywords|..."}]
        """
        if not self.llm_router:
            logger.warning("No LLM available for rule extraction")
            return []
        
        rules = []
        
        # Process in batches to avoid overwhelming LLM
        for chunk in chunks[:5]:  # Limit for MVP
            prompt = f"""
Extraia regras específicas de ATS (Applicant Tracking System) do seguinte texto:

{chunk}

Liste cada regra em uma linha, no formato:
- [CATEGORIA] Descrição da regra

Categorias: KEYWORDS, FORMATTING, STRUCTURE, LENGTH, METRICS

Regras:
"""
            
            try:
                response = self.llm_router.llm.generate(
                    prompt,
                    temperature=0.1,
                    max_tokens=300
                )
                
                # Parse rules
                import re
                lines = response.split('\n')
                for line in lines:
                    match = re.match(r'-\s*\[(\w+)\]\s*(.*)', line)
                    if match:
                        category = match.group(1).lower()
                        rule_text = match.group(2).strip()
                        
                        if rule_text:
                            rules.append({
                                "text": rule_text,
                                "category": category
                            })
            
            except Exception as e:
                logger.error(f"Rule extraction failed for chunk: {e}")
        
        return rules
    
    def query(
        self,
        question: str,
        ats_type: Optional[ATSType] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Query knowledge base (RAG)
        
        Args:
            question: Question or topic
            ats_type: Filter by ATS type
            top_k: Number of results
        
        Returns:
            [
                {
                    "text": "chunk text",
                    "metadata": {...},
                    "distance": float
                }
            ]
        """
        logger.info(f"Querying KB: {question}")
        
        # Create query embedding
        query_embedding = self.embedder.encode(question).tolist()
        
        # Build where filter
        where_filter = None
        if ats_type:
            where_filter = {"ats_type": ats_type.value}
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results
        formatted = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                formatted.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })
        
        logger.info(f"Found {len(formatted)} results")
        return formatted
    
    def get_ats_checklist(self, ats_type: ATSType) -> Dict[str, str]:
        """
        Get ATS-specific checklist
        
        Combines:
        - Default checklist
        - Learned rules from videos
        """
        # Default checklists
        DEFAULT_CHECKLISTS = {
            ATSType.GUPY: {
                "no_images": "Currículo não contém imagens?",
                "no_tables": "Currículo não contém tabelas?",
                "keywords_present": "Palavras-chave da vaga presentes 2-3x?",
                "bullets_short": "Bullets com menos de 80 caracteres?",
                "pages_max_2": "Máximo 2 páginas?",
                "metrics_included": "Inclui métricas quantificáveis?"
            },
            ATSType.GREENHOUSE: {
                "keywords_exact": "Keywords exatas da vaga?",
                "chronological": "Experiências em ordem cronológica reversa?",
                "simple_formatting": "Formatação simples (sem colunas)?",
                "contact_info": "Informações de contato completas?"
            },
            ATSType.LEVER: {
                "keywords_present": "Keywords presentes 2-3x?",
                "action_verbs": "Bullets começam com verbos de ação?",
                "no_headers": "Sem headers/rodapés complexos?"
            },
            ATSType.WORKDAY: {
                "section_headers": "Seções claramente delimitadas?",
                "keywords_present": "Keywords presentes?",
                "education_included": "Educação incluída?",
                "skills_section": "Seção de habilidades presente?"
            },
            ATSType.TALEO: {
                "no_special_chars": "Sem caracteres especiais?",
                "keywords_present": "Keywords presentes 2-4x?",
                "simple_bullets": "Bullets simples (sem símbolos especiais)?"
            }
        }
        
        checklist = DEFAULT_CHECKLISTS.get(ats_type, {})
        
        # TODO: Augment with learned rules from videos
        # Query for rules specific to this ATS
        
        return checklist
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        total_chunks = self.collection.count()
        
        # Count by ATS type
        ats_counts = {}
        for ats_type in ATSType:
            count = self.collection.count(
                where={"ats_type": ats_type.value}
            )
            if count > 0:
                ats_counts[ats_type.value] = count
        
        return {
            "total_chunks": total_chunks,
            "by_ats": ats_counts,
            "embedding_model": self.embedder.get_sentence_embedding_dimension()
        }
