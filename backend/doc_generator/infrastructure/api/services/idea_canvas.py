"""Idea Canvas service with interactive Q&A streaming."""

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator

from loguru import logger

from ....domain.prompts.idea_canvas import (
    first_question_prompt,
    next_question_prompt,
    question_system_prompt,
)
from ....infrastructure.llm import LLMService
from ..schemas.idea_canvas import (
    AnswerRequest,
    ApproachOption,
    CanvasCompleteEvent,
    CanvasErrorEvent,
    CanvasNode,
    CanvasNodeType,
    CanvasProgressEvent,
    CanvasQuestion,
    CanvasQuestionEvent,
    CanvasReadyEvent,
    CanvasState,
    CanvasTemplate,
    QuestionOption,
    QuestionType,
    StartCanvasRequest,
)


class CanvasSession:
    """Represents an active canvas session."""

    def __init__(
        self,
        session_id: str,
        idea: str,
        template: CanvasTemplate,
        provider: str,
        model: str,
    ):
        self.session_id = session_id
        self.idea = idea
        self.template = template
        self.provider = provider
        self.model = model
        self.conversation_history: list[dict] = []
        self.nodes: CanvasNode = CanvasNode(
            id="root",
            type=CanvasNodeType.ROOT,
            label=idea[:150] + ("..." if len(idea) > 150 else ""),
            description=idea,
            children=[],
        )
        self.current_question_id: str | None = None
        self.current_question_options: list[QuestionOption] = (
            []
        )  # Store current question's options
        self.question_count = 0
        self.is_complete = False

    def add_question(
        self,
        question: str,
        question_id: str,
        options: list[QuestionOption] | None = None,
    ) -> None:
        """Add a question node to the tree."""
        question_node = CanvasNode(
            id=question_id,
            type=CanvasNodeType.QUESTION,
            label=question[:120] + ("..." if len(question) > 120 else ""),
            description=question,
            children=[],
        )
        self._find_and_add_child(self.nodes, question_node)
        self.current_question_id = question_id
        self.current_question_options = options or []  # Store options for later
        self.question_count += 1

    def add_answer(
        self, answer: str, answer_id: str, selected_option_id: str | None = None
    ) -> None:
        """Add an answer node to the tree with all available options."""
        answer_node = CanvasNode(
            id=answer_id,
            type=CanvasNodeType.ANSWER,
            label=answer[:120] + ("..." if len(answer) > 120 else ""),
            description=answer,
            children=[],
            options=self.current_question_options,  # Store all options that were available
            selected_option_id=selected_option_id,  # Mark which was selected
        )
        # Find the current question and add answer as its child
        if self.current_question_id:
            self._add_child_to_node(self.nodes, self.current_question_id, answer_node)
        # Clear current question options after adding answer
        self.current_question_options = []

    def _find_and_add_child(self, node: CanvasNode, child: CanvasNode) -> bool:
        """Find the deepest answer node and add child to it."""
        # If this node has no children, add here
        if not node.children:
            node.children.append(child)
            return True

        # Try to find the deepest path (last answer node)
        for i in range(len(node.children) - 1, -1, -1):
            child_node = node.children[i]
            if child_node.type == CanvasNodeType.ANSWER:
                return self._find_and_add_child(child_node, child)

        # If no answer nodes found, add to this node
        node.children.append(child)
        return True

    def _add_child_to_node(
        self, node: CanvasNode, target_id: str, child: CanvasNode
    ) -> bool:
        """Find a node by ID and add a child to it."""
        if node.id == target_id:
            node.children.append(child)
            return True
        for child_node in node.children:
            if self._add_child_to_node(child_node, target_id, child):
                return True
        return False

    def get_state(self) -> CanvasState:
        """Get the current canvas state."""
        return CanvasState(
            session_id=self.session_id,
            idea=self.idea,
            template=self.template,
            nodes=self.nodes,
            question_count=self.question_count,
            is_complete=self.is_complete,
        )


