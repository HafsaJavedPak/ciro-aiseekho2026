# backend/agents/base.py
import time
from abc import ABC, abstractmethod
from typing import Any, Optional
from backend.models.trace import AgentTrace
from backend.services.firestore_service import firestore_service

class BaseAgent(ABC):
    """
    Abstract base class for all CIRO Agents.
    Handles execution timing and automatic trace logging to Firestore.
    """
    
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Name of the agent, e.g., 'classification_agent'."""
        pass
        
    @property
    def model_name(self) -> str:
        """The model used, e.g., 'rule-based' or 'gemini-1.5-flash'."""
        return "rule-based"
        
    async def run(self, incident_id: str, input_data: Any, **kwargs) -> Any:
        """
        Wrapper that runs the agent logic and automatically logs the trace.
        """
        start_time = time.time()
        
        try:
            # The core logic must return 4 things: output, reasoning, decision, next_agent
            output, reasoning, decision, next_agent = await self.execute(incident_id, input_data, **kwargs)
            is_degraded = False
        except Exception as e:
            print(f"[{self.agent_name}] Error during execution: {e}")
            raise e
            
        latency_ms = int((time.time() - start_time) * 1000)
        
        output_dict = output.model_dump() if hasattr(output, "model_dump") else (output if isinstance(output, dict) else {"result": str(output)})
        
        # Build and save the trace
        trace = AgentTrace(
            incident_id=incident_id,
            agent=self.agent_name,
            input_summary=self._summarize_input(input_data),
            reasoning=reasoning,
            output=output_dict,
            decision=decision,
            next_agent=next_agent,
            latency_ms=latency_ms,
            model=self.model_name,
            is_degraded=is_degraded
        )
        
        await firestore_service.save_trace(trace)
        
        return output

    @abstractmethod
    async def execute(self, incident_id: str, input_data: Any, **kwargs) -> tuple[Any, str, str, Optional[str]]:
        """
        Must be implemented by subclasses.
        Returns:
            - output: The structured output model (e.g. CrisisClassification)
            - reasoning: A human-readable string explaining the agent's thought process
            - decision: A short string like 'CLASSIFIED' or 'FLAGGED'
            - next_agent: The name of the next agent to trigger, or None if done
        """
        pass
        
    def _summarize_input(self, input_data: Any) -> str:
        """Provides a human-readable summary of the input for the trace UI."""
        return f"Received {type(input_data).__name__} payload."
