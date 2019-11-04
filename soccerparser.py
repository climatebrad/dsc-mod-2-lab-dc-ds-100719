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
import matplotlib.pyplot as plt
import seaborn as sns

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

def winloss_to_int(winloss):
    """utility function that converts win to 1, loss to -1, draw to 0"""
    if winloss == 'W':
        return 1
    if winloss == 'L':
        return -1
    return 0

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

    ha_dict = {True: {'teamcol' : 'HomeTeam',
                      'oppcol' : 'AwayTeam',
                      'teamgoals' : 'FTHG',
                      'oppgoals' : 'FTAG'},
               False: {'teamcol' : 'AwayTeam',
                       'oppcol' : 'HomeTeam',
                       'teamgoals' : 'FTAG',
                       'oppgoals' : 'FTHG'}
              }

    team_cities_lookup = {
        'England' : {
            'url' : 'https://en.wikipedia.org/wiki/2011%E2%80%9312_Premier_League',
            'table_no' : 1,
            'team_field' : 'Team',
            'city_field' : 'Location'
        },
        'Germany' : {
            'url' : 'https://en.wikipedia.org/wiki/List_of_football_clubs_in_Germany',
            'table_no' : 0,
            'team_field' : 'Club',
            'city_field' : 'City'
        }
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

#  Load teams

    def _load_teams(self):
        """Loads list of teams into teams and results_df."""
        self.teams = list(np.unique(self.input_df[["HomeTeam", "AwayTeam"]].values.ravel('F')))
        self.results_df = pd.DataFrame(self.teams, columns=['team'])

# Load matches

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

        # convert FTR to winloss
        localdf.ftr = localdf.ftr.apply(ftr_to_winloss, is_home=is_home)

        # convert ftr goals to winloss goals
        teamgoals = SoccerParser.ha_dict[is_home]['teamgoals'].lower()
        oppgoals = SoccerParser.ha_dict[is_home]['oppgoals'].lower()
        localdf = localdf.rename(columns={'ftr' : 'result',
                                          teamgoals : 'goals',
                                          oppgoals : 'opp_goals'})
        # append results to self.match_df
        match_cols = SoccerParser.match_cols
        self.match_df = self.match_df[match_cols].append(localdf[match_cols], ignore_index=True)

    def _load_team_matches(self, team):
        """Loads match results of team into match_df"""
        self._load_team_home_or_away_matches(team, is_home=True)
        self._load_team_home_or_away_matches(team, is_home=False)

    def _load_matches(self):
        """Loads match results for every team into match_df"""
        for team in self.teams:
            self._load_team_matches(team)
        self.match_df['result_int'] = self.match_df.result.apply(winloss_to_int)


# Team goals

# old way of generating:
#    def team_game_goals(self, team, is_home: bool):
#        """returns pd.Series with goals scored by team at home or away"""
#        teamgoals = SoccerParser.ha_dict[is_home]['teamgoals']
#        teamcol = SoccerParser.ha_dict[is_home]['teamcol']
#        return pd.Series(self.input_df.query(f"{teamcol} == '{esc(team)}'")[teamgoals])

    def team_total_goals(self, team):
        """returns total goals scored by team"""
        return self.match_df[self.match_df.team == team].goals.sum()

#        home_goals = self.team_game_goals(team, is_home=True)
#        away_goals = self.team_game_goals(team, is_home=False)
#        return home_goals.append(away_goals).sum()

    def _load_goals(self):
        """Loads total goals scored by each team into results_df."""
        self.results_df['goals'] = self.results_df.team.apply(self.team_total_goals)

# Team wins - probably easier to calculate from self.match_df
# self.match_df[self.match_df.team = team].goals.sum()

    def team_total_wins(self, team):
        """returns total wins of team"""
        team = esc(team)
        return self.input_df.query(f"(HomeTeam == '{team}' and FTR == 'H')"
                                   + f"or (AwayTeam == '{team}' and FTR == 'A')").shape[0]

    def _load_wins(self):
        """Loads total wins by each team into results_df."""
        self.results_df['wins'] = self.results_df.team.apply(self.team_total_wins)


    def team_win_chart(self, team):
        """returns axes object with bar chart of wins, losses, and draws for team"""
        if team not in self.teams:
            raise ValueError(f"No such team {team} found.")
        sns.set(style="darkgrid")
        ax = sns.countplot(data=self.match_df[self.match_df.team == team],
                      x='result',
                      order=['W', 'L', 'D'],
                      palette=sns.xkcd_palette(['emerald', 'cherry', 'grey']))
        ax.set_title(f"{team} 2011 Season", fontsize='x-large')
        return ax

    def _load_team_cities(self, country):
        """Load team cities from Wikipedia"""
        url = SoccerParser.team_cities_lookup[country]['url']
        table_no = SoccerParser.team_cities_lookup[country]['table_no']
        city_field = SoccerParser.team_cities_lookup[country]['city_field']
        team_field = SoccerParser.team_cities_lookup[country]['team_field']
        c_teams_df = pd.read_html(url)[table_no]
        for team in self.teams:
            city_as_dict = c_teams_df[c_teams_df[team_field].str.contains(team)][city_field]
            if not city_as_dict.empty:
                city = city_as_dict.values[0]
                self.results_df[self.results_df.team == team]['city'] = city
                self.results_df[self.results_df.team == team]['country'] = country
