import logging
from typing import List, Dict, Tuple, Any

from app.core.config import settings
from app.schemas.ai_request_context import AIRequestContext

logger = logging.getLogger("app.services.prompt_optimizer")

class PromptOptimizer:
    def __init__(self):
        self.max_turns = getattr(settings, "PROMPT_MAX_HISTORY_TURNS", 3)
        self.preserved_keywords = [
            "Current Interview Stage",
            "Current Evaluation Summary",
            "Current Interview Instructions"
        ]

    def _is_persistent(self, message: Dict[str, Any]) -> bool:
        if message.get("persistent", False):
            return True
        content = message.get("content", "")
        if not isinstance(content, str):
            return False
        for keyword in self.preserved_keywords:
            if keyword in content:
                return True
        return False

    def optimize_system_prompt(self, prompt: str) -> str:
        """
        Removes duplicate instructions and unnecessary examples.
        Keeps interview rules concise, preserves behaviour and evaluation rules.
        """
        if not prompt:
            return prompt
        
        # Simple string optimization: remove duplicate consecutive lines
        lines = prompt.split('\n')
        optimized_lines = []
        prev_line = None
        for line in lines:
            stripped = line.strip()
            # keep empty lines but don't duplicate them
            if stripped == prev_line and stripped != "":
                continue
            optimized_lines.append(line)
            prev_line = stripped
            
        return '\n'.join(optimized_lines)

    def remove_redundant_context(self, text: str) -> str:
        if not text:
            return text
        # Future-proofing for removing bloated context
        return text.strip()

    def optimize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not messages:
            return []
            
        optimized = []
        prev_message = None
        
        for msg in messages:
            # 1. Remove empty messages
            content = msg.get("content", "")
            if isinstance(content, str):
                content = content.strip()
                if not content:
                    continue
                msg["content"] = content
            
            # 2. Remove exact duplicate consecutive assistant/system messages
            if prev_message:
                if msg.get("role") == prev_message.get("role") and msg.get("role") in ["assistant", "system"]:
                    if msg.get("content") == prev_message.get("content"):
                        continue
                        
            # Apply system prompt optimization if it's a system message
            if msg.get("role") == "system" and isinstance(msg.get("content"), str):
                msg["content"] = self.optimize_system_prompt(msg["content"])
                
            optimized.append(msg)
            prev_message = msg
            
        return optimized

    def compress_history(self, messages: List[Dict[str, Any]], context: AIRequestContext = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Compresses history by keeping only the last N interview turns.
        A turn is roughly [AI Question, Candidate Answer, AI Evaluation].
        Older messages are removed but persistent ones are kept.
        """
        if not messages:
            return [], []

        retained = []
        removed = []
        
        # Apply budget manager flags
        effective_max_turns = self.max_turns
        if context:
            if context.grace_mode:
                effective_max_turns = 1 # Keep only latest turn
            elif context.aggressive_compression:
                effective_max_turns = max(1, self.max_turns - 1)
        
        # Identify persistent messages and system prompts (always kept)
        history_candidates = []
        for i, msg in enumerate(messages):
            if msg.get("role") == "system" or self._is_persistent(msg):
                msg["_always_keep"] = True
                retained.append(msg)
            else:
                msg["_original_index"] = i
                history_candidates.append(msg)
                
        # A turn consists of [AI Question, Candidate Answer, AI Evaluation]
        # We will iterate backwards, counting the number of Candidate Answers (role='user').
        
        retained_history = []
        removed = []
        turns_found = 0
        
        for i in range(len(history_candidates) - 1, -1, -1):
            msg = history_candidates[i]
            if turns_found < effective_max_turns:
                retained_history.insert(0, msg)
                if msg.get("role") == "user":
                    turns_found += 1
            else:
                # We've reached max_turns. The oldest kept turn starts with a user answer,
                # but we MUST keep the assistant's question that triggered it!
                if msg.get("role") == "assistant" and len(retained_history) > 0 and retained_history[0].get("role") == "user":
                    retained_history.insert(0, msg)
                else:
                    removed.insert(0, msg)
            
        # Reconstruct the original order
        final_retained = []
        for msg in messages:
            if msg.get("_always_keep"):
                msg.pop("_always_keep", None)
                final_retained.append(msg)
            elif msg in retained_history:
                msg.pop("_original_index", None)
                final_retained.append(msg)
                
        # Cleanup removed
        for msg in removed:
            msg.pop("_original_index", None)
            
        return final_retained, removed

    def run_optimization(self, messages: List[Dict[str, Any]], context: AIRequestContext = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], dict]:
        """
        Runs full optimization pipeline and returns (retained, removed, stats).
        """
        original_count = len(messages)
        original_chars = sum(len(str(m)) for m in messages)
        
        optimized = self.optimize_messages(messages)
        retained, removed = self.compress_history(optimized, context)
        
        optimized_count = len(retained)
        optimized_chars = sum(len(str(m)) for m in retained)
        removed_count = len(removed)
        
        compression_pct = round((1 - (optimized_chars / original_chars)) * 100, 2) if original_chars > 0 else 0
        
        stats = {
            "original_count": original_count,
            "optimized_count": optimized_count,
            "original_chars": original_chars,
            "optimized_chars": optimized_chars,
            "removed_count": removed_count,
            "compression_pct": compression_pct
        }
        
        return retained, removed, stats
