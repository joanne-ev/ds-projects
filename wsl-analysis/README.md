# ⚽ Predicting Game Results in the Women's Super League (WSL)

## How to use this repository

[Marimo notebooks](https://marimo.io/) were used in favour of Jupyter Notebooks. Marimo notebooks are Git-friendly reproducible Python scripts (`.py`) that can be edited as a notebook as shared as an app. A core feature of Marimo is its reactivity - *"run one cell and marimo reacts by running affected cells"*. Marimo also provides built-in [interactive elements](https://docs.marimo.io/guides/interactivity/) like dropdowns allowing for more user-engaged reading.

### To run this notebook

1. [Download the `data` folder](https://downgit.github.io/#/home?url=https://github.com/joanne-ev/ds-projects/tree/wsl-analysis/wsl-analysis/data)
2. [Open `notebook.py` in molab](https://molab.marimo.io/github/joanne-ev/ds-projects/blob/wsl-analysis/wsl-analysis/notebook.py)
3. In molab, save a copy of this notebook
4. In your molab session upload the `data` folder
5. Run the notebook!
6. Toggle app model on the bottom right to see the notebook as the outputs without the code cells

## Background

The Women's Super League (WSL) is the top division league for professional women's football in England. It is widely regarded as one of the most popular and competitive league in women's football, attracting elite talent from across the globe. This project analyses the WSL through various visualisations of goals scored segmented by teams and regions alongside match-specific facets like kickoff timings. This project will also look at smaller research questions I was interested in knowing with the ultimate goal of developing a deep learning model to predict the next season's winner.

## Research Question

1. Who are the *Big Six* of the WSL?
2. Does kickoff time mean fewer goals scored?

### Who are the *Big Six* of the WSL?

**Background:** The *Big Six* is a term used to describe the six wealthiest clubs in the Premier League (i.e., top division league for professional men's football in England) that historically dominate the league standings and possess the largest global fanbases. The Big Six include: Arsenal, Chelsea, Liverpool, Manchester City, Manchester United and Tottenham Hotspur.

**Problem:** The Big Six teams are commonly attributed to the men's teams in the Premier League. This Big Six was not officially established for women's teams in the WSL. Currently, the WSL's equivalent of the Big Six mirrors that of the men, but it is unclear whether this is true. Moreover, as time has gone on, the Big Six in the Premier League is being questioned with teams like Tottenham Hotspur struggling against relegation (25/26) and others like Manchester United (24/25) and Chelsea (25/26) not finishing in the top six. As well, the WSL is a smaller league than the Premier League with only 12 teams playing per season with plans to grow to 14 teams in the 26/27 season. Therefore, it would be more suitable for the WSL to have a Big Four rather than a Big Six, in keeping with the Premier League's 30% ratio.

**Purpose:** This research looks to determine the current *Big Four* of the WSL based on data from previous seasons.

**Analysis:** The WSL's Big Four will be determined by 
1. Ratio of games won to games lost
1. Ratio of goals scored to goals conceeded
1. Consistency throughout seasons
