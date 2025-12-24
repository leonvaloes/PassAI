"""
Session Export - Salvar e exportar sessões de conversação

Permite salvar transcrições e sugestões para revisão posterior.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionExporter:
    """
    Exportador de sessões de conversação.
    
    Salva transcrições, sugestões e metadados.
    """
    
    def __init__(self, output_dir: str = "sessions"):
        """
        Inicializa exportador.
        
        Args:
            output_dir: Diretório para salvar sessões
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.current_session = {
            'session_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'start_time': datetime.now().isoformat(),
            'transcriptions': [],
            'suggestions': [],
            'metadata': {}
        }
        
        logger.info(f"Session exporter initialized: {self.output_dir}")
    
    def add_transcription(self, text: str, intent: str, metadata: Optional[Dict] = None):
        """
        Adiciona transcrição à sessão.
        
        Args:
            text: Texto transcrito
            intent: Intenção detectada
            metadata: Metadados adicionais
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'text': text,
            'intent': intent,
            'metadata': metadata or {}
        }
        
        self.current_session['transcriptions'].append(entry)
    
    def add_suggestion(self, suggestion: str, context: Optional[str] = None):
        """
        Adiciona sugestão da IA à sessão.
        
        Args:
            suggestion: Sugestão gerada
            context: Contexto que gerou a sugestão
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'suggestion': suggestion,
            'context': context or ''
        }
        
        self.current_session['suggestions'].append(entry)
    
    def set_metadata(self, key: str, value):
        """Define metadado da sessão."""
        self.current_session['metadata'][key] = value
    
    def export_json(self, filename: Optional[str] = None) -> Path:
        """
        Exporta sessão para JSON.
        
        Args:
            filename: Nome do arquivo (None = auto)
            
        Returns:
            Path do arquivo salvo
        """
        if filename is None:
            filename = f"session_{self.current_session['session_id']}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Session exported to JSON: {filepath}")
        return filepath
    
    def export_markdown(self, filename: Optional[str] = None) -> Path:
        """
        Exporta sessão para Markdown.
        
        Args:
            filename: Nome do arquivo (None = auto)
            
        Returns:
            Path do arquivo salvo
        """
        if filename is None:
            filename = f"session_{self.current_session['session_id']}.md"
        
        filepath = self.output_dir / filename
        
        # Gerar markdown
        lines = []
        lines.append(f"# AI Copilot Session")
        lines.append(f"\n**Session ID:** {self.current_session['session_id']}")
        lines.append(f"**Start Time:** {self.current_session['start_time']}")
        lines.append(f"\n---\n")
        
        # Intercalar transcrições e sugestões
        all_entries = []
        
        for t in self.current_session['transcriptions']:
            all_entries.append(('transcription', t))
        
        for s in self.current_session['suggestions']:
            all_entries.append(('suggestion', s))
        
        # Ordenar por timestamp
        all_entries.sort(key=lambda x: x[1]['timestamp'])
        
        # Escrever entradas
        for entry_type, entry in all_entries:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M:%S")
            
            if entry_type == 'transcription':
                lines.append(f"## [{timestamp}] 🎤 User ({entry['intent']})")
                lines.append(f"\n{entry['text']}\n")
            else:
                lines.append(f"## [{timestamp}] 🤖 AI Suggestion")
                lines.append(f"\n{entry['suggestion']}\n")
        
        # Metadata
        if self.current_session['metadata']:
            lines.append("\n---\n")
            lines.append("## Session Metadata")
            for key, value in self.current_session['metadata'].items():
                lines.append(f"- **{key}:** {value}")
        
        # Salvar
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"Session exported to Markdown: {filepath}")
        return filepath
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas da sessão."""
        return {
            'total_transcriptions': len(self.current_session['transcriptions']),
            'total_suggestions': len(self.current_session['suggestions']),
            'session_id': self.current_session['session_id'],
            'start_time': self.current_session['start_time']
        }
