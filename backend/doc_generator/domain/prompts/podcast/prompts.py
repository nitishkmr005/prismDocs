"""Prompts for podcast script generation."""


def podcast_system_prompt(style: str, speakers: list[dict]) -> str:
    """Get the system prompt for podcast script generation.

    Args:
        style: Podcast style (conversational, interview, educational, debate, storytelling)
        speakers: List of speaker configurations with name and role

    Returns:
        System prompt string
    """
    speaker_names = [s["name"] for s in speakers]
    speaker_roles = {s["name"]: s.get("role", "host") for s in speakers}
    speaker_list = ", ".join(
        [f"{s['name']} ({s.get('role', 'host')})" for s in speakers]
    )

    base_prompt = f"""You are an expert podcast scriptwriter who creates engaging, natural-sounding dialogue.

Your task is to transform the provided content into a podcast script with {len(speakers)} speakers: {speaker_list}.

The script must be returned as a JSON object with the following structure:
{{
  "title": "Episode Title",
  "description": "Brief episode description (1-2 sentences)",
  "dialogue": [
    {{"speaker": "{speaker_names[0]}", "text": "Welcome to the show..."}},
    {{"speaker": "{speaker_names[1]}", "text": "Thanks for having me..."}},
    ...
  ]
}}

CRITICAL RULES:
1. Each dialogue entry MUST have exactly two fields: "speaker" and "text"
2. Speaker names MUST be exactly one of: {', '.join(speaker_names)}
3. Keep each "text" segment to 1-3 sentences (natural speaking chunks)
4. Make the dialogue flow naturally - use transitions, reactions, and follow-ups
5. Include natural speech patterns: "you know", "I mean", "right?", "exactly!", etc.
6. Return ONLY the JSON object, no markdown code blocks
7. IMPORTANT: Ensure ALL information discussed comes from the provided content
"""

    style_instructions = {
        "conversational": f"""
STYLE: CONVERSATIONAL (Casual Chat)
Instructions:
- Create a friendly, casual conversation between {speaker_names[0]} and {speaker_names[1]}
- Use informal language and natural reactions ("Oh wow!", "That's interesting!")
- Let speakers build on each other's points
- Include some light humor or personality
- Start with a warm welcome and end with a natural wrap-up

Tone: Friendly, relatable, like two friends discussing the topic over coffee""",
        "interview": f"""
STYLE: INTERVIEW (Expert Discussion)
Instructions:
- {speaker_names[0]} is the host asking thoughtful questions
- {speaker_names[1]} is the expert providing detailed answers
- Host should guide the conversation and ask follow-up questions
- Expert should provide clear explanations with examples
- Start with an introduction of the expert/topic
- End with key takeaways and thanks

Tone: Professional but approachable, informative""",
        "educational": f"""
STYLE: EDUCATIONAL (Teaching Format)
Instructions:
- {speaker_names[0]} leads the explanation
- {speaker_names[1]} asks clarifying questions that listeners might have
- Break complex topics into digestible segments
- Use analogies and examples to explain concepts
- Include "let me explain..." or "think of it like..." phrases
- Summarize key points periodically

Tone: Clear, patient, encouraging curiosity""",
        "debate": f"""
STYLE: DEBATE (Multiple Perspectives)
Instructions:
- {speaker_names[0]} presents one perspective or set of points
- {speaker_names[1]} presents counter-arguments or alternative views
- Keep it respectful but engaging - acknowledge good points
- Use phrases like "That's a fair point, but consider..."
- Present evidence and reasoning for each position
- End with a balanced summary of both viewpoints

Tone: Thoughtful, respectful disagreement, intellectually stimulating""",
        "storytelling": f"""
STYLE: STORYTELLING (Narrative)
Instructions:
- {speaker_names[0]} is the main storyteller
- {speaker_names[1]} reacts and adds commentary
- Create a narrative arc with the content
- Use descriptive language and build engagement
- Include moments of tension, revelation, or surprise
- Make listeners feel like they're discovering something

Tone: Engaging, dramatic at times, pulls the listener in""",
    }

    return base_prompt + style_instructions.get(
        style, style_instructions["conversational"]
    )


def podcast_script_prompt(
    content: str, duration_minutes: int, source_count: int
) -> str:
    """Get the user prompt for podcast script generation.

    Args:
        content: The source content to create a podcast from
        duration_minutes: Target podcast duration
        source_count: Number of sources being processed

    Returns:
        User prompt string
    """
    # Estimate words based on typical speech rate (130-150 words per minute)
    target_words = duration_minutes * 140
    target_exchanges = duration_minutes * 8  # Roughly 8 exchanges per minute

    return f"""Transform the following content into an engaging podcast script.

TARGET LENGTH:
- Duration: ~{duration_minutes} minutes
- Approximate word count: {target_words} words
- Target number of dialogue exchanges: {target_exchanges}

CONTENT SOURCES: {source_count}

GUIDELINES:
1. Cover ALL key points from the content - don't skip important information
2. Make it engaging from the first line - hook the listener
3. Ensure natural transitions between topics
4. End with a clear conclusion or call-to-action
5. Each speaker should contribute meaningfully to the discussion

CONTENT TO TRANSFORM:
{content}

Generate the podcast script JSON now. Remember:
- Return ONLY valid JSON
- Use the exact speaker names provided in the system prompt
- Keep dialogue entries short (1-3 sentences each)
- Make it sound natural when read aloud"""
