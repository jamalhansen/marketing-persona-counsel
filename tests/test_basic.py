from local_first_common.personas import load_obsidian_persona
from marketing_persona_counsel.ingestion import load_markdown_content
from marketing_persona_counsel.models import PersonaEvaluation


def test_persona_parsing(tmp_path):
    persona_file = tmp_path / "Test Persona.md"
    persona_file.write_text("""# Test Persona
**Archetype:** The Researcher

## Lens
Sees the world through data.

## System Prompt Seed
> You are a meticulous researcher.
""", encoding="utf-8")
    
    persona = load_obsidian_persona(persona_file)
    assert persona.name == "Test Persona"
    assert persona.archetype == "The Researcher"
    assert "meticulous researcher" in persona.system_prompt


def test_markdown_ingestion(tmp_path):
    post_file = tmp_path / "post.md"
    post_file.write_text("""---
title: My Cool Post
---
This is the content.
""", encoding="utf-8")
    
    title, content = load_markdown_content(post_file)
    assert title == "My Cool Post"
    assert content.strip() == "This is the content."


def test_persona_evaluation_model():
    ev = PersonaEvaluation(
        persona_name="Patty",
        sentiment="Happy",
        interest_score=8,
        engagement_score=7,
        friendliness_score=9,
        shareability_score=5,
        outstanding_questions=["Why?"],
        tips_to_improve=["More code"],
        narrative="Good stuff."
    )
    assert ev.persona_name == "Patty"
    assert ev.interest_score == 8
