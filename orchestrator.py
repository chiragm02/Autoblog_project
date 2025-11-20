import asyncio, logging, uuid, json, yaml
from services.llm import LLMService
from agents.research_agent import ResearchAgent
from agents.draft_agent import DraftAgent
from agents.review_agent import ReviewAgent
from agents.formatter_agent import FormatterAgent
from agents.publish_agent import PublishAgent
from memory.session_service import InMemorySessionService
from memory.memory_bank import MemoryBank
from tools.context_compactor import ContextCompactor

logger = logging.getLogger("orchestrator")
logging.basicConfig(level=logging.INFO)

class Orchestrator:
    def __init__(self, config):
        self.llm = LLMService(config)
        self.session_service = InMemorySessionService()
        self.memory = MemoryBank()
        self.research_agent = ResearchAgent(config)
        self.draft_agent = DraftAgent(self.llm)
        self.review_agent = ReviewAgent(self.llm)
        self.formatter_agent = FormatterAgent()
        self.publish_agent = PublishAgent(config)
        self.compactor = ContextCompactor()

    async def create_post(self, topic, prefs=None):
        trace_id = str(uuid.uuid4())
        self.session_service.create_session(trace_id, topic, prefs or {})

        research = await self.research_agent.research(topic, trace_id)
        compact = self.compactor.compact(research)
        draft = await self.draft_agent.create_draft(topic, compact, prefs or {}, trace_id)
        final, score = await self.review_agent.review_loop(draft, research, trace_id)
        formatted = self.formatter_agent.format(final, topic, prefs or {})

        publish = None
        if prefs and prefs.get("publish"):
            publish = self.publish_agent.publish(formatted, topic, trace_id)

        result = {
            "trace_id": trace_id,
            "topic": topic,
            "draft": final,
            "formatted": formatted,
            "publish_result": publish,
            "review_score": score
        }
        self.memory.save_post_summary(trace_id, topic, compact, score)
        return result
