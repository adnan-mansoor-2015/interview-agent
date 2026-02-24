import json
import csv
import os
import random
import hashlib
from services.claude_client import claude_client
from prompts.curator_prompts import get_question_curator_prompt

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


class QuestionCurator:
    """Agent responsible for sourcing interview questions from curated CSV banks."""

    def __init__(self):
        self._behavioral_questions = None
        self._technical_topics = None
        self._system_design_questions = None
        self._leetcode_questions = None

    # ── CSV loaders (lazy, load once and cache) ────────────────────

    def _load_csv(self, filename):
        """Load a CSV file from the data directory and return list of dicts."""
        path = os.path.join(DATA_DIR, filename)
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows

    @property
    def behavioral_questions(self):
        if self._behavioral_questions is None:
            self._behavioral_questions = self._load_csv("behavioral_questions.csv")
        return self._behavioral_questions

    @property
    def technical_topics(self):
        if self._technical_topics is None:
            self._technical_topics = self._load_csv("technical_topics.csv")
        return self._technical_topics

    @property
    def system_design_questions(self):
        if self._system_design_questions is None:
            self._system_design_questions = self._load_csv("system_design_questions.csv")
        return self._system_design_questions

    @property
    def leetcode_questions(self):
        if self._leetcode_questions is None:
            self._leetcode_questions = self._load_csv("leetcode_questions.csv")
        return self._leetcode_questions

    # ── Main entry point ───────────────────────────────────────────

    def get_question(self, category: str, focus_areas: list, asked_questions: list):
        """Get a new question based on category, sourcing from CSV banks."""
        try:
            if category == "coding":
                return self._get_coding_question(focus_areas, asked_questions)
            elif category == "behavioral":
                return self._get_behavioral_question(focus_areas, asked_questions)
            elif category == "technical":
                return self._get_technical_question(focus_areas, asked_questions)
            elif category == "system-design":
                return self._get_system_design_question(focus_areas, asked_questions)
            else:
                return {"error": f"Unknown category: {category}"}
        except Exception as e:
            return {"error": f"Failed to generate question: {str(e)}"}

    # ── Coding: pick directly from CSV (no Claude call) ────────────

    def _get_coding_question(self, focus_areas, asked_questions):
        """Pick a LeetCode question from the CSV bank."""
        pool = list(self.leetcode_questions)

        # Filter by focus areas (match against Category column)
        if focus_areas:
            focus_lower = [f.lower() for f in focus_areas]
            filtered = [
                q for q in pool
                if any(f in q.get("Category", "").lower() for f in focus_lower)
            ]
            if filtered:
                pool = filtered

        # Exclude already-asked questions
        pool = [
            q for q in pool
            if self._generate_question_id(q.get("Question", "")) not in asked_questions
        ]

        # Reset pool if all exhausted
        if not pool:
            pool = list(self.leetcode_questions)

        # Sort by rank (lower = higher priority) and pick from top 30
        pool_sorted = sorted(pool, key=lambda q: int(q.get("Rank", 999)))
        top_pool = pool_sorted[: max(30, len(pool_sorted))]
        question = random.choice(top_pool)

        question_id = self._generate_question_id(question.get("Question", ""))
        company_str = question.get("Company", "")
        companies = [c.strip() for c in company_str.split(",")] if company_str else []

        return {
            "question_id": question_id,
            "question_title": question.get("Question", ""),
            "difficulty": question.get("Difficulty", "Medium"),
            "companies": companies,
            "leetcode_url": question.get("LeetCode_Link", ""),
            "hackerrank_url": None,
            "focus_areas": [question.get("Category", "")],
            "optimal_complexity": question.get("IdealTimeComplexity", ""),
            "follow_up": question.get("FollowUp", ""),
        }

    # ── Behavioral: pick directly from CSV (no Claude call) ────────

    def _get_behavioral_question(self, focus_areas, asked_questions):
        """Pick a behavioral question from the CSV bank."""
        pool = list(self.behavioral_questions)

        # Filter by focus areas (match against Leadership_Principle or Company)
        if focus_areas:
            focus_lower = [f.lower() for f in focus_areas]
            filtered = [
                q for q in pool
                if any(
                    f in q.get("Leadership_Principle", "").lower()
                    or f in q.get("Company", "").lower()
                    for f in focus_lower
                )
            ]
            if filtered:
                pool = filtered

        # Exclude already-asked
        pool = [
            q for q in pool
            if self._generate_question_id(q.get("Question", "")) not in asked_questions
        ]

        if not pool:
            pool = list(self.behavioral_questions)

        # Prefer Priority 1 questions
        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        question = random.choice(selection_pool)
        question_id = self._generate_question_id(question.get("Question", ""))

        return {
            "question_id": question_id,
            "question_text": question.get("Question", ""),
            "source": f"{question.get('Company', 'FAANG')} Leadership Principles",
            "company": question.get("Company", "Amazon"),
            "leadership_principle": question.get("Leadership_Principle", ""),
            "star_focus": question.get("STAR_Focus", ""),
            "metadata": {
                "difficulty": "medium",
                "commonly_asked": True,
                "priority": question.get("Priority", "1"),
            },
        }

    # ── Technical: pick topic from CSV, then Claude generates question

    def _get_technical_question(self, focus_areas, asked_questions):
        """Pick a topic from CSV, then ask Claude to create a targeted question.
        Falls back to a CSV-derived question if Claude API is unavailable."""
        pool = list(self.technical_topics)

        # Filter by focus areas (match against Category, Topic, or Sub-Topic)
        if focus_areas:
            focus_lower = [f.lower() for f in focus_areas]
            filtered = [
                q for q in pool
                if any(
                    f in q.get("Category", "").lower()
                    or f in q.get("Topic", "").lower()
                    or f in q.get("Sub-Topic", "").lower()
                    for f in focus_lower
                )
            ]
            if filtered:
                pool = filtered

        # Get the depth point column (handle both possible names)
        def get_depth(row):
            return row.get("Sub-Sub-Topic / Granular Depth Point", row.get("Sub-Sub-Topic", ""))

        # Exclude already-asked
        pool = [
            q for q in pool
            if self._generate_question_id(get_depth(q)) not in asked_questions
        ]

        if not pool:
            pool = list(self.technical_topics)

        # Prefer Priority 1
        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        topic = random.choice(selection_pool)
        depth_point = get_depth(topic)
        topic_id = self._generate_question_id(depth_point)
        focus_area = f"{topic.get('Topic', '')} - {topic.get('Sub-Topic', '')}"

        # Try Claude API to generate a targeted question
        try:
            topic_str = (
                f"Category: {topic.get('Category', '')}, "
                f"Topic: {topic.get('Topic', '')}, "
                f"Sub-Topic: {topic.get('Sub-Topic', '')}, "
                f"Depth: {depth_point}"
            )

            system_prompt = get_question_curator_prompt(
                "technical", focus_areas, asked_questions, topic_context=topic_str
            )

            response = claude_client.send_message(
                system_prompt=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"Generate a senior-level technical interview question about: {topic_str}",
                }],
            )
            content = claude_client.extract_text(response)
            question_data = self._parse_json(content)

            question_data["question_id"] = topic_id
            question_data.setdefault("focus_area", focus_area)
            question_data.setdefault(
                "source",
                f"Senior Backend Engineer - {topic.get('Category', '')}",
            )
            return question_data

        except Exception:
            # Fallback: build question directly from CSV topic (no Claude needed)
            question_text = (
                f"Explain {depth_point} in the context of {topic.get('Topic', '')} "
                f"({topic.get('Sub-Topic', '')}). "
                f"What are the key trade-offs and how would you apply this in a production system?"
            )
            return {
                "question_id": topic_id,
                "question_text": question_text,
                "source": f"Senior Backend Engineer - {topic.get('Category', '')}",
                "company": "FAANG",
                "focus_area": focus_area,
                "metadata": {
                    "difficulty": "senior",
                    "requires_diagram": False,
                },
            }

    # ── System Design: pick directly from CSV (no Claude call) ─────

    def _get_system_design_question(self, focus_areas, asked_questions):
        """Pick a system design question from the CSV bank."""
        pool = list(self.system_design_questions)

        # Exclude already-asked
        pool = [
            q for q in pool
            if self._generate_question_id(q.get("Question", "")) not in asked_questions
        ]

        if not pool:
            pool = list(self.system_design_questions)

        # Prefer Priority 1
        p1 = [q for q in pool if q.get("Priority", "2") == "1"]
        selection_pool = p1 if p1 else pool

        question = random.choice(selection_pool)
        question_id = self._generate_question_id(question.get("Question", ""))

        # Parse Key_Components from comma-separated string to list
        components_str = question.get("Key_Components", "")
        components = [c.strip() for c in components_str.split(",") if c.strip()]

        return {
            "question_id": question_id,
            "question_text": question.get("Question", ""),
            "source": f"Asked at {question.get('Company', 'FAANG')}",
            "company": question.get("Company", ""),
            "scale_requirements": question.get("Scale_Requirements", ""),
            "key_components": components,
            "lp_hints": question.get("LP_Hints", ""),
            "metadata": {
                "difficulty": "senior",
                "commonly_asked": True,
                "priority": question.get("Priority", "1"),
            },
        }

    # ── Helpers ────────────────────────────────────────────────────

    def _parse_json(self, content: str):
        """Extract and parse JSON from Claude's response."""
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)

    def _generate_question_id(self, text: str) -> str:
        """Generate a unique hash-based ID for a question."""
        return hashlib.md5(text.encode()).hexdigest()[:12]


# Global instance
question_curator = QuestionCurator()
