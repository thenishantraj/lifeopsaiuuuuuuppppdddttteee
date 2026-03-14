import os
from typing import List
from crewai import Agent
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = "not-required"
os.environ["OPENAI_API_BASE"] = ""
os.environ["OPENAI_MODEL_NAME"] = ""


@tool("schedule_action_item")
def schedule_action_item(task: str, category: str, priority: str = "medium"):
    """Schedule an action item in the system."""
    return f"Scheduled: {task} ({category}, priority: {priority})"


@tool("set_reminder")
def set_reminder(message: str, hours_from_now: int = 24):
    """Set a reminder for future follow-up."""
    return f"Reminder set for {hours_from_now}h: {message}"


@tool("validate_cross_domain")
def validate_cross_domain(domain: str, recommendation: str, context: dict = {}):
    """Validate recommendations across life domains."""
    return f"Validated [{domain}]: {recommendation[:100]}"


class LifeOpsAgents:
    def __init__(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,
                google_api_key=api_key
            )
        except Exception:
            self.llm = None

    def create_health_agent(self) -> Agent:
        return Agent(
            role="Health and Wellness Expert",
            goal="Optimize health and wellness through personalized, evidence-based recommendations",
            backstory="Dr. Maya Patel has 15 years in integrative medicine, specializing in stress management, preventive healthcare, and mind-body wellness.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            tools=[schedule_action_item, set_reminder]
        )

    def create_finance_agent(self) -> Agent:
        return Agent(
            role="Personal Finance Advisor",
            goal="Help users achieve financial freedom through smart budgeting, saving, and investing",
            backstory="Alex Chen is a CFA with 12 years expertise in personal finance, behavioral economics, and wealth building for everyday people.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            tools=[schedule_action_item]
        )

    def create_study_agent(self) -> Agent:
        return Agent(
            role="Learning Specialist",
            goal="Maximize learning efficiency and academic performance using cognitive science",
            backstory="Prof. James Wilson, cognitive scientist at MIT, specializes in learning optimization, spaced repetition, and peak performance.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm,
            tools=[schedule_action_item, set_reminder]
        )

    def create_life_coordinator(self) -> Agent:
        return Agent(
            role="Life Operations Coordinator",
            goal="Orchestrate all life domains for optimal balance, productivity, and fulfillment",
            backstory="Sophia Williams, systems thinker and certified life coach, helps high-achievers design lives of purpose, balance, and peak performance.",
            verbose=False,
            allow_delegation=True,
            llm=self.llm,
            tools=[validate_cross_domain, schedule_action_item]
        )

    def get_all_agents(self) -> List[Agent]:
        return [
            self.create_health_agent(),
            self.create_finance_agent(),
            self.create_study_agent(),
            self.create_life_coordinator()
        ]