class IdeaCanvasService:
    """Service for managing idea canvas sessions."""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._sessions: dict[str, CanvasSession] = {}

    def _configure_api_key(self, provider: str, api_key: str) -> None:
        """Configure API key in environment for the provider."""
        if provider in ("gemini", "google"):
            os.environ["GEMINI_API_KEY"] = api_key
            os.environ["GOOGLE_API_KEY"] = api_key
        elif provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key

    def _call_llm_with_fallback(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
        step_name: str,
        preferred_model: str | None = None,
    ) -> str:
        """Call LLM with automatic model fallback on errors.

        Tries multiple models in order if one fails with 503/overload errors.
        """
        # Define fallback models for Gemini (in order of preference)
        gemini_models = [
            preferred_model or "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
        ]
        # Remove duplicates while preserving order
        seen = set()
        gemini_models = [
            m for m in gemini_models if m and not (m in seen or seen.add(m))
        ]

        if provider not in ("gemini", "google"):
            # For non-Gemini providers, just use the preferred model
            llm_service = LLMService(
                provider=provider, model=preferred_model or "gpt-4.1-mini"
            )
            return llm_service._call_llm(
                system_prompt,
                user_prompt,
                max_tokens,
                temperature,
                json_mode,
                step_name,
            )

        last_error = None
        for model in gemini_models:
            try:
                llm_service = LLMService(provider=provider, model=model)
                result = llm_service._call_llm(
                    system_prompt,
                    user_prompt,
                    max_tokens,
                    temperature,
                    json_mode,
                    step_name,
                )
                return result
            except Exception as e:
                error_str = str(e)
                # Check if it's a 503/overload error that we should retry
                if (
                    "503" in error_str
                    or "overload" in error_str.lower()
                    or "unavailable" in error_str.lower()
                ):
                    logger.warning(
                        f"Model {model} overloaded, trying next model. Error: {error_str[:100]}"
                    )
                    last_error = e
                    continue
                else:
                    # For other errors, don't retry
                    raise e

        # If all models failed, raise the last error
        if last_error:
            raise last_error
        raise ValueError("No models available")

    def _parse_question_response(self, response: str) -> dict:
        """Parse LLM response into question data."""
        try:
            data = json.loads(response)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON from response
            return self._extract_json(response) or {}

    def _extract_json(self, text: str) -> dict | None:
        """Try to extract JSON object from text."""
        if not text:
            return None

        start_idx = text.find("{")
        if start_idx == -1:
            return None

        stack = []
        for i in range(start_idx, len(text)):
            ch = text[i]
            if ch == "{":
                stack.append(ch)
            elif ch == "}":
                if stack:
                    stack.pop()
                    if not stack:
                        try:
                            return json.loads(text[start_idx : i + 1])
                        except json.JSONDecodeError:
                            return None
        return None

    def _build_canvas_question(self, data: dict, question_id: str) -> CanvasQuestion:
        """Build a CanvasQuestion from parsed LLM response."""
        question_type = QuestionType(data.get("type", "single_choice"))

        options = []
        if question_type == QuestionType.SINGLE_CHOICE:
            for opt in data.get("options", []):
                options.append(
                    QuestionOption(
                        id=opt.get("id", f"opt_{uuid.uuid4().hex[:6]}"),
                        label=opt.get("label", ""),
                        description=opt.get("description"),
                        recommended=opt.get("recommended", False),
                    )
                )

        approaches = []
        if question_type == QuestionType.APPROACH:
            for appr in data.get("approaches", []):
                approaches.append(
                    ApproachOption(
                        id=appr.get("id", f"appr_{uuid.uuid4().hex[:6]}"),
                        title=appr.get("title", ""),
                        description=appr.get("description", ""),
                        pros=appr.get("pros", []),
                        cons=appr.get("cons", []),
                        recommended=appr.get("recommended", False),
                    )
                )

        return CanvasQuestion(
            id=question_id,
            question=data.get("question", "What would you like to do?"),
            type=question_type,
            options=options,
            approaches=approaches,
            allow_skip=True,
            context=data.get("context"),
        )

    async def start_session(
        self,
        request: StartCanvasRequest,
        api_key: str,
        user_id: str | None = None,
    ) -> AsyncIterator[
        CanvasReadyEvent | CanvasQuestionEvent | CanvasProgressEvent | CanvasErrorEvent
    ]:
        """Start a new canvas session and generate the first question.

        Args:
            request: Start canvas request
            api_key: API key for LLM provider
            user_id: Optional user ID

        Yields:
            Canvas events
        """
        try:
            # Create session
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            provider = request.provider.value
            if provider == "google":
                provider = "gemini"

            session = CanvasSession(
                session_id=session_id,
                idea=request.idea,
                template=request.template,
                provider=provider,
                model=request.model,
            )
            self._sessions[session_id] = session

            yield CanvasProgressEvent(message="Starting canvas session...")

            # Configure LLM
            self._configure_api_key(provider, api_key)
            llm_service = LLMService(provider=provider, model=request.model)

            if not llm_service.is_available():
                raise ValueError(f"LLM service not available for provider: {provider}")

            yield CanvasProgressEvent(message="Generating first question...")

            # Generate first question
            import asyncio

            loop = asyncio.get_event_loop()

            system_prompt = question_system_prompt(request.template.value)
            user_prompt = first_question_prompt(request.idea, request.template.value)

            response = await loop.run_in_executor(
                self._executor,
                llm_service._call_llm,
                system_prompt,
                user_prompt,
                2000,
                0.7,
                True,
                "first_question",
            )

            # Parse response
            question_data = self._parse_question_response(response)
            question_id = f"q_{uuid.uuid4().hex[:8]}"
            question = self._build_canvas_question(question_data, question_id)

            # Add question to session with its options
            session.add_question(question.question, question_id, question.options)

            # Yield ready event with first question
            yield CanvasReadyEvent(
                session_id=session_id,
                canvas=session.get_state(),
            )

            yield CanvasQuestionEvent(
                question=question,
                canvas=session.get_state(),
            )

        except Exception as e:
            logger.error(f"Failed to start canvas session: {e}")
            yield CanvasErrorEvent(
                message=str(e),
                code="START_ERROR",
            )

    async def submit_answer(
        self,
        request: AnswerRequest,
        api_key: str,
        user_id: str | None = None,
    ) -> AsyncIterator[
        CanvasQuestionEvent
        | CanvasCompleteEvent
        | CanvasProgressEvent
        | CanvasErrorEvent
    ]:
        """Submit an answer and get the next question.

        Args:
            request: Answer request
            api_key: API key for LLM provider
            user_id: Optional user ID

        Yields:
            Canvas events
        """
        try:
            session = self._sessions.get(request.session_id)
            if not session:
                raise ValueError(f"Session not found: {request.session_id}")

            yield CanvasProgressEvent(message="Processing answer...")

            # Format answer
            answer_str = (
                request.answer
                if isinstance(request.answer, str)
                else ", ".join(request.answer)
            )

            # Add answer to conversation history
            session.conversation_history.append(
                {
                    "question": (
                        session.nodes.children[-1].label
                        if session.nodes.children
                        else ""
                    ),
                    "answer": answer_str,
                }
            )

            # Add answer node - find matching option ID if user selected an option
            answer_id = f"a_{uuid.uuid4().hex[:8]}"
            selected_option_id = None
            for opt in session.current_question_options:
                if opt.label == answer_str or opt.id == answer_str:
                    selected_option_id = opt.id
                    break
            session.add_answer(answer_str, answer_id, selected_option_id)

            # Configure LLM
            self._configure_api_key(session.provider, api_key)
            llm_service = LLMService(provider=session.provider, model=session.model)

            yield CanvasProgressEvent(message="Generating next question...")

            # Generate next question
            import asyncio

            loop = asyncio.get_event_loop()

            system_prompt = question_system_prompt(session.template.value)
            user_prompt = next_question_prompt(
                session.idea,
                session.conversation_history,
                session.question_count,
            )

            response = await loop.run_in_executor(
                self._executor,
                llm_service._call_llm,
                system_prompt,
                user_prompt,
                2000,
                0.7,
                True,
                "next_question",
            )

            # Parse response
            question_data = self._parse_question_response(response)

            # Check if LLM suggests completion (primary decision maker)
            # Only use hard cap of 25 as absolute fallback
            llm_suggests_complete = question_data.get("suggest_complete", False)
            hard_cap_reached = session.question_count >= 25

            if llm_suggests_complete or hard_cap_reached:
                session.is_complete = True
                # Use LLM's summary if provided
                summary = question_data.get("summary", "")
                if summary:
                    completion_msg = summary
                elif hard_cap_reached:
                    completion_msg = (
                        "We've covered a lot of ground! "
                        "Ready to generate your implementation spec."
                    )
                else:
                    completion_msg = (
                        "I think we've explored the key areas of your idea. "
                        "Ready to generate your implementation spec?"
                    )
                yield CanvasCompleteEvent(
                    message=completion_msg,
                    canvas=session.get_state(),
                )
                return

            # Build and add question with its options
            question_id = f"q_{uuid.uuid4().hex[:8]}"
            question = self._build_canvas_question(question_data, question_id)
            session.add_question(question.question, question_id, question.options)

            yield CanvasQuestionEvent(
                question=question,
                canvas=session.get_state(),
            )

        except Exception as e:
            logger.error(f"Failed to process answer: {e}")
            yield CanvasErrorEvent(
                message=str(e),
                code="ANSWER_ERROR",
            )

    def get_session(self, session_id: str) -> CanvasSession | None:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def generate_approaches(self, session_id: str, api_key: str) -> dict:
        """Generate 4 implementation approaches from the Q&A session.

        Args:
            session_id: The session ID
            api_key: API key for LLM

        Returns:
            Dict with list of 4 approaches, each containing mermaid diagram and tasks
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        self._configure_api_key(session.provider, api_key)

        # Build Q&A summary
        qa_summary = ""
        for i, item in enumerate(session.conversation_history, 1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            qa_summary += f"\nQ{i}: {question}\nA{i}: {answer}\n"

        system_prompt = """You are an expert solution architect. Generate exactly 4 different implementation approaches for the given idea.

