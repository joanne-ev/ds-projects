import marimo

__generated_with = "0.23.6"
app = marimo.App(width="columns")


@app.cell(column=0)
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Data Cleaning & Pre-processing

    Data source: [Fixture Downloads](https://fixturedownload.com/results/wsl-2024)
    """)
    return


@app.cell
def _():
    # Packages
    import polars as pl
    import sys
    import csv
    from IPython.display import display

    return csv, display, pl, sys


@app.cell
def _(pl, sys):
    data_23 = pl.read_csv("data/wsl-2023-UTC.csv")
    data_24 = pl.read_csv("data/wsl-2024-UTC.csv")

    print(data_23.shape, data_24.shape, sep="\n")

    if data_23.columns != data_24.columns:
        sys.exit("Not matching")
    return data_23, data_24


@app.cell
def _(data_23, data_24, pl):
    # Insert the season year as a new column
    data_23_1 = data_23.clone().with_columns(pl.lit("23/24").alias("Season"))
    data_24_1 = data_24.clone().with_columns(pl.lit("24/25").alias("Season"))
    data = pl.concat([data_23_1, data_24_1])

    # Join the two dataframes on top of each other
    print(data.shape)
    data.head()
    return (data,)


@app.cell
def _(csv, data):
    # Team and their respective stadium
    home_stadium = (
        data.select(["Home Team", "Location"])
        .unique()
        .sort(by=["Home Team", "Location"])
        .rename({"Home Team": "Team", "Location": "Stadium"})
    )

    # Manually categorise each stadium by exporting the unique stadiums within the column

    import requests
    import time

    stadium = False

    if stadium:
        home_stadium.write_csv("data/team_stadiums.csv")

        with open("data/team_stadiums.csv") as f:
            rows = list(csv.DictReader(f))
        for _row in rows:
            query = f"{_row['Stadium']}"
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                },
                headers={"User-Agent": "StadiumGeocoder/1.0"},
            ).json()
            _row["latitude"] = resp[0]["lat"] if resp else ""
            _row["longitude"] = resp[0]["lon"] if resp else ""
            _row["region"] = (
                resp[0]["address"].get("state_district")
                or resp[0]["address"].get("city_district")
                if resp
                else ""
            )
            time.sleep(1.5)

        print("Creating CSV...")
        with open("data/team_stadium_locations.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    return


@app.cell
def _(pl):
    # Check if there are null values
    tsl = pl.read_csv("data/team_stadium_locations.csv")

    # Count the number of null values
    tsl_null_check = tsl.null_count().transpose().to_series().sum() > 0

    if tsl_null_check:
        print(tsl.filter(pl.any_horizontal(pl.all().is_null())))
        raise ValueError("null present")
    else:
        (
            pl.read_csv("data/team_stadium_locations.csv")
            .with_columns(
                pl.when(pl.col("region").str.contains("London"))
                .then(pl.lit("Greater London"))
                .when(pl.col("region").str.contains("Liverpool|Manchester"))
                .then(pl.lit("North West"))
                .otherwise(pl.col("region"))
                .alias("region")
            )
            .write_csv("data/team_stadium_locations.csv")
        )
    return


@app.cell
def _(csv, data):
    # Convert the csv of the stadiums and their geographical location into a dictionary where the stadium is the key and the location is the value
    with open("data/team_stadium_locations.csv", "r") as file:
        reader = csv.DictReader(file)
        stadium_region = {}
        stadium_longitude = {}
        stadium_latitude = {}
        for _row in reader:
            stadium_longitude[_row["Stadium"]] = _row["longitude"]
            stadium_latitude[_row["Stadium"]] = _row["latitude"]
            stadium_region[_row["Stadium"]] = _row["region"]
        if (
            len(stadium_region)
            != len(stadium_longitude)
            != len(stadium_latitude)
        ):
            print(
                "Incorrect",
                len(stadium_longitude),
                len(stadium_latitude),
                len(stadium_region),
                data["Location"].unique().shape[0],
                sep="\n",
            )
    return stadium_latitude, stadium_longitude, stadium_region


@app.cell
def _(data, pl, stadium_latitude, stadium_longitude, stadium_region):
    data_new = (
        data.clone()
        .with_columns(
            pl.col("Result").str.replace_all(" ", ""),  # Remove all whitespace
            pl.col("Date").str.to_datetime(
                "%d/%m/%Y %H:%M"
            ),  # Convert to DateTime data type
            pl.col("Location").alias("Stadium"),  # Rename the column
        )
        .with_columns(
            # Get results specific for home and away teams
            pl.col("Result")
            .str.split("-")
            .list.get(0)
            .cast(pl.Int8)
            .alias("Home Goals"),
            pl.col("Result")
            .str.split("-")
            .list.get(1)
            .cast(pl.Int8)
            .alias("Away Goals"),
            # Separate the date into individual variables
            pl.col("Date").dt.day().alias("Day"),
            pl.col("Date").dt.month().alias("Month"),
            pl.col("Date").dt.year().alias("Year"),
            pl.col("Date").dt.hour().alias("Hour"),
            # Identify Kickoff period based on the Date
            pl.when(pl.col("Date").dt.hour().le(13))  # <=12pm for morning
            .then(pl.lit("Morning"))
            .when(
                pl.col("Date").dt.hour().is_between(12, 18, closed="none")
            )  # 13 < time < 18 for afternoon
            .then(pl.lit("Afternoon"))
            .when(pl.col("Date").dt.hour().ge(18))  # >=18 for evening
            .then(pl.lit("Evening"))
            .alias("Kickoff"),
            # Identify geographical region of each stadium
            pl.col("Stadium").replace(stadium_region).alias("Region"),
            pl.col("Stadium").replace(stadium_longitude).alias("Longitude"),
            pl.col("Stadium").replace(stadium_latitude).alias("Latitude"),
        )
        .with_columns(
            # Calculate the goal difference
            (pl.col("Home Goals") - pl.col("Away Goals")).alias(
                "Goal Difference"
            ),
            # Calculate the number of goals scored
            (pl.col("Home Goals") + pl.col("Away Goals")).alias(
                "Goals Scored"
            ),
            # Determine the winners
            pl.when(pl.col("Home Goals").gt(pl.col("Away Goals")))
            .then(pl.lit("Home"))
            .when(pl.col("Away Goals").gt(pl.col("Home Goals")))
            .then(pl.lit("Away"))
            .otherwise(pl.lit("Draw"))
            .alias("Winner"),
        )
        .with_columns(
            # Identify winning teams
            pl.when(pl.col("Winner").eq("Away"))
            .then(pl.col("Away Team"))
            .when(pl.col("Winner").eq("Home"))
            .then(pl.col("Home Team"))
            .otherwise(pl.lit("Draw"))
            .alias("Winning Team"),
            # Identify losing teams
            pl.when(pl.col("Winner").eq("Away"))
            .then(pl.col("Home Team"))
            .when(pl.col("Winner").eq("Home"))
            .then(pl.col("Away Team"))
            .otherwise(pl.lit("Draw"))
            .alias("Losing Team"),
        )
        # Drop unnecessary columns
        .drop(["Location", "Date", "Result"])
        # Assign the right data type for a column - lower-precision variants are more memory-efficient
        .cast(
            {
                "Round Number": pl.UInt8,
                "Day": pl.UInt8,
                "Month": pl.UInt8,
                "Year": pl.UInt16,
                "Hour": pl.UInt8,
                "Longitude": pl.Decimal(scale=3),
                "Latitude": pl.Decimal(scale=3),
                "Home Goals": pl.UInt8,
                "Away Goals": pl.UInt8,
                "Goals Scored": pl.UInt8,
            }
        )
    )
    return (data_new,)


@app.cell
def _(data_new, pl):
    # Order categories within a categorical variable using Enum (i.e., ordered categorical data type)
    kickoff_enum = pl.Enum(
        ["Morning", "Afternoon", "Evening"]
    )

    # Reorder columns
    df = (
        data_new
        .clone()
        .select(
            [
                "Season",
                "Round Number",
                "Hour",
                "Day",
                "Month",
                "Year",
                "Kickoff",
                "Stadium",
                "Region",
                "Longitude",
                "Latitude",
                "Home Team",
                "Away Team",
                "Home Goals",
                "Away Goals",
                "Winner",
                "Winning Team",
                "Losing Team",
                "Goal Difference",
                "Goals Scored",
            ]
        )
        .cast({"Kickoff": kickoff_enum})
    )

    df.head()
    return (df,)


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # Data Visualisations
    """)
    return


