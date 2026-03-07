"""LangChain integration example for llm-output-guard.

Prerequisites:
    pip install llm-output-guard langchain-openai
"""

from pydantic import BaseModel

# llm-output-guard integration
from llm_output_guard.integrations.langchain import GuardedLLM, GuardOutputParser


class MovieReview(BaseModel):
    title: str
    rating: float
    pros: list[str]
    cons: list[str]
    verdict: str


# ---------------------------------------------------------------------------
# Option A: GuardedLLM wrapper
# ---------------------------------------------------------------------------

def example_guarded_llm():
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        print("langchain-openai not installed; skipping GuardedLLM example.")
        return

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    guarded = GuardedLLM(
        llm=llm,
        schema=MovieReview,
        max_retries=3,
        raise_on_failure=True,
    )

    result = guarded.invoke(
        "Review the movie 'Dune: Part Two' (2024). Return JSON only."
    )
    review: MovieReview = result.data
    print(f"Title  : {review.title}")
    print(f"Rating : {review.rating}/10")
    print(f"Verdict: {review.verdict}")


# ---------------------------------------------------------------------------
# Option B: GuardOutputParser in an LCEL chain
# ---------------------------------------------------------------------------

def example_output_parser():
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
        print("langchain-openai not installed; skipping OutputParser example.")
        return

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a film critic. Always respond in JSON."),
        ("human", "{question}"),
    ])
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    parser = GuardOutputParser(schema=MovieReview)

    chain = prompt | llm | parser
    review = chain.invoke({"question": "Review Oppenheimer (2023)."})
    print(review)


if __name__ == "__main__":
    example_guarded_llm()
