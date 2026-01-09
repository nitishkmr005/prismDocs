#!/usr/bin/env python3
"""Test the content-aware image generation concept extraction."""

import sys
import os

# Set up path
sys.path.insert(0, "src")
os.chdir("/Users/nitishkumarharsoor/Documents/1.Learnings/1.Projects/4.Experiments/7.document-generator")

# Direct imports to avoid dependency chain
import json
import re
from loguru import logger

# Load settings first
from doc_generator.infrastructure.settings import get_settings

# Import prompts
from doc_generator.config.prompts.image_prompts import (
    CONCEPT_EXTRACTION_PROMPT,
    CONCEPT_EXTRACTION_SYSTEM_PROMPT,
    CONTENT_AWARE_IMAGE_PROMPT,
    IMAGE_STYLE_TEMPLATES,
)

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Sample content from the Transformers lecture
SAMPLE_SECTIONS = [
    {
        "title": "Position Embeddings",
        "content": """So if you remember, here we're letting tokens interact with all other tokens in a direct fashion. 
        So they have direct links. But contrary to things like RNNs, where you have a sequential dependency where 
        you process each token one at a time, here you're basically losing this idea of a token being processed 
        before another one. So you lose this position information. So as a result of that, we need to somehow 
        quantify tokens at each position and try to inject that information when the transformer is processing the inputs.
        
        The original transformer paper authors chose to have a dedicated embedding for each position. Position 1 has 
        one embedding, position 2 has one embedding, etc. And what they chose to do is to add that embedding to the 
        input-token embedding.
        
        The second method uses sinusoidal embeddings with sine and cosine functions. The formula is basically 
        sine of something times m for even dimensions and cosine for odd dimensions. This allows the model to 
        learn relative positions because the dot product of position embeddings depends only on the relative distance.
        
        Modern models use RoPE (Rotary Position Embeddings) which rotates the query and key vectors by an angle 
        that depends on position. The rotation matrix uses cosine and sine of theta times m."""
    },
    {
        "title": "Self-Attention Mechanism",
        "content": """The self-attention mechanism can be expressed with this formula: softmax of query times key 
        transpose over square root of dk times v. So I hope this formula is familiar for you. This formula is 
        highly optimized. These are big matrix multiplications that hardware is very capable of doing.
        
        The idea is that the query is going to ask which other tokens are most similar to itself by comparing 
        query and key. And then once that's done, basically we will be taking the associated value.
        
        You have these notations of queries, keys, and values. Each token is attending to all other tokens 
        in the sequence through this mechanism of attention. The attention weights are computed using dot product 
        of queries and keys, normalized by softmax."""
    },
    {
        "title": "Multi-Head Attention Variants",
        "content": """There are some variations as to how many projection matrices to share. You have the extreme 
        example where all h heads share the same projection matrices for V and K - this is called MQA (Multi-Query 
        Attention).
        
        You have the in-between case called GQA (Grouped Query Attention) where you share g projection matrices 
        for V and K, and then you have groups of size h over g.
        
        And then you have the standard Multi-Head Attention (MHA) where every head has its own query projection, 
        key projection, and value projection matrices.
        
        The reason for sharing K and V projections is related to the KV cache - every time you decode something, 
        you need to attend to all other tokens, so the keys and values come up a lot. Sharing projection matrices 
        allows you to save memory."""
    }
]


