# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

import streamlit as st
import geopandas as gpd
import json
from typing import List
from shapely.geometry import Point
from pydeck import Deck, Layer, ViewState
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from app.geo_utils import read_uploaded_file
from app.spatial_query import query_districts_by_geometry
from app.models import DistrictOverlap
from app.database import get_connection
from dotenv import load_dotenv

load_dotenv()

# Initialize chat history
msgs = StreamlitChatMessageHistory()
st.set_page_config(layout="centered", page_title="🧠 District Locator Agent")
st.title("🧠 District Locator Agent")

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)


def locate_district(geom_wkt: str) -> List[DistrictOverlap]:
    """Return structured district overlap data"""
    return query_districts_by_geometry(geom_wkt)


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


def show_polygon_map(gdf: gpd.GeoDataFrame) -> None:
    """Visualize the uploaded geometry"""
    geojson_str = gdf.to_json()
    geojson = json.loads(geojson_str)

    geojson_layer = Layer(
        "GeoJsonLayer",
        data=geojson,
        get_fill_color="[180, 0, 200, 140]",
        pickable=True,
        stroked=True,
    )

    centroid = gdf.geometry.iloc[0].centroid
    view_state = ViewState(latitude=centroid.y, longitude=centroid.x, zoom=10, pitch=0)

    st.pydeck_chart(Deck(layers=[geojson_layer], initial_view_state=view_state))


# Define tools for the agent
tools = [
    Tool(
        name="LocateDistrict",
        func=locate_district,
        description="Given a geometry WKT, returns structured data about intersecting Indonesian districts.",
    ),
    Tool(
        name="SummarizeDistrict",
        func=summarize_district,
        description="Returns demographic summary for a specific district.",
    ),
    Tool(
        name="ShowMap",
        func=show_polygon_map,
        description="Visualizes a GeoDataFrame on a map.",
    ),
]

# Initialize the main agent
agent: AgentExecutor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    handle_parsing_errors=True,
)


def process_uploaded_file(uploaded_file) -> gpd.GeoDataFrame:
    """Process uploaded file and return GeoDataFrame"""
    try:
        return read_uploaded_file(uploaded_file)
    except Exception as e:
        raise RuntimeError(f"File processing failed: {str(e)}")


# Main interface
uploaded_file = st.file_uploader(
    "Upload GeoJSON or zipped Shapefile (.shp.zip)",
    type=["geojson", "json", "zip"],
    key="file_uploader",
)

if uploaded_file:
    try:
        gdf = process_uploaded_file(uploaded_file)
        st.success(f"File loaded with {len(gdf)} feature(s).")

        # Store geometry in session state
        st.session_state["current_geometry"] = gdf.geometry.iloc[0].wkt

        if st.checkbox("🔍 Show map preview"):
            show_polygon_map(gdf)

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# Update your chat interaction section to:


def display_chat():
    """Display chat history in correct order (newest at bottom)"""
    # Display all messages in chronological order
    for msg in msgs.messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.write(msg.content)
        else:
            with st.chat_message("assistant"):
                st.write(msg.content)


# Main chat interaction
if prompt := st.chat_input("Ask about districts"):
    # Add user message to history FIRST
    msgs.add_user_message(prompt)

    # Display all messages (including the new one)
    display_chat()

    # Then process and show agent response
    geometry_wkt = st.session_state.get("current_geometry", None)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            if geometry_wkt:
                response = agent.run(
                    {
                        "input": f"{prompt}\n\nGeometry WKT: {geometry_wkt}",
                        "file_name": st.session_state.get("uploaded_file_name", ""),
                    }
                )
            else:
                response = agent.run({"input": prompt})

        st.write(response)

    # Add AI response to history
    msgs.add_ai_message(response)