For each approach, provide:
1. A unique descriptive name (e.g., "Microservices", "Serverless", "Monolith", "Hybrid")
2. A mermaid diagram showing the architecture or flow
3. A list of implementation tasks with tech stack and complexity

Return ONLY valid JSON in this exact format:
{
  "approaches": [
    {
      "id": "approach_1",
      "name": "Descriptive Name",
      "mermaidCode": "flowchart TD\\n    A[Start] --> B[Process]\\n    B --> C[End]",
      "tasks": [
        {
          "id": "task_1",
          "name": "Task Name",
          "description": "What this task involves",
          "techStack": "React, Node.js",
          "complexity": "Medium"
        }
      ]
    }
  ]
}

MERMAID RULES:
- Use flowchart TD (top-down) or LR (left-right) for architecture
- Use sequenceDiagram for interactions
- Use graph for simple flows
- Escape special characters properly
- Keep diagrams clear and readable
- Use descriptive node labels

TASK RULES:
- 4-8 tasks per approach
- Complexity: Low, Medium, or High
- Tech stack: comma-separated technologies
- Description: 1-2 sentences explaining the task"""

        user_prompt = f"""Generate 4 different implementation approaches for this idea.

IDEA: {session.idea}

TEMPLATE: {session.template.value.replace('_', ' ').title()}

