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

def ftr_to_winloss(ftr, is_home: bool):
    """utility function that converts away/home/draw match results to win/loss/draw"""
    if ftr == 'D':
        return ftr
    if (is_home and (ftr == 'H')) or (not is_home and (ftr == 'A')):
        return 'W'
    return 'L'

class SoccerParser:
    """Parses soccer match information."""
    match_cols = ['match_id',
                       'team',
                       'opponent',
                       'date',
                       'div',
                       'goals',
                       'opp_goals',
                       'result',
                       'is_home']

    ha_dict = { True: { 'teamcol' : 'HomeTeam',
                       'oppcol' : 'AwayTeam',
                       'teamgoals' : 'FTHG',
                       'oppgoals' : 'FTAG' },
                False: { 'teamcol' : 'AwayTeam',
                        'oppcol' : 'HomeTeam',
                        'teamgoals' : 'FTAG',
                        'oppgoals' : 'FTHG' }
              }

    def __init__(self, database):
        self._con = sqlite3.connect(database)
        self.input_df = None
        self.teams = None
        self.results_df = None
        self.match_df = pd.DataFrame(columns=SoccerParser.match_cols)

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
        teamcol = SoccerParser.ha_dict[is_home]['teamcol']

        oppcol = SoccerParser.ha_dict[is_home]['oppcol']
        localdf = self.input_df.query(f"{teamcol} == '{esc(team)}'").copy()

        # Standardize column names
        localdf = localdf.rename(columns={teamcol : 'team',
                                          oppcol : 'opponent'})
        localdf.columns = localdf.columns.str.lower()

        # Create is_home boolean column
        localdf['is_home'] = is_home

        # Drop the season column
        localdf = localdf.drop(columns='season')
        localdf.ftr = localdf.ftr.apply(ftr_to_winloss, is_home=is_home)

        teamgoals = SoccerParser.ha_dict[is_home]['teamgoals'].lower()
        oppgoals = SoccerParser.ha_dict[is_home]['oppgoals'].lower()
        localdf = localdf.rename(columns={'ftr' : 'result',
                                          teamgoals : 'goals',
                                          oppgoals : 'opp_goals'})
        self.match_df = self.match_df[SoccerParser.match_cols].append(localdf[SoccerParser.match_cols], ignore_index=True)

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

    def team_game_goals(self, team, is_home: bool):
        """returns pd.Series with goals scored by team"""
        teamgoals = SoccerParser.ha_dict[is_home]['teamgoals']
        teamcol = SoccerParser.ha_dict[is_home]['teamcol']
        return pd.Series(self.input_df.query(f"{teamcol} == '{esc(team)}'")[teamgoals])

    def team_total_goals(self, team):
        """returns total goals scored by team"""
        home_goals = self.team_game_goals(team, is_home=True)
        away_goals = self.team_game_goals(team, is_home=False)
        return home_goals.append(away_goals).sum()

    def team_total_wins(self, team):
        """returns total wins of team"""
        team = esc(team)
        return self.input_df.query(f"(HomeTeam == '{team}' and FTR == 'H')"
                                   + f"or (AwayTeam == '{team}' and FTR == 'A')").shape[0]
