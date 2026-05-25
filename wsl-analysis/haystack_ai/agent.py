import os
from dotenv import load_dotenv
from haystack.components.agents import Agent
from haystack_integrations.components.generators.ollama import OllamaChatGenerator
from haystack.dataclasses import ChatMessage
from haystack_ai.tools import search_tool, create_stadium_location_csv_tool

load_dotenv()

def stadium_location_agent(
    count: int,
    stadium_file: str = "team_stadiums.txt",
    model: str = "qwen2.5:7b",
    location_file: str = "team_stadium_loc.csv"
):

    # Read the stadium file in Python
    with open(stadium_file, 'r') as f:
        lines = f.read().strip().splitlines()

    stadiums = [line.split(',') for line in lines[1:] if ',' in line]

    chat_generator = OllamaChatGenerator(model=model, url="http://localhost:11434", generation_kwargs={"temperature": 0})

    for team, stadium in stadiums:
        team = team.strip()
        stadium = stadium.strip()
        print(f"[INFO] Processing: {team} | {stadium}")

        agent = Agent(
            chat_generator=chat_generator,
            tools=[search_tool, create_stadium_location_csv_tool],
            max_agent_steps=3,  # One for each tool
            system_prompt=f"""
            You are a tool-calling agent. You have two tools: search_tool and create_stadium_location_csv.
            Rules:
            - Only call tools. Never write code or explanations.
            - Call search_tool first, then create_stadium_location_csv. Two calls total.
            - Never call create_stadium_location_csv more than once per stadium.
            - Use the stadium name exactly as given. Do not rename it.
            - If any value is missing use "NOT FOUND" for strings and 0.0 for numbers.
            
            Example:
              Call search_tool(query="Arsenal Meadow Park WSL stadium England latitude longitude region")
              Call create_stadium_location_csv(filename="{location_file}", team="Arsenal", stadium="Meadow Park", region="London", latitude=51.41, longitude=-0.45)
            """
        )

        response = agent.run(
            messages=[ChatMessage.from_user(
                f'Step 1: Call search_tool with query="{team} {stadium} WSL stadium England latitude longitude region". '
                f'Step 2: From the search result extract region, latitude, longitude, then call create_stadium_location_csv('
                f'filename="{location_file}", team="{team}", stadium="{stadium}", region=<extracted>, latitude=<extracted>, longitude=<extracted>). '
                f'Do not pass query to create_stadium_location_csv.'
            )]
        )

        messages = response.get("messages", [])
        last = messages[-1] if messages else None
        if last and last.text:
            print(f"[INFO] {last.text[:100]}")

    # Verify final count
    if os.path.exists(location_file):
        with open(location_file, 'r') as f:
            row_count = sum(1 for line in f) - 1  # exclude header
        print(f"\n[RESULT] {row_count}/{count} stadiums written to {location_file}")
    else:
        print("[ERROR] CSV file was not created.")