@app.cell
def _():
    import polars.selectors as cs
    import plotly.express as px
    import plotly.graph_objects as go

    return cs, go, px


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Stadium Map
    """)
    return


@app.cell
def _():
    team_colours = {
        "Arsenal": "#db0007",
        "Aston Villa": "#95bfe5",
        "Brighton & Hove Albion": "#005daa",
        "Bristol City": "#E21A23",
        "Chelsea": "#6a7ab5",
        "Crystal Palace": "#d3d2d2",
        "Everton": "#0d00e9",
        "Leicester City": "#fdbe11",
        "Liverpool": "#CF1031",
        "Manchester City": "#6caddf",
        "Manchester United": "#da030e",
        "Tottenham Hotspur": "#020031",
        "West Ham United": "#7c2c3b",
    }
    return (team_colours,)


@app.cell
def _(df, pl, px, team_colours):
    stadium_count = (
        df["Stadium"]
        .value_counts()
        .sort(by="Stadium")
        .rename({"count": "Number of Matches"})
    )

    stadium_loc_df = (
        pl.read_csv("data/team_stadium_locations.csv")
        .join(stadium_count, on=["Stadium"], how="inner")
        .sort(by="Team")
    )

    _fig = px.scatter_map(
        data_frame=stadium_loc_df,
        lat="latitude",
        lon="longitude",
        color="Team",
        color_discrete_map=team_colours,
        hover_name="Stadium",
        hover_data={"latitude": False, "longitude": False},
        size="Number of Matches",
        zoom=5.5,
        center={"lat": 52, "lon": -1.5},  # Focus on England
        title="Stadium Map",
        subtitle="Map of the stadiums located in England sized by the number of total matches hosted in the stadium",
    )
    _fig.update_layout(autosize=False, width=800, height=800)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Goals Scored
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Region / Stadium
    """)
    return