Q&A CONTEXT:
{qa_summary}

Generate 4 distinct approaches with varying complexity/architecture styles:
1. A simple/minimal approach (fastest to implement)
2. A balanced/standard approach (good tradeoffs)
3. A scalable/enterprise approach (more complex but scales better)
4. An innovative/modern approach (using latest technologies)

Each approach should have a mermaid diagram and implementation tasks.
Return ONLY the JSON object."""

        response = self._call_llm_with_fallback(
            provider=session.provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=6000,
            temperature=0.7,
            json_mode=True,
            step_name="generate_approaches",
            preferred_model=session.model,
        )

        # Parse response
        data = self._parse_question_response(response)

        if not data or "approaches" not in data:
            # Create fallback structure
            data = {"approaches": self._create_fallback_approaches(session)}

        return data

    def _create_fallback_approaches(self, session: CanvasSession) -> list[dict]:
        """Create fallback approaches if LLM response is invalid."""
        base_name = session.idea[:30] if len(session.idea) > 30 else session.idea

        return [
            {
                "id": "approach_1",
                "name": "Simple MVP",
                "mermaidCode": f"flowchart TD\n    A[User] --> B[{base_name}]\n    B --> C[Database]",
                "tasks": [
                    {"id": "t1", "name": "Setup project", "description": "Initialize project structure", "techStack": "Node.js", "complexity": "Low"},
                    {"id": "t2", "name": "Build core feature", "description": "Implement main functionality", "techStack": "React", "complexity": "Medium"},
                ]
            },
            {
                "id": "approach_2",
                "name": "Standard Stack",
                "mermaidCode": "flowchart TD\n    A[Frontend] --> B[API]\n    B --> C[Service]\n    C --> D[Database]",
                "tasks": [
                    {"id": "t1", "name": "Frontend setup", "description": "Build user interface", "techStack": "React, TypeScript", "complexity": "Medium"},
                    {"id": "t2", "name": "API development", "description": "Create REST endpoints", "techStack": "FastAPI", "complexity": "Medium"},
                ]
            },
            {
                "id": "approach_3",
                "name": "Scalable Architecture",
                "mermaidCode": "flowchart TD\n    A[Load Balancer] --> B[Service 1]\n    A --> C[Service 2]\n    B --> D[Cache]\n    C --> D\n    D --> E[Database]",
                "tasks": [
                    {"id": "t1", "name": "Microservices setup", "description": "Design service boundaries", "techStack": "Docker, K8s", "complexity": "High"},
                    {"id": "t2", "name": "Caching layer", "description": "Add Redis caching", "techStack": "Redis", "complexity": "Medium"},
                ]
            },
            {
                "id": "approach_4",
                "name": "Modern Serverless",
                "mermaidCode": "flowchart TD\n    A[CDN] --> B[Edge Functions]\n    B --> C[Serverless API]\n    C --> D[Managed DB]",
                "tasks": [
                    {"id": "t1", "name": "Serverless setup", "description": "Configure cloud functions", "techStack": "AWS Lambda, Vercel", "complexity": "Medium"},
                    {"id": "t2", "name": "Edge optimization", "description": "Deploy edge functions", "techStack": "Cloudflare Workers", "complexity": "Medium"},
                ]
            },
        ]

    def refine_approach(
        self,
        session_id: str,
        api_key: str,
        approach_index: int,
        element_id: str,
        element_type: str,
        refinement_answer: str,
        current_approach: dict,
    ) -> dict:
        """Refine a specific approach based on user feedback.

        Args:
            session_id: The session ID
            api_key: API key for LLM
            approach_index: Index of the approach to refine
            element_id: ID of the clicked element
            element_type: 'diagram' or 'task'
            refinement_answer: User's refinement answer
            current_approach: Current approach data

        Returns:
            Updated approach dict
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        self._configure_api_key(session.provider, api_key)

        system_prompt = """You are refining an implementation approach based on user feedback.

Update ONLY the relevant parts of the approach while keeping the overall structure.
Return the complete updated approach in the same JSON format.

{
  "id": "approach_id",
  "name": "Approach Name",
  "mermaidCode": "updated mermaid code",
  "tasks": [updated tasks array]
}"""

        user_prompt = f"""Refine this approach based on user feedback.

CURRENT APPROACH:
{json.dumps(current_approach, indent=2)}

USER CLICKED ON: {element_type} with ID "{element_id}"

USER'S REFINEMENT REQUEST: {refinement_answer}

Update the approach to address the user's feedback. If they clicked on:
- A diagram element: Update the mermaid code and related tasks
- A task: Update that specific task and potentially related diagram elements

Return the complete updated approach as JSON."""

        response = self._call_llm_with_fallback(
            provider=session.provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.6,
            json_mode=True,
            step_name="refine_approach",
            preferred_model=session.model,
        )

        data = self._parse_question_response(response)

        if not data or "id" not in data:
            # Return original if parsing failed
            return current_approach

        return data

    def generate_report(
        self, session_id: str, api_key: str, image_api_key: str | None = None
    ) -> dict:
        """Generate an LLM-powered implementation plan from a canvas session.

        Args:
            session_id: The session ID
            api_key: API key for LLM
            image_api_key: API key for image generation (optional)

        Returns:
            Dict with title and markdown_content
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Configure LLM
        self._configure_api_key(session.provider, api_key)
        llm_service = LLMService(provider=session.provider, model=session.model)

        # Build Q&A summary for the LLM
        qa_summary = ""
        for i, item in enumerate(session.conversation_history, 1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            qa_summary += f"\nQ{i}: {question}\nA{i}: {answer}\n"

        # Create dynamic prompt based on template type
        template_name = session.template.value

        # Define sections based on template type
        if template_name == "startup":
            # Startup planning template with specific sections
            sections_guidance = """1. **Hook & Problem Statement**
   - Start with one compelling story OR one striking statistic that illustrates the problem
   - Explain why this problem matters NOW (timing, market trends, urgency)
   - Define the user/customer clearly - who exactly experiences this pain?
   - Current workflow: How do they solve this problem today? What's broken/inefficient?

