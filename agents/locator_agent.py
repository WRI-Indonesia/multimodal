from typing import List
from langchain.agents import Tool
from langchain.agents import initialize_agent  # type: ignore
from langchain.agents.agent import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI
from app.spatial_query import query_districts_by_geometry
from app.models import DistrictOverlap
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4", temperature=0)


def locate_district(geom_wkt: str) -> str:
    results: List[DistrictOverlap] = query_districts_by_geometry(geom_wkt)
    if not results:
        return "No overlapping districts found."

    msg = "The given polygon intersects with the districts of "
    parts = [
        f"{d.district} in {d.province} ({d.pct_overlap:.2f}% overlap)" for d in results
    ]
    msg += ", ".join(parts) + "."
    return msg


tools = [
    Tool(
        name="LocateDistrict",
        func=locate_district,
        description="Given a geometry WKT, returns a list of intersecting Indonesian districts with overlap percentages.",
    )
]

agent: AgentExecutor = initialize_agent(
    tools=tools, llm=llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True
)