@app.cell
def _(df, pl, px):
    # Bar chart comparing which region had the most goals scored
    region_goals = (
        df.clone()
        .group_by("Region")
        .agg(pl.col("Goals Scored").sum())
        .sort(by="Goals Scored", descending=True)
    )

    px.bar(
        data_frame=region_goals,
        x="Region",
        y="Goals Scored",
        title="Total Goals Scored by Region",
    )
    return


@app.cell
def _(df, pl, px):
    # Bar chart showing which stadium had the most goals scored
    stadium_goals = (
        df.clone()
        .group_by(["Stadium", "Region"])
        .agg(pl.col("Goals Scored").sum())
        .sort(by="Goals Scored", descending=True)
    )
    stadium_goals
    _fig = px.bar(
        data_frame=stadium_goals,
        y="Stadium",
        x="Goals Scored",
        color="Region",
        color_discrete_sequence=px.colors.qualitative.Dark24,
        title="Total Goals Scored by Stadium and Region",
    )

    _fig.update_layout(
        autosize=False,
        width=1200,
        height=700,
        yaxis={
            "categoryorder": "total ascending"
        },  # Orders the bars in ascending order (bottom up)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Kickoff
    """)
    return


@app.cell
def _(df, pl, px):
    # Bar chart showing which kickoff had the most goals scored
    kickoff_goals = (
        df.clone()
        .group_by("Kickoff")
        .agg(pl.col("Goals Scored").sum())
        .sort(by="Kickoff")
    )

    px.bar(
        data_frame=kickoff_goals,
        x="Kickoff",
        y="Goals Scored",
        title="Total Goals Scored by Kickoff",
    )
    return


@app.cell
def _(df, pl, px):
    # Number of games per kickoff
    kickoff_games = (
        df.clone()
        .select(pl.col("Kickoff").value_counts())
        .unnest("Kickoff")
        .sort(by="Kickoff")
    )

    _fig = px.bar(
        data_frame=kickoff_games,
        x="Kickoff",
        y="count",
        title="Total Games by Kickoff",
    )
    _fig.update_layout(autosize=False, width=600, height=600)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Home vs Away
    """)
    return


@app.cell
def _(cs, data_new_1, pl, px):
    home_away_goals = (
        data_new_1.clone()
        .select(pl.sum("Home Goals", "Away Goals"))
        .unpivot(
            on=cs.numeric(),
            variable_name="Home/Away",
            value_name="Goals Scored",
        )
    )

    _fig = px.bar(
        data_frame=home_away_goals,
        x="Home/Away",
        y="Goals Scored",
        title="Total Goals Scored Home and Away",
    )
    _fig.update_layout(autosize=False, width=600, height=600)
    return


