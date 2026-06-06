import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Who are the *Big Four* of the WSL?

    **Background:** The *Big Six* is a term used to describe the six wealthiest clubs in the Premier League (i.e., top division league for professional men's football in England) that historically dominate the league standings and possess the largest global fanbases. The Big Six include: Arsenal, Chelsea, Liverpool, Manchester City, Manchester United and Tottenham Hotspur.

    **Problem:** The Big Six teams are commonly attributed to the men's teams in the Premier League. This Big Six was not officially established for women's teams in the WSL. Currently, the WSL's equivalent of the Big Six mirrors that of the men, but it is unclear whether this is true. Moreover, as time has gone on, the Big Six in the Premier League is being questioned with teams like Tottenham Hotspur struggling against relegation (25/26) and others like Manchester United (24/25) and Chelsea (25/26) not finishing in the top six. As well, the WSL is a smaller league than the Premier League with only 12 teams playing per season with plans to grow to 14 teams in the 26/27 season. Therefore, it would be more suitable for the WSL to have a Big Four rather than a Big Six, in keeping with the Premier League's 30% ratio.

    **Purpose:** This research looks to determine the current *Big Four* of the WSL based on data from previous seasons.

    **Analysis:** The WSL's Big Four will be determined by

    1. Ratio of games won to games lost
    2. Ratio of goals scored to goals conceeded -> Goal Difference
    3. Consistency throughout seasons
    """)
    return


@app.cell
def _():
    import polars as pl
    import seaborn as sns
    import matplotlib.pyplot as plt

    return pl, plt, sns


@app.cell
def _(pl):
    data = pl.read_csv("data/wsl_data.csv")

    data.head()
    return (data,)


@app.cell
def _(data, pl):
    def group_by_agg_count(grp_by: str, alias: str):
        df = (
            data.clone()
            .group_by(grp_by)
            .agg(pl.len().alias(alias))
            .sort(by=alias, descending=True)
            .rename({grp_by: 'Team'})
        )

        return df

    return (group_by_agg_count,)


@app.cell
def _(data, group_by_agg_count, pl):
    wins = group_by_agg_count('Winning Team', 'Wins')

    losses = group_by_agg_count('Losing Team', 'Losses')

    gd = (
        data.clone()
        .group_by('Home Team')
        .agg(pl.col('Goal Difference').sum().alias('GD'))
        .sort(by='GD')
        .rename({'Home Team': 'Team'})
    )

    win_loss_gd = (
        wins
        .join(losses, on='Team')
        .join(gd, on='Team')
        .filter(~pl.col('Team').eq('Draw'))
        .with_columns(
            (pl.col('Wins') / pl.col('Losses')).round(1).alias('Win-Loss Ratio')
        )
        .select(['Team', 'Win-Loss Ratio', 'GD'])
        .sort(['Win-Loss Ratio', 'GD'], descending=[True, True])
        # .head(4)
    )

    win_loss_gd
    return (win_loss_gd,)


@app.cell
def _(data, plt, sns, win_loss_gd):
    sns.barplot(win_loss_gd, x='Team', y='Win-Loss Ratio')
    plt.title(f'Ratio of games won to games lost for WSL teams from {data['Season'].unique().min()} to {data['Season'].unique().max()}')
    plt.xticks(rotation=45, ha='right')
    plt.gca()  # return the current axes as the final display value
    return


@app.cell
def _(data, plt, sns, win_loss_gd):
    sns.barplot(win_loss_gd.sort(['GD'], descending=[True]), x='Team', y='GD')
    plt.title(f'Goal Difference for WSL teams from {data['Season'].unique().min()} to {data['Season'].unique().max()}')
    plt.xticks(rotation=45, ha='right')
    plt.gca()  # return the current axes as the final display value
    return


if __name__ == "__main__":
    app.run()