2. **Solution Overview**
   - What is the core solution and how does it solve the problem?
   - Key differentiators from existing solutions
   - MVP scope: What are the essential features for launch?

3. **Market Opportunity & Audience**
   - Target market size (TAM, SAM, SOM if applicable)
   - Customer segments and personas
   - Customer acquisition strategy
   - Go-to-market approach

4. **Business / Impact Model**
   - Revenue streams OR impact metrics (for non-profit/internal tools)
   - Impact generated:
     * Productivity improvements (time saved, efficiency gains)
     * Quality improvements
     * Cost savings
     * Revenue potential or risk reduction
   - Integration and adoption path - how will users transition to this solution?
   - Pricing strategy (if applicable)

5. **Implementation Roadmap**
   - Phase 1 (MVP): Core features and timeline
   - Phase 2: Growth features
   - Future: Long-term vision

6. **Team & Resources**
   - Key roles needed
   - Technology requirements
   - Budget considerations

7. **Risk Analysis & Mitigation**
   - Key risks (market, technical, execution)
   - Mitigation strategies

8. **Next Steps**
   - Immediate action items to validate and begin"""
            doc_type = "Startup Plan"
            writer_role = "expert startup advisor and business strategist"
        elif template_name in ("web_app", "ai_agent", "tech_stack"):
            # Technical templates with code examples
            sections_guidance = """1. **Executive Summary** - A brief overview of the project (2-3 paragraphs)
2. **Project Overview** - Goals, target users, and key value propositions
3. **Technical Architecture** - Recommended tech stack, system components, and architecture patterns
4. **Feature Breakdown** - Detailed list of features organized by priority (MVP, Phase 2, Future)
5. **Implementation Roadmap** - Phased approach with milestones and estimated timelines
6. **Code Examples** - Include relevant Python/SQL code snippets for key components
7. **Risk Analysis** - Potential challenges and mitigation strategies
8. **Success Metrics** - KPIs and how to measure project success
9. **Next Steps** - Immediate action items to get started"""
            doc_type = "Implementation Plan"
            writer_role = "expert technical writer and product strategist"
        elif template_name == "project_spec":
            # Project specification
            sections_guidance = """1. **Executive Summary** - Brief overview of the project scope
2. **Project Goals & Objectives** - What success looks like
3. **Scope & Deliverables** - What's included and excluded
4. **Requirements** - Functional and non-functional requirements
5. **Timeline & Milestones** - Key dates and checkpoints
6. **Resources & Budget** - Required resources and cost estimates
7. **Risks & Dependencies** - Potential blockers and how to mitigate
8. **Acceptance Criteria** - How deliverables will be validated"""
            doc_type = "Project Specification"
            writer_role = "expert project manager and technical writer"
        elif template_name == "implement_feature":
            # Feature implementation planning
            sections_guidance = """1. **Feature Overview** - What this feature does and why it matters