@app.cell
def _(cs, df, pl, px):
    # Stacked bar chart of which team scored the most goals separated by home and away goals
    home_goals = (
        df.clone()
        .group_by("Home Team")
        .agg(pl.col("Home Goals").sum().alias("Home"))
        .sort(by="Home Team")
        .rename({"Home Team": "Team"})
    )

    away_goals = (
        df.clone()
        .group_by("Away Team")
        .agg(pl.col("Away Goals").sum().alias("Away"))
        .sort(by="Away Team")
        .rename({"Away Team": "Team"})
    )

    home_away_team_goals = (
        home_goals.join(away_goals, on=["Team"], how="inner")
        # Pivot long
        .unpivot(
            index="Team",
            on=cs.numeric(),
            variable_name="Home/Away",
            value_name="Goals Scored",
        )
    )

    _fig = px.bar(
        data_frame=home_away_team_goals,
        x="Team",
        y="Goals Scored",
        color="Home/Away",
        color_discrete_sequence=px.colors.qualitative.Bold,
        title="Total Goals Scored Home and Away by Team",
    )
    _fig.update_layout(autosize=False, width=1000, height=600)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Teams
    """)
    return


@app.cell
def _(df, pl):
    total_home_away_goals = (
        df.clone()
        .group_by("Home Team")
        .agg(pl.col("Home Goals", "Away Goals").sum())
        .with_columns(
            (pl.col("Home Goals") + pl.col("Away Goals")).alias("Total Goals"),
            pl.lit("Total").alias("Season"),
        )
        .rename({"Home Team": "Team"})
        .select("Season", "Team", "Home Goals", "Away Goals", "Total Goals")
    )

    season_goals = (
        df.clone()
        .group_by("Season", "Home Team")
        .agg(pl.col("Home Goals", "Away Goals").sum())
        .with_columns(
            (pl.col("Home Goals") + pl.col("Away Goals")).alias("Total Goals")
        )
        .sort(by="Season")
        .rename({"Home Team": "Team"})
    )

    season_total_goals = pl.concat([season_goals, total_home_away_goals])
    return (season_total_goals,)


@app.cell
def _(
    display,
    home_away_dropdown,
    pl,
    px,
    season_dropdown,
    season_total_goals,
):
    # Pie chart of goals scored segmented by teams and the season
    def team_goals_by_season(
        season: str = "23/24", home_away: str = "Total Goals"
    ):
        df1 = season_total_goals.filter(pl.col("Season").eq(f"{season}"))
        _fig = px.pie(
            df1,
            names="Team",
            values=f"{home_away}",
            title=f"Proportion of {home_away} Scored by Teams ({season})",
        )
        _fig.update_layout(autosize=False, width=750, height=500)
        return _fig


    try:
        display(
            team_goals_by_season(
                season=season_dropdown.value,
                home_away=home_away_dropdown.value,
            )
        )
    except ValueError:
        print(
            "Please select season and the type of goals using the dropdowns below"
        )
    return


@app.cell
def _(df, display, mo):
    season_dropdown = mo.ui.dropdown(
        options=df["Season"].unique().sort(descending=True).to_list(),
        label="Choose a season",
        value=df["Season"].unique().sort(descending=True).to_list()[0],
        searchable=False,
    )

    home_away_dropdown = mo.ui.dropdown(
        options=["Home Goals", "Away Goals", "Total Goals"],
        label="Choose goals scored",
        value="Home Goals",
        searchable=False,
    )

    display(season_dropdown, home_away_dropdown)
    return home_away_dropdown, season_dropdown


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Time-Series
    """)
    return


@app.cell
def _(df, pl, px):
    # Time series of goals scored compared between each season and the over all seasons
    df_season_goals = (
        df.clone()
        .group_by("Season", "Round Number")
        .agg(pl.col("Goals Scored").sum())
        .sort(by="Round Number")
    )

    df_total_goals = (
        df.clone()
        .group_by("Round Number")
        .agg(pl.col("Goals Scored").sum())
        .sort(by="Round Number")
        .with_columns(pl.lit("Total").alias("Season"))
        .select("Season", "Round Number", "Goals Scored")
    )

    df_goals = pl.concat([df_season_goals, df_total_goals])

    _fig = px.line(
        df_goals,
        x="Round Number",
        y="Goals Scored",
        color="Season",
        color_discrete_sequence=px.colors.qualitative.G10,
    )
    _fig.update_layout(
        autosize=False,
        width=1300,
        height=600,
        title="Time-series of Goals Score by Round Number",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1),
    )
    return


