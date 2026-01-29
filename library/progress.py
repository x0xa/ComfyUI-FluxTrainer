import time
import threading
import logging

logger = logging.getLogger(__name__)

try:
    from server import PromptServer
    HAS_PROMPT_SERVER = True
except ImportError:
    HAS_PROMPT_SERVER = False

_progress_interval = 5.0

def send_progress(message: str):
    """Send progress update via WebSocket if available"""
    if HAS_PROMPT_SERVER and hasattr(PromptServer, 'instance') and PromptServer.instance:
        try:
            PromptServer.instance.send_sync("progress", {"message": message})
            logger.info(f"[Flux Trainer] {message}")
        except Exception as e:
            logger.warning(f"[Flux Trainer] Failed to send progress: {e}")
    else:
        logger.info(f"[Flux Trainer] {message}")

class ProgressNotifier:
    """Sends progress updates via WebSocket every N seconds during long operations"""

    def __init__(self, message: str, interval: float = _progress_interval):
        self.message = message
        self.interval = interval
        self.stop_event = threading.Event()
        self.thread = None

    def __enter__(self):
        send_progress(self.message)
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        return False

    def _loop(self):
        while not self.stop_event.wait(self.interval):
            send_progress(self.message)
