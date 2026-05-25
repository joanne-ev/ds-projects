import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _():
    import polars as pl
    import matplotlib.pyplot as plt
    import duckdb


    df = pl.read_csv("data/fifa26-wc-2026.csv")

    print(df.head())

    print(df.columns)

    print(df.describe())
    return


if __name__ == "__main__":
    app.run()
