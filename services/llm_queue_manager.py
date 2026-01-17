
from collections import deque, defaultdict
from PySide6.QtCore import QObject, Signal
from .worker import LLMWorker
import logging

class LLMQueueManager(QObject):
    # Signals
    task_started = Signal(str) # node_id
    task_finished = Signal(str, str) # node_id, result
    task_failed = Signal(str, str) # node_id, error_msg
    task_queued = Signal(str) # node_id
    queue_updated = Signal() # General update signal if needed

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("LLM.QueueManager")
        self.queues = defaultdict(deque) # provider -> deque of (node_id, prompt, config)
        self.active_workers = {} # provider -> LLMWorker (only one active per provider)
        self.worker_map = {} # node_id -> LLMWorker (to find worker by node_id quickly)

    def submit_task(self, node_id, prompt, config):
        """
        Submit a task. It will start immediately if the provider is free, 
        otherwise it will be queued.
        """
        provider = config.get("provider", "Default")
        # Normalize provider name for queueing logic
        # You might want to resolve "Default" to actual provider here or keep it simple.
        # For strict queuing, we should probably resolve "Default" before calling submit_task,
        # or inside submit_task if we have access to settings. 
        # But 'config' usually comes from the Node and might say "Default".
        # If it says "Default", we treat everything "Default" as one queue? 
        # Or do we resolve it? 
        # The worker resolves it. Let's assume for now that if multiple nodes are "Default", 
        # they share the "Default" queue. This is acceptable behavior.
        
        if self.is_node_running_or_queued(node_id):
            self.logger.warning(f"Node {node_id} is already running or queued.")
            return

        self.logger.info(f"Submitting task for Node {node_id} (Provider: {provider})")

        # Check if provider is busy
        if provider not in self.active_workers:
            self.start_worker(node_id, prompt, config, provider)
        else:
            self.logger.info(f"Provider {provider} busy. Queuing Node {node_id}")
            self.queues[provider].append((node_id, prompt, config))
            self.task_queued.emit(node_id)

    def start_worker(self, node_id, prompt, config, provider):
        self.logger.info(f"Starting worker for Node {node_id} on {provider}")
        worker = LLMWorker(node_id, prompt, config)
        worker.finished.connect(self.on_worker_finished)
        worker.error.connect(self.on_worker_error)
        
        self.active_workers[provider] = worker
        self.worker_map[node_id] = worker
        
        worker.start()
        self.task_started.emit(node_id)

    def cancel_task(self, node_id):
        self.logger.info(f"Cancelling task for Node {node_id}")
        
        # 1. Check if it's the active worker
        active_worker_to_cancel = None
        provider_to_free = None
        
        for provider, worker in self.active_workers.items():
            if worker.node_id == node_id:
                active_worker_to_cancel = worker
                provider_to_free = provider
                break
        
        if active_worker_to_cancel:
            # Active
            active_worker_to_cancel.cancel()
            # We don't wait for thread to finish, we treat it as done for the queue purpose.
            # But the thread might still be running in background.
            # We should remove it from our tracking.
            del self.active_workers[provider_to_free]
            if node_id in self.worker_map:
                del self.worker_map[node_id]
            
            # Since we cancelled, we can try to start next in queue for this provider
            self.process_next_in_queue(provider_to_free)
            return

        # 2. Check if it's in a queue
        for provider, queue in self.queues.items():
            # queue is a deque of tuples
            # We need to find and remove
             # This is O(N) but N is small (queue size)
            
            found_idx = -1
            for i, item in enumerate(queue):
                if item[0] == node_id:
                    found_idx = i
                    break
            
            if found_idx != -1:
                del queue[found_idx]
                self.logger.info(f"Removed Node {node_id} from {provider} queue")
                # No signal needed specifically for queue removal other than maybe UI update if we had a full queue UI
                # But we should probably reset the Node UI to Idle? 
                # The caller (MainWindow) will handle UI reset when they call cancel_task usually?
                # Actually, cancel_task is void. The UI needs to know it's cancelled.
                # Let's emit specific signal or just let UI handle it?
                # The plan said: "Immediately update the UI to "Idle"". 
                # If the user clicked Cancel, UI does it locally.
                # But strict MVC suggested Manager emits signals.
                # For simplicity, returning "True" or relying on caller is fine, but...
                # Let's simple return.
                return

    def on_worker_finished(self, node_id, result):
        # Identify provider
        worker = self.worker_map.get(node_id)
        if not worker: 
            return # Should not happen unless cancelled race condition

        # Check if cancelled (worker.is_cancelled handles `finished` emit suppression usually, but let's be safe)
        if worker.is_cancelled:
            return

        self.task_finished.emit(node_id, result)
        self.cleanup_worker(node_id)

    def on_worker_error(self, node_id, error_msg):
        worker = self.worker_map.get(node_id)
        # Check if cancelled
        if worker and worker.is_cancelled:
            return

        self.task_failed.emit(node_id, error_msg)
        self.cleanup_worker(node_id)

    def cleanup_worker(self, node_id):
        worker = self.worker_map.pop(node_id, None)
        if not worker: return
        
        # Find provider
        provider_found = None
        for provider, w in self.active_workers.items():
            if w == worker:
                provider_found = provider
                break
        
        if provider_found:
            del self.active_workers[provider_found]
            
            # CRITICAL FIX: Ensure thread is fully finished before checking next
            if worker.isRunning():
                worker.quit()
                worker.wait()
            else:
                worker.wait()
            worker.deleteLater()
            
            self.process_next_in_queue(provider_found)

    def process_next_in_queue(self, provider):
        if self.queues[provider]:
            next_task = self.queues[provider].popleft()
            node_id, prompt, config = next_task
            self.start_worker(node_id, prompt, config, provider)

    def is_node_running_or_queued(self, node_id):
        if node_id in self.worker_map: return True
        for queue in self.queues.values():
            for item in queue:
                if item[0] == node_id: return True
        return False

    def shutdown(self):
        """Cancel all workers and wait for them to finish."""
        self.logger.info("Shutting down Queue Manager...")
        self.queues.clear() # Clear pending
        
        workers = list(self.active_workers.values())
        for worker in workers:
            self.logger.info(f"Stopping worker {worker.node_id}")
            worker.cancel()
            worker.quit()
            worker.wait() # Wait for thread to exit
        self.logger.info("Shutdown complete.")
