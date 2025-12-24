"""
Hotkey Manager para AI Copilot

Gerencia atalhos de teclado globais.
"""

import logging
from typing import Callable, Dict
from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager:
    """
    Gerenciador de hotkeys globais.
    
    Permite registrar atalhos de teclado que funcionam
    mesmo quando o app não tem foco.
    """
    
    def __init__(self):
        """Inicializa gerenciador de hotkeys."""
        self.hotkeys: Dict[str, Callable] = {}
        self.listener = None
        self.current_keys = set()
        
    def register(self, hotkey: str, callback: Callable):
        """
        Registra um hotkey.
        
        Args:
            hotkey: String de hotkey (ex: 'ctrl+shift+p')
            callback: Função a ser chamada quando hotkey ativado
        """
        self.hotkeys[hotkey.lower()] = callback
        logger.info(f"Hotkey registered: {hotkey}")
    
    def _parse_hotkey(self, hotkey: str) -> set:
        """Converte string de hotkey para set de teclas."""
        parts = hotkey.lower().split('+')
        keys = set()
        
        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                keys.add(keyboard.Key.ctrl_l)
                keys.add(keyboard.Key.ctrl_r)
            elif part == 'shift':
                keys.add(keyboard.Key.shift)
                keys.add(keyboard.Key.shift_r)
            elif part == 'alt':
                keys.add(keyboard.Key.alt_l)
                keys.add(keyboard.Key.alt_r)
            else:
                # Letra normal
                keys.add(keyboard.KeyCode.from_char(part))
        
        return keys
    
    def _on_press(self, key):
        """Callback quando tecla é pressionada."""
        try:
            self.current_keys.add(key)
            
            # Verificar se algum hotkey foi ativado
            for hotkey_str, callback in self.hotkeys.items():
                required_keys = self._parse_hotkey(hotkey_str)
                
                # Verificar se todas as teclas necessárias estão pressionadas
                if self._check_hotkey_match(required_keys):
                    logger.debug(f"Hotkey triggered: {hotkey_str}")
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"Hotkey callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Hotkey press error: {e}")
    
    def _check_hotkey_match(self, required_keys: set) -> bool:
        """Verifica se hotkey foi ativado."""
        # Para cada tecla necessária, verificar se está pressionada
        for required_key in required_keys:
            if isinstance(required_key, keyboard.KeyCode):
                # Tecla de caractere
                if required_key not in self.current_keys:
                    return False
            else:
                # Tecla especial (ctrl, shift, etc) - aceitar qualquer variante
                if required_key not in self.current_keys:
                    # Verificar variantes (left/right)
                    found = False
                    for pressed_key in self.current_keys:
                        if self._keys_equivalent(required_key, pressed_key):
                            found = True
                            break
                    if not found:
                        return False
        
        return True
    
    def _keys_equivalent(self, key1, key2) -> bool:
        """Verifica se duas teclas são equivalentes (ex: ctrl_l e ctrl_r)."""
        # Ctrl
        if key1 in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return key2 in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
        # Shift
        if key1 in (keyboard.Key.shift, keyboard.Key.shift_r):
            return key2 in (keyboard.Key.shift, keyboard.Key.shift_r)
        # Alt
        if key1 in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            return key2 in (keyboard.Key.alt_l, keyboard.Key.alt_r)
        
        return key1 == key2
    
    def _on_release(self, key):
        """Callback quando tecla é soltada."""
        try:
            self.current_keys.discard(key)
        except Exception as e:
            logger.error(f"Hotkey release error: {e}")
    
    def start(self):
        """Inicia listener de hotkeys."""
        if self.listener is not None:
            return
        
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        logger.info("Hotkey manager started")
    
    def stop(self):
        """Para listener de hotkeys."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Hotkey manager stopped")
    
    def get_registered_hotkeys(self) -> list:
        """Retorna lista de hotkeys registrados."""
        return list(self.hotkeys.keys())