@app.cell
def _(df, pl, px, team_dropdown):
    # Time series of the number of goals each team has scored over the season
    def track_team_goals(team: str = "Arsenal"):
        team_season_goals = (
            df.clone()
            .filter(
                (pl.col("Home Team") == f"{team}")
                | (pl.col("Away Team") == f"{team}")
            )
            .with_columns(
                pl.when(pl.col("Home Team") == f"{team}")
                .then(pl.col("Home Goals"))
                .when(pl.col("Away Team") == f"{team}")
                .then(pl.col("Away Goals"))
                .alias("Goal Tracking")
            )
            .select("Season", "Round Number", "Goal Tracking")
        )

        total_team_season_goals = (
            team_season_goals.clone()
            .group_by("Round Number")
            .agg(pl.col("Goal Tracking").sum())
            .sort(by="Round Number")
            .with_columns(pl.lit("Total").alias("Season"))
            .select("Season", "Round Number", "Goal Tracking")
            .cast({"Goal Tracking": pl.UInt8})
        )

        team_season_goals_df = pl.concat(
            [team_season_goals, total_team_season_goals]
        )

        _fig = px.line(
            team_season_goals_df,
            x="Round Number",
            y="Goal Tracking",
            color="Season",
            title=f"Goals Scored by {team} per Round",
        )

        if team is None:
            return "Please select a Team using the dropdown below"
        else:
            return _fig.update_layout(
                autosize=False,
                width=1300,
                height=600,
                xaxis=dict(tick0=1, dtick=1),
            )


    track_team_goals(team=team_dropdown.value)
    return


@app.cell
def _(df, mo):
    team_dropdown = mo.ui.dropdown(
        options=df["Home Team"].unique().sort().to_list(),
        label="Select a team",
        # value='Arsenal',
        searchable=True,
    )

    team_dropdown
    return (team_dropdown,)


@app.cell
def _(df, go, pl, season_dropdown2):
    # Bar chart showing most goals scored by a single team at each round for each season
    import warnings

    warnings.filterwarnings(
        "ignore", message="Comparisons with None always result in null"
    )


    def team_most_goals_per_round_season(season: str = "23/24"):
        df1 = (
            df.clone()
            .group_by("Season", "Round Number")
            .agg(pl.all().sort_by("Goals Scored").last())
            .sort(by="Round Number")
            .select("Season", "Round Number", "Winning Team", "Goals Scored")
            .filter(pl.col("Season").eq(season))
        )

        _fig = go.Figure()
        _fig.add_bar(
            x=df1["Round Number"].to_list(),
            y=df1["Goals Scored"].to_list(),
            text=df1["Winning Team"].to_list(),
            textposition="inside",
            textangle=-90,
            insidetextanchor="middle",
            textfont_size=12,
        )

        if season is None:
            return "Please select a season using the dropdown below"
        else:
            return _fig.update_layout(
                title=f"Most Goals Scored in Each Round for the {season} Season",
                xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            )


    team_most_goals_per_round_season(season=season_dropdown2.value)
    return


@app.cell
def _(df, display, mo):
    season_dropdown2 = mo.ui.dropdown(
        options=df["Season"].unique().to_list(),
        label="Choose a season",
        # value=df['Season'].unique().sort(descending=True).to_list()[0],
        searchable=False,
    )

    display(
        season_dropdown2,
    )
    return (season_dropdown2,)


@app.cell
def _(df, pl, px):
    # Source - https://stackoverflow.com/a/72019719
    most_goals_per_round_season = (
        df.clone()
        .group_by("Season", "Round Number")
        .agg(pl.all().sort_by("Goals Scored").last())
        .sort(by="Round Number")
        .select("Season", "Round Number", "Goals Scored")
    )

    most_goals_per_round_total = (
        most_goals_per_round_season.clone()
        .group_by("Round Number")
        .agg(pl.col("Goals Scored").sum())
        .with_columns(pl.lit("Total").alias("Season"))
        .select("Season", "Round Number", "Goals Scored")
        .cast({"Goals Scored": pl.UInt8})
    )

    most_goals_per_round = pl.concat(
        [most_goals_per_round_season, most_goals_per_round_total]
    ).sort(by="Round Number")

    _fig = px.line(
        data_frame=most_goals_per_round,
        x="Round Number",
        y="Goals Scored",
        color="Season",
        title="Most Goals Scored per Round",
    )
    _fig.update_layout(xaxis=dict(tickmode="linear", tick0=1, dtick=1))
    return


if __name__ == "__main__":
    app.run()
