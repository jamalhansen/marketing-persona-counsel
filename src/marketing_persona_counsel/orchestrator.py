import asyncio
from typing import Any
from pydantic_ai import Agent
from .models import PersonaEvaluation, CouncilResult
from local_first_common.personas import ObsidianPersona


async def evaluate_post(
    persona: ObsidianPersona,
    content: str,
    model: Any,
) -> PersonaEvaluation:
    """Run a single persona's evaluation of the content."""
    
    agent = Agent(
        model,
        output_type=PersonaEvaluation,
        system_prompt=(
            f"{persona.system_prompt}\n\n"
            "You are a member of a marketing evaluation council. "
            "Your task is to review the provided blog post or article and give your honest feedback "
            "based on your persona's unique lens and biases. "
            "Be critical but constructive. Score 1-10 on the requested metrics."
        ),
    )
    
    result = await agent.run(content)
    # Ensure the persona name is correctly set in the result
    evaluation = result.output
    evaluation.persona_name = persona.name
    return evaluation


async def run_council(
    personas: list[ObsidianPersona],
    content: str,
    title: str,
    location: str,
    model: Any,
    concurrency: int = 3,
) -> CouncilResult:
    """Run all personas in parallel (with concurrency limit)."""
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def wrapped_eval(p: ObsidianPersona):
        async with semaphore:
            return await evaluate_post(p, content, model)
            
    tasks = [wrapped_eval(p) for p in personas]
    evaluations = await asyncio.gather(*tasks)
    
    return CouncilResult(
        source_title=title,
        source_location=location,
        evaluations=list(evaluations),
    )