2. **User Stories** - Who benefits and how
3. **Functional Requirements** - Detailed behavior specifications
4. **UI/UX Considerations** - Interface and experience design notes
5. **Technical Approach** - How to implement this feature
6. **Edge Cases & Error Handling** - What could go wrong and how to handle it
7. **Testing Strategy** - How to validate the feature works correctly
8. **Rollout Plan** - How to release this feature safely"""
            doc_type = "Feature Implementation Spec"
            writer_role = "expert product manager and technical writer"
        else:
            # Custom/general ideas - adapt to content dynamically
            sections_guidance = """Analyze the idea and questions/answers to determine the appropriate document structure.
Choose sections that make sense for this specific idea. Examples:

For creative projects (books, art, music):
- Vision & Concept, Target Audience, Creative Direction, Content Outline, Production Plan, Distribution Strategy

For business ideas:
- Executive Summary, Market Analysis, Value Proposition, Business Model, Go-to-Market Strategy, Financial Projections

For personal projects (travel, events, learning):
- Overview, Goals & Objectives, Planning Details, Timeline, Budget, Resources Needed

For research or academic work:
- Abstract, Background, Methodology, Expected Outcomes, Timeline, References

Choose the most appropriate structure based on the actual idea content."""
            doc_type = "Comprehensive Plan"
            writer_role = "expert writer who adapts to any domain"

        system_prompt = f"""You are an {writer_role}. Your task is to generate a comprehensive {doc_type} document based on the user's idea exploration session.

The document should be in Markdown format. Structure it with the following sections (adapt as needed based on the idea):

{sections_guidance}

CRITICAL FORMATTING RULES:
1. Use proper Markdown headers: # for main title, ## for sections, ### for subsections
2. Use bullet points (- ) for lists of items
3. ALWAYS wrap code in triple backticks with the language specified:
   ```python
   # Python code here
   ```
   ```sql
   -- SQL code here
   ```
4. NEVER write code as plain text or bullet points
5. Every code example MUST be in a fenced code block with language tag

CODE REQUIREMENTS:
- For technical projects, include practical code examples
- Use Python for: backend logic, API endpoints, data processing, automation
- Use SQL for: database schemas, queries, migrations
- Use bash for: setup commands, deployment scripts
- Each code block should be complete and runnable
- Include comments in code to explain key parts

Make the document actionable, specific, and tailored to the decisions made during the exploration session."""

        user_prompt = f"""Based on the following idea exploration session, generate a comprehensive {doc_type} document.

ORIGINAL IDEA:
{session.idea}

TEMPLATE: {session.template.value.replace('_', ' ').title()}

EXPLORATION Q&A:
{qa_summary}

Generate a detailed, actionable {doc_type} document in Markdown format.

REQUIREMENTS:
1. Reference the specific decisions and answers from the exploration
2. Include Python and SQL code examples where relevant
3. CRITICAL: All code MUST be in fenced code blocks with triple backticks and language tag
4. Do NOT write code as plain text or bullet points
5. Each code example should be complete and practical

Example of correct code formatting:
```python
def example_function():
    return "This is correct"
```

