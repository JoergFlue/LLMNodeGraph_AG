"""
Command Manager - Manages the Undo/Redo stacks.
"""

from typing import List, Optional, Callable
from .command import Command

class CommandManager:
    """Manages undo and redo stacks for the application."""
    
    def __init__(self, max_stack_size: int = 50):
        """
        Initialize the CommandManager.
        
        Args:
            max_stack_size (int): Maximum number of undo steps to keep.
        """
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_stack_size = max_stack_size
        self._on_stack_changed: List[Callable[[], None]] = []
        
    def add_listener(self, callback: Callable[[], None]) -> None:
        """
        Add a listener to be notified when the stacks change.
        
        Args:
            callback (Callable): Function to call on change.
        """
        self._on_stack_changed.append(callback)
        
    def _notify_listeners(self) -> None:
        """Notify all listeners that the command stack has changed."""
        for callback in self._on_stack_changed:
            callback()
            
    def execute(self, command: Command) -> None:
        """
        Execute a command and add it to the undo stack.
        
        Args:
            command (Command): The command to execute.
        """
        command.execute()
        self.undo_stack.append(command)
        
        # Limit stack size
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
            
        # Clear redo stack whenever a new command is executed
        self.redo_stack.clear()
        self._notify_listeners()
        
    def undo(self) -> bool:
        """
        Undo the last command.
        
        Returns:
            bool: True if undo was successful, False if stack empty.
        """
        if not self.undo_stack:
            return False
            
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        self._notify_listeners()
        return True
        
    def redo(self) -> bool:
        """
        Redo the last undone command.
        
        Returns:
            bool: True if redo was successful, False if stack empty.
        """
        if not self.redo_stack:
            return False
            
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)
        self._notify_listeners()
        return True
        
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
        
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
        
    def get_undo_description(self) -> Optional[str]:
        """Get description of the next undo action."""
        if self.undo_stack:
            return self.undo_stack[-1].get_description()
        return None
        
    def get_redo_description(self) -> Optional[str]:
        """Get description of the next redo action."""
        if self.redo_stack:
            return self.redo_stack[-1].get_description()
        return None
        
    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._notify_listeners()
        
    def set_max_stack_size(self, size: int) -> None:
        """
        Set the maximum stack size.
        
        Args:
            size (int): New maximum size.
        """
        self.max_stack_size = size
        # Trim current stack if needed
        while len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
        self._notify_listeners()
