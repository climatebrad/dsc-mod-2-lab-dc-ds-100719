"""Soccer parser.

Usage:
from soccerparser import SoccerParser

sp = SoccerParser('database.sqlite')
sp.parse()
results = sp.results_df
"""

import sqlite3
import numpy as np
import pandas as pd
# import seaborn as sns

def esc(string):
    """utility function that escapes single quotes"""
    return string.replace("'", "\\'")

def ftr_to_winloss(ftr, is_home):
    """utility function that converts away/home/draw match results to win/loss/draw"""
    if ftr == 'D':
        return ftr
    if (is_home and (ftr == 'H')) or (not is_home and (ftr == 'A')):
        return 'W'
    return 'L'

class SoccerParser:
    """Parses soccer match information."""

    def __init__(self, database):
        self._con = sqlite3.connect(database)
        self.input_df = None
        self.teams = None
        self.results_df = None
        self.match_cols = ['match_id',
                           'team',
                           'opponent',
                           'date',
                           'div',
                           'goals',
                           'opp_goals',
                           'result',
                           'is_home']
        self.match_df = pd.DataFrame(columns=self.match_cols)

    def __del__(self):
        self._con.close()



    def parse(self):
        """Main function."""
        self._load_input()
        self._load_teams()
        self._load_matches()
        self._load_goals()
        self._load_wins()

    def _load_input(self):
        """Loads 2011 matches into input_df."""
        localdf = pd.read_sql("SELECT * FROM Matches", self._con, parse_dates=['Date'])
        self.input_df = localdf[localdf.Season == 2011].copy()

    def _load_team_home_or_away_matches(self, team, is_home: bool):
        """Called by _load_team_matches"""
        teamcat = 'HomeTeam' if is_home else 'AwayTeam'
        oppcat = 'AwayTeam' if is_home else 'HomeTeam'
        localdf = self.input_df.query(f"{teamcat} == '{esc(team)}'").copy()
        localdf = localdf.rename(columns={teamcat : 'team',
                                          oppcat : 'opponent'})
        localdf = localdf.rename(columns=lambda x: x.lower())
        localdf['is_home'] = is_home
        localdf = localdf.drop(columns='season')
        localdf.ftr = localdf.ftr.apply(ftr_to_winloss, args=[True])
        localdf = localdf.rename(columns={'fthg' : 'goals',
                                          'ftag' : 'opp_goals'})
        self.match_df[self.match_cols].append(localdf[self.match_cols], ignore_index=True)

    def _load_team_matches(self, team):
        """Loads match results of team into match_df"""
        self._load_team_home_or_away_matches(team, is_home=True)
        self._load_team_home_or_away_matches(team, is_home=False)

    def _load_matches(self):
        """Loads match results for every team into match_df"""
        self.results_df.team.apply(self._load_team_matches)

    def _load_teams(self):
        """Loads list of teams into teams and results_df."""
        self.teams = list(np.unique(self.input_df[["HomeTeam", "AwayTeam"]].values.ravel('F')))
        self.results_df = pd.DataFrame(self.teams, columns=['team'])

    def _load_goals(self):
        """Loads total goals scored by each team into results_df."""
        self.results_df['goals'] = self.results_df.team.apply(self.team_total_goals)

    def _load_wins(self):
        """Loads total wins by each team into results_df."""
        self.results_df['wins'] = self.results_df.team.apply(self.team_total_wins)

    def team_game_goals(self, team, home_or_away):
        """returns pd.Series with goals scored by team; home_or_away is 'H' or 'A'"""
        if home_or_away == 'H':
            teamcol = 'HomeTeam'
        elif home_or_away == 'A':
            teamcol = 'AwayTeam'
        else:
            raise ValueError(f"Invalid value {home_or_away}. Must be 'H' or 'A'.")
        gamecol = 'FT' + home_or_away + 'G'
        return pd.Series(self.input_df.query(f"{teamcol} == '{esc(team)}'")[gamecol])

    def team_total_goals(self, team):
        """returns total goals scored by team"""
        home_goals = self.team_game_goals(team, 'H')
        away_goals = self.team_game_goals(team, 'A')
        return home_goals.append(away_goals).sum()

    def team_total_wins(self, team):
        """returns total wins of team"""
        team = esc(team)
        return self.input_df.query(f"(HomeTeam == '{team}' and FTR == 'H')"
                                   + f"or (AwayTeam == '{team}' and FTR == 'A')").shape[0]