Wrong (do NOT do this):
- def example_function():
- return "This is wrong\""""

        # Generate the implementation plan with model fallback
        response = self._call_llm_with_fallback(
            provider=session.provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.7,
            json_mode=False,
            step_name="generate_report",
            preferred_model=session.model,
        )

        # Clean up the response (remove markdown code blocks if present)
        markdown_content = response.strip()
        if markdown_content.startswith("```markdown"):
            markdown_content = markdown_content[11:]
        if markdown_content.startswith("```"):
            markdown_content = markdown_content[3:]
        if markdown_content.endswith("```"):
            markdown_content = markdown_content[:-3]
        markdown_content = markdown_content.strip()

        # Add decision tree from the canvas
        decision_tree = self._build_decision_tree_markdown(session.nodes)

        # Add header and footer
        title = (
            f"{doc_type}: {session.idea[:50]}{'...' if len(session.idea) > 50 else ''}"
        )

        from datetime import datetime

        footer = f"\n\n---\n*Generated by PrismDocs on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Based on {session.question_count} exploration questions*"

        full_content = markdown_content
        if decision_tree:
            full_content += f"\n\n{decision_tree}"
        full_content += footer

        summary_image_base64 = None
        if image_api_key:
            summary_image_base64 = self._generate_report_image(
                title, markdown_content, image_api_key
            )

        # Generate PDF
        pdf_base64 = self._generate_pdf_from_markdown(
            title, full_content, image_base64=summary_image_base64
        )

        return {
            "title": title,
            "markdown_content": full_content,
            "pdf_base64": pdf_base64,
            "image_base64": summary_image_base64,
            "image_format": "png" if summary_image_base64 else None,
        }

    def _generate_pdf_from_markdown(
        self,
        title: str,
        markdown_content: str,
        image_base64: str | None = None,
    ) -> str:
        """Generate PDF from markdown content and return as base64 string.

        Args:
            title: Document title
            markdown_content: Markdown content to convert
            image_base64: Optional base64 image to embed in PDF

        Returns:
            Base64-encoded PDF data
        """
        import base64
        import re
        import tempfile
        from pathlib import Path
        from datetime import datetime

        try:
            from ....infrastructure.generators.pdf.generator import PDFGenerator

            pdf_generator = PDFGenerator()

            # Create temporary directory for output
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Generate a clean filename from the title
                # Remove special characters and limit length
                clean_title = re.sub(r"[^\w\s-]", "", title).strip()
                clean_title = re.sub(r"[-\s]+", "_", clean_title)[:50]
                filename = f"{clean_title}.pdf" if clean_title else "canvas_report.pdf"

                pdf_markdown = markdown_content
                if image_base64:
                    image_path = temp_path / "idea_canvas_summary.png"
                    try:
                        cleaned = image_base64.split(",", 1)[-1]
                        image_path.write_bytes(base64.b64decode(cleaned))
                        pdf_markdown = (
                            f"![Implementation Summary]({image_path})\n\n"
                            + markdown_content
                        )
                    except Exception as exc:
                        logger.warning(f"Failed to embed summary image: {exc}")

                # Prepare content for PDF generator
                content = {
                    "title": title,
                    "markdown": pdf_markdown,
                }

                metadata = {
                    "title": title,  # PDF generator uses this for display title
                    "custom_filename": (
                        clean_title if clean_title else "canvas_report"
                    ),  # For file output
                    "source": "Idea Canvas",
                    "created_at": datetime.now().isoformat(),
                    "content_type": "Implementation Spec",
                }

                # Generate PDF
                pdf_path = pdf_generator.generate(content, metadata, temp_path)

                # Read and encode as base64
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

                return pdf_base64

        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            return ""

    def _add_node_to_markdown(self, node: CanvasNode, lines: list, depth: int) -> None:
        """Recursively add canvas nodes to markdown."""
        indent = "  " * depth

        if node.type == CanvasNodeType.ROOT:
            lines.append(f"- 💡 **{node.label}**")
        elif node.type == CanvasNodeType.QUESTION:
            lines.append(f"{indent}- ❓ *{node.label}*")
        elif node.type == CanvasNodeType.ANSWER:
            lines.append(f"{indent}- ✅ **{node.label}**")
        elif node.type == CanvasNodeType.APPROACH:
            lines.append(f"{indent}- 🔧 **{node.label}**")

        for child in node.children:
            self._add_node_to_markdown(child, lines, depth + 1)

    def _build_decision_tree_markdown(self, root: CanvasNode) -> str:
        """Build a markdown decision tree section from the canvas nodes."""
        lines: list[str] = []
        self._add_node_to_markdown(root, lines, 0)
        if not lines:
            return ""
        return "## Decision Tree\n\n" + "\n".join(lines)

    def _generate_report_image(
        self, title: str, markdown_content: str, api_key: str
    ) -> str | None:
        """Generate a summary image for the report."""
        from ....domain.image_styles import get_style_by_id
        from ....infrastructure.image.image_service import ImageService

        if not api_key:
            return None

        service = ImageService(api_key=api_key)
        if not service.is_available():
            return None

        snippet = (markdown_content or "").strip()[:1500]
        prompt = (
            "Create a clean, hand-drawn style infographic that summarizes this "
            "implementation plan. Use warm colors, whiteboard aesthetics, simple "
            "icons, and arrows connecting concepts. Include the main title at the top.\n\n"
            f"Title: {title}\n\nKey points to visualize:\n{snippet}"
        )

        style = get_style_by_id("whiteboard_handwritten")
        image_data, _prompt_used = service.generate_raster_image(
            prompt=prompt, style=style, free_text_mode=False
        )
        return image_data

    def generate_mindmap_from_session(self, session_id: str, api_key: str) -> dict:
        """Generate a mind map from the canvas session's implementation report.

        This first generates an implementation report from the Q&A, then creates
        a mind map visualization of that report.

        Args:
            session_id: The session ID
            api_key: API key for LLM

        Returns:
            MindMapTree-compatible dict
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Configure API key for LLM calls
        self._configure_api_key(session.provider, api_key)

        # Step 1: Generate the implementation report from Q&A
        # (Reuse the report generation logic but just get the markdown)
        qa_summary = ""
        for i, item in enumerate(session.conversation_history, 1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            qa_summary += f"\nQ{i}: {question}\nA{i}: {answer}\n"

        template_name = session.template.value

        report_system_prompt = """You are an expert technical writer. Generate a concise implementation plan based on the exploration session. 
Focus on actionable items organized by category. Use markdown format with clear headers."""

        report_user_prompt = f"""Based on this idea exploration session, generate a concise implementation plan.

ORIGINAL IDEA: {session.idea}
TEMPLATE: {template_name.replace('_', ' ').title()}

