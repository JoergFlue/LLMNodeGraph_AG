
import re
from typing import Optional
from .node import Node
from .graph import Graph

class ContextAssembler:
    def __init__(self, graph: Graph):
        self.graph = graph

    def assemble(self, node: Node) -> str:
        """
        Assembles the context for a node:
        1. Inherited history from primary parent (trace_depth).
        2. Resolve @ID references from inputs in the current prompt.
        3. Merge and enforce token limits.
        """
        # 1. Gather History (Sequential Context from Primary Parent)
        history_text = self._gather_history(node, node.config.trace_depth)

        # 2. Identify and Gather Implicit Context (Unreferenced Inputs)
        # Find explicit refs first to avoid duplication
        refs = re.findall(r'@(\w+)', node.prompt)
        referenced_ids = set(refs)
        
        input_nodes = self.graph.get_input_nodes(node.id)
        implicit_parts = []
        for inp in input_nodes:
            # If not explicitly referenced, add it to implicit context
            # (and if not the primary parent already covered by history? 
            #  Actually _gather_history covers primary parent if depth > 0.
            #  If depth=0, primary parent is not in history.
            #  We should avoid duplicating if history already has it. 
            #  But history is a block string, hard to check.
            #  Simple heuristic: If trace_depth > 0 and inp is primary, skip.)
            
            is_primary = (node.input_links and inp.id == self.graph.links[node.input_links[0]].source_id)
            if node.config.trace_depth > 0 and is_primary:
                continue # Already in history
                
            if inp.id not in referenced_ids and inp.cached_output:
                implicit_parts.append(inp.cached_output)
                
        implicit_context = "\n\n".join(implicit_parts)

        # 3. Process current prompt for references (Explicit Context)
        current_prompt = node.prompt
        final_prompt = self._inject_references(current_prompt, node)
        
        # 4. Combine
        # Order: History -> Implicit Inputs -> Prompt
        full_text = ""
        if history_text:
            full_text += history_text + "\n\n"
        if implicit_context:
            full_text += implicit_context + "\n\n"
        full_text += final_prompt
        
        # 5. Guard (Token Limiter) 
        # Note: _enforce_limit Logic changes slightly as we have pre-assembled full_text 
        # minus the logic of prioritizing prompt.
        # Let's adjust _enforce_limit to take (history+implicit) vs prompt.
        context_block = history_text + ("\n\n" + implicit_context if implicit_context else "")
        return self._enforce_limit(context_block, final_prompt, node.config.max_tokens)

    def _gather_history(self, node: Node, depth: int) -> str:
        """
        Recursively fetches cached output from the primary parent (first input)
        up to the specified depth.
        """
        if depth <= 0 or not node.input_links:
            return ""
        
        # Assume first input is the Primary Parent for linear history inheritance
        link_id = node.input_links[0]
        link = self.graph.links.get(link_id)
        if not link:
            return ""
            
        parent = self.graph.nodes.get(link.source_id)
        if not parent:
            return ""
            
        # Recursive gather
        parent_history = self._gather_history(parent, depth - 1)
        
        parts = []
        if parent_history:
            parts.append(parent_history)
        if parent.cached_output:
            parts.append(parent.cached_output)
            
        return "\n".join(parts)

    def _inject_references(self, prompt: str, node: Node) -> str:
        """
        Replace @ID or @Label with the cached output of the connected node.
        Only resolves nodes that are physically connected as inputs.
        """
        input_nodes = self.graph.get_input_nodes(node.id)
        # Create map for ID matching
        ref_map = {n.id: n.cached_output for n in input_nodes}
        
        def replace(match):
            key = match.group(1)
            # Only replace if key is in connected inputs
            if key in ref_map:
                return ref_map[key]
            return match.group(0) # Keep literal if not found/connected
            
        return re.sub(r'@(\w+)', replace, prompt)

    def _enforce_limit(self, history: str, prompt: str, limit: int) -> str:
        """
        Simple char/4 heuristic. 
        Prioritizes Prompt + References. Truncates History from the top (oldest).
        """
        # Estimate tokens (1 token ~= 4 chars)
        prompt_tokens = len(prompt) / 4
        history_tokens = len(history) / 4
        total = prompt_tokens + history_tokens
        
        if total <= limit:
            return f"{history}\n{prompt}" if history else prompt
            
        # We need to cut history
        budget_for_history = limit - prompt_tokens
        
        if budget_for_history <= 0:
            # Prompt is too large on its own. 
            # We keep the prompt as the spec says "Keep the Current Prompt".
            return prompt
            
        # Calculate chars to keep
        chars_to_keep = int(budget_for_history * 4)
        if len(history) > chars_to_keep:
            truncated = history[-chars_to_keep:]
            return f"[...Truncated by {int(total - limit)} tokens...]\n{truncated}\n{prompt}"
            
        return f"{history}\n{prompt}"
