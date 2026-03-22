import json
from typing import List, Dict, Any
import google.generativeai as genai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class AIProductivityAgent:
    """AI service for task prioritization and analysis using Google Gemini"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize Gemini API"""
        if not cls._initialized:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            cls._initialized = True
    
    @staticmethod
    def build_prompt(tasks: List[Dict[str, Any]]) -> str:
        """Build the prompt for AI analysis"""
        tasks_text = "\n".join([
            f"{i+1}. {task['title']} (Due: {task.get('due_date', 'No due date')})\n   Description: {task.get('description', 'N/A')}"
            for i, task in enumerate(tasks)
        ])
        
        prompt = f"""You are a productivity assistant optimizing task prioritization using the Eisenhower Matrix.

Given the following tasks, analyze and prioritize them:

{tasks_text}

For each task, classify into ONE of these categories:
1. Urgent & Important (Do First)
2. Important but Not Urgent (Schedule)
3. Urgent but Not Important (Delegate/Minimize)
4. Neither (Eliminate)

Also:
- Identify any tasks that appear to be procrastination patterns
- Suggest a prioritized schedule for today (max 6 tasks)
- Provide productivity insights

Return ONLY valid JSON (no markdown, no extra text):

{{
    "prioritized_tasks": [
        {{"task_id": 1, "title": "...", "category": "urgent_important", "reason": "..."}}
    ],
    "today_plan": ["task_title_1", "task_title_2"],
    "procrastination_flags": ["task_title_3"],
    "insights": "Overall productivity insights here"
}}"""
        return prompt
    
    @staticmethod
    def analyze_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send tasks to Gemini and get AI analysis"""
        try:
            AIProductivityAgent.initialize()
            prompt = AIProductivityAgent.build_prompt(tasks)
            
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1500
                )
            )
            
            # Extract and parse JSON from response
            response_text = response.text.strip()
            
            # Handle markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            analysis = json.loads(response_text)
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "prioritized_tasks": [],
                "today_plan": [],
                "procrastination_flags": [],
                "insights": "AI analysis failed - using default prioritization"
            }
        except Exception as e:
            logger.error(f"AI service error: {e}")
            # Return mock data for development/testing when API fails
            logger.warning("Returning mock AI analysis for development/testing")
            return AIProductivityAgent._get_mock_analysis(tasks)
    
    @staticmethod
    def _get_mock_analysis(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return mock AI analysis for development/testing when API is unavailable"""
        # Categorize tasks for mock analysis
        prioritized = []
        today_plan = []
        
        for i, task in enumerate(tasks[:6]):  # Max 6 tasks
            category = ["urgent_important", "important_not_urgent", "urgent_not_important", "neither"][i % 4]
            prioritized.append({
                "task_id": task.get("id", i+1),
                "title": task["title"],
                "category": category,
                "reason": f"Mock analysis: classified as {category.replace('_', ' ')}"
            })
            today_plan.append(task["title"])
        
        return {
            "prioritized_tasks": prioritized,
            "today_plan": today_plan,
            "procrastination_flags": [],
            "insights": "⚠️ DEVELOPMENT MODE: Using mock AI analysis. To enable real Gemini analysis, check your API key."
        }
    
    @staticmethod
    def generate_weekly_report(completed: int, pending: int, total: int) -> Dict[str, Any]:
        """Generate a weekly productivity report using Gemini"""
        try:
            AIProductivityAgent.initialize()
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            prompt = f"""As a productivity coach, generate a brief, motivating weekly report based on these metrics:
- Total tasks: {total}
- Completed: {completed}
- Pending: {pending}
- Completion rate: {completion_rate:.1f}%

Return valid JSON only:
{{
    "summary": "...",
    "completion_rate": {completion_rate},
    "strengths": ["..."],
    "areas_for_improvement": ["..."],
    "recommended_actions": ["..."]
}}"""
            
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=800
                )
            )
            
            response_text = response.text.strip()
            
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            report = json.loads(response_text)
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {
                "summary": f"Completed {completed} out of {total} tasks",
                "completion_rate": (completed / total * 100) if total > 0 else 0,
                "strengths": ["Consistent effort"],
                "areas_for_improvement": ["Increase daily focus"],
                "recommended_actions": ["Review blocking issues"]
            }
