import numpy as np
import pandas as pd
import seaborn as sns
import sqlite3

class SoccerParser:
    """Parses soccer match information."""
    def __init__(self, database):
        self.con = sqlite3.connect(database)
        self.df = None

    def parse(self)
        self.df = self._load_matches()

    def _load_matches(self):
        """Loads 2011 matches into df."""
        df = pd.read_sql("SELECT * FROM Matches", con, parse_dates=['Date'])
        self.df = df[df.Season == 2011]

    def game_goals(self, team, home_or_away):
        """returns pd.Series with goals scored by team; home_or_away is 'H' or 'A'"""
        if home_or_away == 'H':
            teamcol = 'HomeTeam'
        elif home_or_away == 'A':
            teamcol = 'AwayTeam'
        else:
            raise ValueError(f"Invalid value {home_or_away}. Must be 'H' or 'A'.")
        gamecol = 'FT' + home_or_away + 'G'
        team_esc = team.replace("'","\\'")
        return pd.Series(self.df.query(f"{teamcol}=='{team_esc}'")[gamecol])

    def total_goals(self, team):
        """returns total goals scored by team"""
        return game_goals(self.df, team, 'H').append(game_goals(self.df, team, 'A')).sum()