EXPLORATION Q&A:
{qa_summary}

Generate a structured implementation plan with clear sections for:
- Overview (1-2 sentences)
- Key Components/Features
- Technical Approach  
- Implementation Steps
- Next Actions"""

        # Generate the report content with model fallback
        report_content = self._call_llm_with_fallback(
            provider=session.provider,
            system_prompt=report_system_prompt,
            user_prompt=report_user_prompt,
            max_tokens=3000,
            temperature=0.6,
            json_mode=False,
            step_name="generate_report_for_mindmap",
            preferred_model=session.model,
        )

        # Step 2: Generate mind map from the implementation report
        mindmap_system_prompt = """You are an expert at creating clear, hierarchical mind maps.

Your task is to analyze an implementation plan and generate a mind map structure as JSON.

The JSON structure must follow this exact format:
{
  "title": "Project Name",
  "summary": "Brief 1-2 sentence summary of the implementation",
  "nodes": {
    "id": "root",
    "label": "Project Name",
    "children": [
      {
        "id": "1",
        "label": "Component/Phase 1",
        "children": [
          {"id": "1.1", "label": "Task/Feature", "children": []},
          {"id": "1.2", "label": "Task/Feature", "children": []}
        ]
      }
    ]
  }
}

Rules:
1. The root node should be the project/idea name
2. First-level children should be major components, phases, or categories
3. Deeper levels should break down into specific tasks, features, or sub-components
4. Each node must have unique "id", concise "label" (max 50 chars), and "children" array
5. Make labels actionable and clear
6. Determine the appropriate depth based on content complexity (2-6 levels as needed)
7. Return ONLY the JSON object, no markdown code blocks"""

        mindmap_user_prompt = f"""Create a mind map from this implementation plan.

GUIDELINES:
- Use as many levels of depth as needed to properly represent the implementation
- Simple projects may only need 2-3 levels, complex ones may need 4-6 levels
- Aim for 3-7 children per node where appropriate
- Group by implementation phases, components, or logical categories
- Focus on actionable items and key decisions
- The structure should reflect the natural hierarchy of the implementation

IMPLEMENTATION PLAN:
{report_content}

Generate the mind map JSON now. Return ONLY valid JSON."""

        # Use Pro model for mindmap JSON as it produces better structured output
        response = self._call_llm_with_fallback(
            provider=session.provider,
            system_prompt=mindmap_system_prompt,
            user_prompt=mindmap_user_prompt,
            max_tokens=4000,
            temperature=0.5,
            json_mode=True,
            step_name="generate_mindmap",
            preferred_model="gemini-2.5-pro",  # Pro produces better JSON
        )

        # Parse response - handle various JSON formats
        data = None

        # First, try direct JSON parse
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            pass

        # If direct parse failed, try to extract JSON from markdown code blocks
        if data is None:
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            try:
                data = json.loads(cleaned_response)
            except json.JSONDecodeError:
                pass

        # If still no luck, try to extract JSON object from text
        if data is None:
            data = self._extract_json(response)

        # If all parsing attempts failed, create a fallback structure
        if data is None:
            logger.warning(
                f"Failed to parse mindmap JSON, using fallback structure. Response: {response[:500]}"
            )
            # Create a basic fallback mind map from the session
            data = {
                "title": session.idea[:50] if len(session.idea) > 50 else session.idea,
                "summary": f"Implementation plan based on {session.question_count} exploration questions",
                "nodes": {
                    "id": "root",
                    "label": (
                        session.idea[:50] if len(session.idea) > 50 else session.idea
                    ),
                    "children": [
                        {"id": "1", "label": "Overview", "children": []},
                        {"id": "2", "label": "Key Features", "children": []},
                        {"id": "3", "label": "Implementation", "children": []},
                        {"id": "4", "label": "Next Steps", "children": []},
                    ],
                },
            }

        # Build MindMapTree-compatible structure
        return {
            "title": data.get("title", session.idea[:50]),
            "summary": data.get("summary", ""),
            "source_count": session.question_count,
            "mode": "summarize",
            "nodes": self._ensure_node_structure(data.get("nodes", {})),
        }

    def _ensure_node_structure(self, node_data: dict) -> dict:
        """Ensure node has proper structure with id, label, children."""
        import uuid as uuid_mod

        node_id = str(node_data.get("id", uuid_mod.uuid4().hex[:8]))
        label = str(node_data.get("label", ""))[:100]

        children = []
        for child_data in node_data.get("children", []):
            children.append(self._ensure_node_structure(child_data))

        return {
            "id": node_id,
            "label": label,
            "children": children,
        }


# Singleton instance
_idea_canvas_service: IdeaCanvasService | None = None


def get_idea_canvas_service() -> IdeaCanvasService:
    """Get or create idea canvas service instance."""
    global _idea_canvas_service
    if _idea_canvas_service is None:
        _idea_canvas_service = IdeaCanvasService()
    return _idea_canvas_service
