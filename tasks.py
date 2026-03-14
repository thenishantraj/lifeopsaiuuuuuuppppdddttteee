from crewai import Task
from typing import Dict, Any, List
from datetime import datetime
import json


class LifeOpsTasks:
    def __init__(self, user_context: Dict[str, Any]):
        self.user_context = user_context

    def create_health_analysis_task(self, agent) -> Task:
        return Task(
            description=f"""Analyze health situation comprehensively.
            Stress: {self.user_context.get('stress_level', 5)}/10
            Sleep: {self.user_context.get('sleep_hours', 7)}h
            Exercise: {self.user_context.get('exercise_frequency', 'Rarely')}
            Problem: {self.user_context.get('problem', 'General optimization')}
            Provide risk assessment, immediate actions, weekly schedule, and action items.""",
            agent=agent,
            expected_output="Comprehensive health analysis with actionable recommendations."
        )

    def create_finance_analysis_task(self, agent) -> Task:
        return Task(
            description=f"""Analyze financial situation with bill management.
            Budget: ${self.user_context.get('monthly_budget', 2000)}
            Expenses: ${self.user_context.get('current_expenses', 1500)}
            Goals: {self.user_context.get('financial_goals', 'Save money')}
            Provide budget optimization and specific savings strategies.""",
            agent=agent,
            expected_output="Detailed financial plan with specific numbers and action items."
        )

    def create_study_analysis_task(self, agent) -> Task:
        return Task(
            description=f"""Create optimized study plan.
            Exam date: {self.user_context.get('exam_date', 'Not specified')}
            Days left: {self.user_context.get('days_until_exam', 30)}
            Study hours/day: {self.user_context.get('current_study_hours', 3)}
            Provide Pomodoro schedule, focus techniques, and burnout prevention.""",
            agent=agent,
            expected_output="Complete study optimization plan with daily schedule."
        )

    def create_life_coordination_task(self, agent, context_tasks: List[Task]) -> Task:
        return Task(
            description=f"""Create integrated life plan from domain analyses.
            Primary concern: {self.user_context.get('problem', 'Life optimization')}
            Resolve conflicts, create priority matrix, unified weekly schedule.""",
            agent=agent,
            expected_output="Integrated life coordination plan with time-blocked schedule.",
            context=context_tasks
        )
