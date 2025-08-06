from langchain.agents import Tool, initialize_agent  # type: ignore
from langchain.agents.agent import AgentExecutor
from langchain_openai import ChatOpenAI
from app.database import get_connection
from langchain.agents.agent_types import AgentType


llm = ChatOpenAI(model="gpt-4", temperature=0)


def summarize_district(name: str) -> str:
    """Fetch district metadata from DB and return a summary."""
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT name, province, population, male_ratio, female_ratio
    FROM districts
    WHERE LOWER(name) = LOWER(%s)
    LIMIT 1;
    """
    cur.execute(query, (name,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return f"No data found for district '{name}'."

    name, province, population, male_ratio, female_ratio = row
    male_percent = round(male_ratio * 100, 1)
    female_percent = round(female_ratio * 100, 1)

    return (
        f"{name} is a district in {province} with an estimated population of {population:,}. "
        f"Gender distribution is approximately {male_percent}% male and {female_percent}% female."
    )


# Optional: if you want it agentized
summarizer_tool = Tool(
    name="SummarizeDistrict",
    func=summarize_district,
    description="Return summary for a district including population and gender",
)

summary_agent: AgentExecutor = initialize_agent(
    tools=[summarizer_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)
