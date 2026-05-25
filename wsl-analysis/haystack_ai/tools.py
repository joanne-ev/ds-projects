from haystack.tools import ComponentTool
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import Tool
import csv
import os
from dotenv import load_dotenv

load_dotenv()

# Tool for web search
search_tool = ComponentTool(
    component=SerperDevWebSearch(),
    name="search_tool",
    description="Searches the web for information. Always call this BEFORE create_stadium_location_csv to find coordinates."
)



# Append geographical information about the Stadium, including its Region, Longitude and Latitude to a CSV file
def create_stadium_location_csv(filename: str, team: str, stadium: str, region: str, longitude: float, latitude: float) -> str:
    """
    Write a stadium's geographical location to the CSV file named `stadium_location.csv`.
    :param filename: The name of the CSV file to write the stadium's geographical location on.
    :param team: The name of the football team.
    :param stadium: The name of the stadium.
    :param region: The geographical region in England where the stadium is located.
    :param longitude: The longitude coordinate of the stadium.
    :param latitude: The latitude coordinate of the stadium.
    """
    print(f"[DEBUG] create_stadium_location_csv called: {team} | {stadium} | {region} | {longitude} | {latitude}")

    try:
        filepath = f"{filename}"
        file_exists = os.path.exists(filepath)

        # Check for duplicate before writing
        if file_exists:
            with open(filepath, 'r') as f:
                existing = f.read()
            if f"{team},{stadium}" in existing:
                return f"SKIPPED: {team} - {stadium} already exists in {filename}."

        # Write searched information into the CSV
        with open(filepath, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=["Team", "Stadium", "Region", "Longitude", "Latitude"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                'Team': team,
                'Stadium': stadium,
                'Region': region,
                'Longitude': float(longitude),  # explicit cast in case model passes a string
                'Latitude': float(latitude)
            })

        return f"SUCCESS: Saved {team} - {stadium} to {filename}."
    except Exception as e:
        return f"ERROR writing {team} - {stadium}: {str(e)}"


create_stadium_location_csv_tool = Tool(
    name="create_stadium_location_csv",
    description="Writes a stadium's location data to CSV. Only call this AFTER calling search_tool. Never pass a query parameter to this tool.",
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "The name of the CSV file to append the stadium's geographical location."},
            "team": {"type": "string", "description": "The name of the football team."},
            "stadium": {"type": "string", "description": "Name of the stadium."},
            "region": {
                "type": "string",
                "description": "Region in England where the stadium is located.",
                # Force the AI to select from one of these regions
                "enum": ["North East", "North West", "Yorkshire and the Humber", "East Midlands", "West Midlands", "East of England", "London", "South East", "South West"],
            },
            "longitude": {"type": "number", "description": "Longitude coordinate of the stadium."},
            "latitude": {"type": "number", "description": "Latitude coordinate of the stadium."},
        },
        "required": ["filename", "team", "stadium", "region", "longitude", "latitude"]
    },
    function=create_stadium_location_csv
)