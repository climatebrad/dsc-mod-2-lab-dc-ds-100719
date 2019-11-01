"""Soccer parser.

Usage:
from soccerparser import SoccerParser

sp = SoccerParser('database.sqlite')
sp.parse()
results = sp.results_df
"""

import numpy as np
import pandas as pd
import seaborn as sns
import sqlite3

class SoccerParser:
    """Parses soccer match information."""
    def __init__(self, database):
        self._con = sqlite3.connect(database)
        self.match_df = None
        self.teams = None
        self.results_df = None

    def __del__(self):
        self._con.close()

    def parse(self):
        """Main function."""
        self._load_matches()
        self._load_teams()
        self._load_goals()

    def _load_goals(self):
        """Loads total goals scored by each team into results_df."""
        self.results_df['goals'] = self.results_df.team.apply(self.total_goals)

    def _load_teams(self):
        """Loads list of teams into teams and results_df."""
        self.teams = list(np.unique(self.match_df[["HomeTeam", "AwayTeam"]].values.ravel('F')))
        self.results_df = pd.DataFrame(self.teams, columns=['team'])

    def _load_matches(self):
        """Loads 2011 matches into df."""
        df = pd.read_sql("SELECT * FROM Matches", self._con, parse_dates=['Date'])
        self.match_df = df[df.Season == 2011]

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
        return pd.Series(self.match_df.query(f"{teamcol} == '{team_esc}'")[gamecol])

    def total_goals(self, team):
        """returns total goals scored by team"""
        home_goals = self.game_goals(team, 'H')
        away_goals = self.game_goals(team, 'A')
        return home_goals.append(away_goals).sum()
