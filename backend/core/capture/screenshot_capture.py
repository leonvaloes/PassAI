"""
Screenshot Capture Module
Captures screenshots using mss library
"""

import mss
import os
from datetime import datetime
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """Handles screen capture functionality"""
    
    def __init__(self, save_dir="screenshots"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        logger.info(f"📸 Screenshot capture initialized: {save_dir}")
    
    def capture_screen(self, monitor_num=0):
        """
        Capture entire screen or specific monitor
        
        Args:
            monitor_num: Monitor index (0 = all monitors, 1+ = specific monitor)
            
        Returns:
            tuple: (filepath, PIL.Image) or (None, None) on error
        """
        try:
            with mss.mss() as sct:
                # Get monitor (0 = all screens, 1+ = specific monitor)
                if monitor_num >= len(sct.monitors):
                    logger.warning(f"Monitor {monitor_num} not found, using all screens")
                    monitor_num = 0
                
                monitor = sct.monitors[monitor_num]
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(self.save_dir, filename)
                
                # Save
                img.save(filepath, optimize=True)
                
                logger.info(f"✅ Screenshot saved: {filepath} ({img.size[0]}x{img.size[1]})")
                
                return filepath, img
                
        except Exception as e:
            logger.error(f"❌ Screenshot capture failed: {e}")
            return None, None
    
    def capture_region(self, x, y, width, height):
        """
        Capture specific screen region
        
        Args:
            x, y: Top-left coordinates
            width, height: Region dimensions
            
        Returns:
            tuple: (filepath, PIL.Image) or (None, None) on error
        """
        try:
            with mss.mss() as sct:
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                
                screenshot = sct.grab(monitor)
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_region_{timestamp}.png"
                filepath = os.path.join(self.save_dir, filename)
                
                img.save(filepath, optimize=True)
                
                logger.info(f"✅ Region screenshot saved: {filepath}")
                
                return filepath, img
                
        except Exception as e:
            logger.error(f"❌ Region capture failed: {e}")
            return None, None
    
    def get_monitors(self):
        """
        Get list of available monitors
        
        Returns:
            list: Monitor information dictionaries
        """
        try:
            with mss.mss() as sct:
                monitors = []
                for i, monitor in enumerate(sct.monitors):
                    monitors.append({
                        "index": i,
                        "width": monitor.get("width", 0),
                        "height": monitor.get("height", 0),
                        "left": monitor.get("left", 0),
                        "top": monitor.get("top", 0)
                    })
                return monitors
        except Exception as e:
            logger.error(f"❌ Failed to get monitors: {e}")
            return []
    
    def list_screenshots(self, limit=20):
        """
        List recent screenshots
        
        Args:
            limit: Maximum number of screenshots to return
            
        Returns:
            list: Screenshot file information
        """
        try:
            files = []
            for filename in os.listdir(self.save_dir):
                if filename.startswith("screenshot_") and filename.endswith(".png"):
                    filepath = os.path.join(self.save_dir, filename)
                    stat = os.stat(filepath)
                    files.append({
                        "filename": filename,
                        "filepath": filepath,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            # Sort by creation time (newest first)
            files.sort(key=lambda x: x["created"], reverse=True)
            
            return files[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to list screenshots: {e}")
            return []