class SimpleConceptExtractor:
    """Simplified concept extractor for testing."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.settings = get_settings()

        if self.api_key and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.debug("Concept extractor initialized with Claude")

    def is_available(self) -> bool:
        return self.client is not None

    def extract(self, section_title: str, content: str) -> dict:
        if not self.is_available():
            logger.debug("Concept extractor not available, using keyword extraction")
            return self._keyword_extraction(section_title, content)

        content_preview = content[:3000] if len(content) > 3000 else content

        prompt = CONCEPT_EXTRACTION_PROMPT.format(
            section_title=section_title,
            content=content_preview
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[
                    {"role": "user", "content": f"{CONCEPT_EXTRACTION_SYSTEM_PROMPT}\n\n{prompt}"}
                ]
            )

            response_text = response.content[0].text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)

            logger.debug(f"Extracted concepts for '{section_title}': {result.get('recommended_style', 'unknown')}")
            return result

        except Exception as e:
            logger.error(f"Concept extraction failed for '{section_title}': {e}")
            return self._keyword_extraction(section_title, content)

    def _keyword_extraction(self, section_title: str, content: str) -> dict:
        content_lower = content.lower()
        
        patterns = {
            "architecture": ["transformer", "encoder", "decoder", "layer", "block", "architecture"],
            "attention": ["attention", "query", "key", "value", "softmax", "multi-head", "self-attention"],
            "position": ["position", "embedding", "sinusoidal", "rope", "rotary"],
            "normalization": ["normalization", "layernorm", "rmsnorm", "normalize"],
            "comparison": ["vs", "versus", "compare", "comparison", "different"],
            "process": ["step", "process", "flow", "pipeline", "sequence"]
        }

        detected_patterns = []
        for pattern_name, keywords in patterns.items():
            matches = sum(1 for kw in keywords if kw in content_lower)
            if matches >= 2:
                detected_patterns.append((pattern_name, matches))

        detected_patterns.sort(key=lambda x: x[1], reverse=True)
        
        if detected_patterns:
            primary_type = detected_patterns[0][0]
        else:
            primary_type = "concept"

        key_terms = []
        all_keywords = [kw for kws in patterns.values() for kw in kws]
        for kw in all_keywords:
            if kw in content_lower and kw not in key_terms:
                key_terms.append(kw)
                if len(key_terms) >= 8:
                    break

        style_map = {
            "architecture": "architecture_diagram",
            "attention": "technical_infographic",
            "position": "comparison_chart",
            "normalization": "technical_infographic",
            "comparison": "comparison_chart",
            "process": "process_flow",
            "concept": "handwritten_notes"
        }

        return {
            "primary_concept": {
                "type": primary_type,
                "title": section_title,
                "elements": key_terms[:5],
                "relationships": [],
                "details": f"Key concepts from {section_title}"
            },
            "secondary_concepts": [],
            "recommended_style": style_map.get(primary_type, "technical_infographic"),
            "key_terms": key_terms
        }

    def generate_content_aware_prompt(self, concepts: dict) -> str:
        primary = concepts.get("primary_concept", {})
        style = concepts.get("recommended_style", "technical_infographic")
        key_terms = concepts.get("key_terms", [])

        style_requirements = IMAGE_STYLE_TEMPLATES.get(
            style,
            IMAGE_STYLE_TEMPLATES.get("technical_infographic", "")
        )

        elements = primary.get("elements", [])
        elements_str = "\n".join(f"- {elem}" for elem in elements) if elements else "- Main concept visualization"

        relationships = primary.get("relationships", [])
        relationships_str = "\n".join(f"- {rel}" for rel in relationships) if relationships else "- Show how concepts connect"

        details = primary.get("details", "")
        key_terms_str = ", ".join(key_terms) if key_terms else "key concepts"

        prompt = CONTENT_AWARE_IMAGE_PROMPT.format(
            style=style.replace("_", " "),
            title=primary.get("title", "Concept Visualization"),
            elements=elements_str,
            relationships=relationships_str,
            details=details,
            key_terms=key_terms_str,
            style_requirements=style_requirements
        )

        return prompt


def test_concept_extraction():
    """Test the ConceptExtractor on sample sections."""
    print("=" * 80)
    print("TESTING CONTENT-AWARE IMAGE GENERATION")
    print("=" * 80)
    
    extractor = SimpleConceptExtractor()
    
    print(f"\nConcept Extractor available (LLM): {extractor.is_available()}")
    print("\n" + "-" * 80)
    
    for section in SAMPLE_SECTIONS:
        title = section["title"]
        content = section["content"]
        
        print(f"\n📄 SECTION: {title}")
        print("-" * 40)
        
        # Test concept extraction
        concepts = extractor.extract(title, content)
        
        print(f"\n📊 Extracted Concepts:")
        primary = concepts.get("primary_concept", {})
        print(f"   Type: {primary.get('type', 'unknown')}")
        print(f"   Elements: {primary.get('elements', [])}")
        if primary.get('relationships'):
            print(f"   Relationships: {primary.get('relationships', [])[:3]}")
        print(f"   Recommended Style: {concepts.get('recommended_style', 'unknown')}")
        print(f"   Key Terms: {concepts.get('key_terms', [])[:8]}")
        
        # Generate content-aware prompt
        prompt = extractor.generate_content_aware_prompt(concepts)
        
        print(f"\n📝 Generated Image Prompt (first 600 chars):")
        print("-" * 40)
        print(prompt[:600] + "..." if len(prompt) > 600 else prompt)
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    test_concept_extraction()
