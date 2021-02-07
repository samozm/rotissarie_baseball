import pandas as pd
import numpy as np
import math
from gurobipy import *
from sklearn import preprocessing
import json
import razzball_scraper

class Team:
    def __init__(self):
        # players
        self.Hitters = {}
        self.Pitchers = {}
        self.Bench = {}
        self.budget = 260

        # batter scoring stats
        self.R = 0
        self.HR = 0
        self.RBI = 0
        self.SB = 0
        self.AVG = math.inf

        # batter auxiliary stats
        self.BatterHits = 0
        self.AB = 0

        # pitcher scoring stats
        self.K = 0
        self.W = 0
        self.SV = 0
        self.ERA = math.inf
        self.WHIP = math.inf

        # pitcher auxiliary stats
        self.ER = 0
        self.BB = 0
        self.IP = 0
        self.PitcherHits = 0

    def add_hitter_to_team(self,hitter):
        self.BatterHits = self.BatterHits + hitter.H
        self.AB = self.AB + hitter.AB

        self.R = hitter.R
        self.HR = hitter.HR
        self.RBI = hitter.RBI
        self.SB = hitter.SB
        self.AVG = self.BatterHits / self.AB
        if len(self.Hitters) < 14:
            self.Hitters[hitter.Name] = hitter
        else:
            self.Bench[hitter.Name] = hitter

    def add_pitcher_to_team(self,pitcher):
        print(pitcher)
        self.IP = self.IP + pitcher.IP
        self.ER = self.ER + pitcher.ER
        self.BB = self.BB + pitcher.BB
        self.PitcherHits = self.PitcherHits + pitcher.Hits

        self.K = self.K + pitcher.K
        self.W = self.W + pitcher.W
        self.SV = self.SV + pitcher.SV

        self.ERA = (self.ER / self.IP) * 9
        self.WHIP = (self.BB + self.PitcherHits) / self.IP
        if len(self.Pitchers) < 11:
            self.Pitchers[pitcher.Name] = pitcher
        else:
            self.Bench[pitcher.Name] = pitcher

class Hitter:
    Type = "Hitter"

    def __init__(self, name, positions, R, HR, RBI, SB, H, AB, estPrice):
        self.Name = name
        self.Pos = positions
        self.R = R
        self.HR = HR
        self.RBI = RBI
        self.SB = SB
        self.H = H
        self.AB = AB
        self.Price = estPrice
        self.Team = ""

class Pitcher:
    Type = "Pitcher"

    def __init__(self, name, positions, K, W, SV, ER, IP, Hits, Walks, estPrice):
        self.Name = name
        self.Pos = positions
        self.K = K
        self.W = W
        self.SV = SV
        self.ER = ER
        self.IP = IP
        self.Hits = Hits
        self.Price = estPrice
        self.BB = Walks
        self.Team = ""


class Optimizer:
    HitterPositions = ['C', '1B', '2B', 'SS', '3B', 'OF', 'outer', 'inner', 'util']
    HitterMetrics = ['R', 'HR', 'RBI', 'SB', 'AVG']

    PitcherPositions = ['SP', 'RP']
    PitcherMetrics = ['W', 'SV', 'K', 'ERA', 'WHIP']
    Teams = {}
    opposing_team_names = []
    all_players = []

    
    def __init__(self):
        self.Teams["My Team"] = Team()
        self.all_players = self.get_hitter_prices(self.get_hitters()).nsmallest(150,'Ovr').append(self.get_pitcher_prices(self.get_starting_pitchers()).nsmallest(120,'Ovr'),ignore_index=True).append(self.get_pitcher_prices(self.get_closing_pitchers()).nsmallest(22,'SV rank'),ignore_index=True)
        self.all_players.fillna(0, inplace=True)
        self.all_players['ERA'] = self.all_players['ERA'].apply(lambda x: 0 if x == 0 else 1/x)
        self.all_players['WHIP'] = self.all_players['WHIP'].apply(lambda x: 0 if x == 0 else 1/x)
        self.all_players['AB'] = self.all_players['AB'].apply(lambda x: 0 if x == 0 else 1/x)
        self.all_players['adjAVG'] = self.all_players['AVG']*100

    def get_all_players(self):
        return self.all_players

    def get_team(self, teamName):
        return self.Teams[teamName]

    def add_team(self, team):
        self.Teams[team] = Team()
        self.opposing_team_names.append(team)

    def remove_team(self, team):
        self.Teams.pop(team)
        self.opposing_team_names.remove(team)

    def get_budget(self, teamName):
        tm = self.Teams[teamName]
        return tm.budget


    def get_team_players(self, tm):
        selected = []
        for m in tm.Bench.values():
            if not (m.empty):
                selected.append(m.Name)
        for m in tm.Hitters.values():
            if not (m.empty):
                selected.append(m.Name)
        for m in tm.Pitchers.values():
            print(m)
            if not (m.empty):
                selected.append(m.Name)
        return selected
        
    def get_hitters(self, combined=False):
        hitters = pd.read_csv('data/razzball-hitters.csv', index_col='#', usecols=['#','Name','Team','ESPN','R','HR', 'RBI', 'SB','AVG','AB','H'])
        hitters.rename_axis('Razzball_Rank', inplace=True)
        hitters.reset_index(inplace=True)

        # sort and rank
        for metric in self.HitterMetrics:
            hitters.sort_values(by=[metric],inplace=True, ascending=False)
            hitters.reset_index(inplace=True, drop=True)
            hitters.index.rename('{} rank'.format(metric), inplace=True)
            hitters.reset_index(inplace=True)
        hitters['Ovr'] = (hitters['AVG rank'] + hitters['SB rank'] + hitters['RBI rank'] + hitters['HR rank'] + hitters['R rank']) / 5
        #hitters['Ovr'] = (hitters['Ovr'] + hitters['Razzball_Rank']) / 2
        hitters.rename(columns={'ESPN':'POS'}, inplace=True)
        
        if (combined):
            hitters = hitters.assign(POS=hitters.POS.str.split('/'))
        else:
            hitters = hitters.assign(POS=hitters.POS.str.split('/')).explode('POS')
        
        hitters.sort_values(by=['Ovr'],inplace=True,ascending=True)
        return hitters

    def get_starting_pitchers(self):
        pitchers = pd.read_csv('data/razzball-pitchers.csv', index_col='#', usecols=['#','Name','Team','POS','W', 'SV', 'K', 'ERA', 'WHIP','IP','BB','H', 'ER'])
        pitchers.rename_axis('Razzball_Rank', inplace=True)
        pitchers.reset_index(inplace=True)
        pitchers.rename(columns={'H':'Hits'}, inplace=True)
        
        pitchers = pitchers.assign(POS=pitchers.POS.str.split('/')).explode('POS')
        sp = pitchers[pitchers['POS'] == 'SP'].reset_index(drop=True)
        rp = pitchers[pitchers['POS'] == 'RP'].reset_index(drop=True)
        
        for metric in self.PitcherMetrics:
            if(metric != 'SV'):
                sp.sort_values(by=[metric],inplace=True, ascending=(metric=='WHIP' or metric=='ERA'))
                sp.reset_index(inplace=True, drop=True)
                sp.rename_axis('{} rank'.format(metric), inplace=True)
                sp.reset_index(inplace=True)
        
        sp['Ovr'] = (sp['W rank'] + sp['K rank'] + sp['ERA rank'] + sp['WHIP rank']) / 4
        sp.sort_values(by=['Ovr'],inplace=True,ascending=True)
        
        return sp

    def get_closing_pitchers(self):
        pitchers = pd.read_csv('data/razzball-pitchers.csv', index_col='#', usecols=['#','Name','Team','POS','W', 'SV', 'K', 'ERA', 'WHIP','IP','BB','H', 'ER'])
        pitchers.rename_axis('Razzball_Rank', inplace=True)
        pitchers.reset_index(inplace=True)
        pitchers.rename(columns={'H':'Hits'}, inplace=True)
        
        pitchers = pitchers.assign(POS=pitchers.POS.str.split('/')).explode('POS')
        rp = pitchers[pitchers['POS'] == 'RP'].reset_index(drop=True)
        
        for metric in self.PitcherMetrics:
            if(metric != 'W'):
                rp.sort_values(by=[metric],inplace=True, ascending=(metric=='WHIP' or metric=='ERA'))
                rp.reset_index(inplace=True, drop=True)
                rp.rename_axis('{} rank'.format(metric), inplace=True)
                rp.reset_index(inplace=True)
        
        rp['Ovr'] = (rp['SV rank'] + rp['K rank'] + rp['ERA rank'] + rp['WHIP rank']) / 4
        rp.sort_values(by=['Ovr'],inplace=True,ascending=True)
        
        return rp
        
    def get_hitter_prices(self, hitters):
        prices = pd.read_csv('data/razzball-hitters-prices.csv', index_col='#', usecols=['#', 'Name', 'Team', '5×5 $', '$R', '$HR', '$RBI', '$SB', '$AVG (no OBP)'])
        prices.rename(columns={'5×5 $': '$'},inplace=True)
        prices['$'] = prices['$'].apply(lambda x: 1 if x <=1 else x)
        hitters = hitters.merge(prices, left_on=['Name', 'Team'], right_on=['Name','Team'], how='left')
        return hitters

    def get_pitcher_prices(self, pitchers):
        prices = pd.read_csv('data/razzball-pitchers-prices.csv', index_col='#', usecols=['#','Name','Team','5×5 $','$W (no QS)','$SV (no HLD)','$K','$WHIP','$ERA'])
        prices.rename(columns={'5×5 $': '$'},inplace=True)
        prices['$'] = prices['$'].apply(lambda x: 1 if x <=1 else x)
        pitchers = pitchers.merge(prices, left_on=['Name', 'Team'], right_on=['Name','Team'], how='left')
        return pitchers

    def get_score(self, tm):
        score = {'R': 0,'HR':0,'RBI':0,'SB':0,'AVG':0,'K':0,'W':0,'SV':0,'ERA':0,'WHIP':0,'Total':0}
        R = sorted([i * (60/162) for i in [1174,1136,1067,1006,1241,1110,974,997,1159,966,898]])
        HR = sorted([i * (60/162) for i in [433,352,353,284,382,321,291,332,355,302,260]])
        RBI = sorted([i * (60/162) for i in [1198,1088,1077,1030,1147,1016,955,1000,1075,905,897]])
        SB = sorted([i * (60/162) for i in [113,141,97,106,94,110,127,121,123,73,72]])
        AVG = sorted([0.2735,0.2592,0.2740,0.2642,0.2768,0.2710,0.2620,0.2601,0.2705,0.2645,0.2641])
        K = sorted([i * (60/162) for i in [1643,1531,1788,1598,1330,1387,1480,1725,1132,1391,1336]])
        W = sorted([i * (60/162) for i in [97,98,109,112,80,93,85,99,64,84,74]])
        SV = sorted([i * (60/162) for i in [59,73,3,55,115,79,105,42,39,59,54]])
        ERA = sorted([3.907, 3.898,4.144,3.665,4.444,4.107,3.760,4.217,3.493,4.112,4.616],reverse=True)
        WHIP = sorted([1.216,1.244,1.262,1.102,1.339,1.247,1.210,1.291,1.131,1.267,1.284],reverse=True)
        
        hitter_scores = {'R':R,'HR':HR,'RBI':RBI,'SB':SB,'AVG':AVG}
        pitcher_scores = {'K':K,'W':W,'SV':SV,'ERA':ERA,'WHIP':WHIP}
        
        for metric in self.HitterMetrics:
            for s in range(len(hitter_scores[metric])):
                if(tm[metric] < hitter_scores[metric][s]):
                    score[metric] = s+1
                    score['Total'] += s+1
                    break
            if (score[metric] == 0):
                score[metric] = 12
                score['Total'] += 12
        
        for metric in self.PitcherMetrics:
            if (metric != 'ERA') and (metric != 'WHIP'):
                for s in range(len(pitcher_scores[metric])):
                    if(tm[metric] < pitcher_scores[metric][s]):
                        score[metric] = s+1
                        score['Total'] += s+1
                        break
            else:
                for s in range(len(pitcher_scores[metric])):
                    if(tm[metric] > pitcher_scores[metric][s]):
                        score[metric] = s+1
                        score['Total'] += s+1
                        break
            if (score[metric] == 0):
                score[metric] = 12
                score['Total'] += 12
                
        return score

    def build_team(self):
        budget = self.Teams["My Team"].budget
        selected = self.get_team_players(self.Teams["My Team"])

        m = Model("mip1")
        # this works really well without using the maxes
        
        scaler = preprocessing.StandardScaler(with_std=False)

        all_players = self.all_players
        
        for team in self.opposing_team_names:
            opp_players = self.get_team_players(self.Teams[team])
            for pl in opp_players:
                all_players = all_players[all_players['Name'] != pl].reset_index(drop=True)

        
        norm_players = all_players[['R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K','ERA','WHIP','AB','H']]
        
        norm_players = pd.DataFrame(scaler.fit_transform(norm_players),columns=['R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K', 'ERA', 'WHIP','H','AB'])
        
        for h in self.HitterMetrics:
            if h == 'AVG':
                all_players['normAVG'] = norm_players['adjAVG']
            else:
                all_players['norm{}'.format(h)] = norm_players[h]
        for p in self.PitcherMetrics:
            all_players['norm{}'.format(p)] = norm_players[p]
        
        for h in ['AB','H']:
            all_players['norm{}'.format(h)] = norm_players[h]
        
        all_names = list(all_players.index)
        name_list = list(dict.fromkeys(all_players['Name']))
        for s in selected:
            all_players.loc[all_players['Name'] == s,'$'] = 0
        allCosts = dict(zip(all_names,all_players['$']))
        
        player_vars = m.addVars(all_names,vtype=GRB.INTEGER,lb=0,ub=1,name='players')
        player_chosen = m.addVars(name_list,vtype=GRB.INTEGER,lb=0,ub=1,name='pl_chosen')
        
        allRuns = dict(zip(all_names,all_players['normR']))
        allHRs = dict(zip(all_names,all_players['normHR']))
        allRBIs = dict(zip(all_names,all_players['normRBI']))
        allSBs = dict(zip(all_names,all_players['normSB']*2.5))
        allAVG = dict(zip(all_names,all_players['normAVG']))
        allAB = dict(zip(all_names,all_players['normAB']*0.8))
        allH = dict(zip(all_names,all_players['normH']*0.8))

        
        allWs = dict(zip(all_names,all_players['normW']))
        allKs = dict(zip(all_names,all_players['normK']))
        allSVs = dict(zip(all_names,all_players['normSV']))
        allERA = dict(zip(all_names,all_players['normERA']))
        allWHIP = dict(zip(all_names,all_players['normWHIP']))
        allPOS = dict(zip(all_names,all_players['POS']))
        
        obj = LinExpr()
        
        obj += quicksum([allRuns[i]*player_vars[i] for i in all_names])
        obj += quicksum([allHRs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allRBIs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allSBs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allAVG[i]*player_vars[i] for i in all_names])
        obj += quicksum([allWs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allKs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allSVs[i]*player_vars[i] for i in all_names])
        obj += quicksum([allERA[i]*player_vars[i] for i in all_names])
        obj += quicksum([allWHIP[i]*player_vars[i] for i in all_names])
        obj += quicksum([allCosts[i]*player_vars[i] for i in all_names])
        obj += quicksum([allH[i]*player_vars[i] for i in all_names])
        obj += quicksum([allAB[i]*player_vars[i] for i in all_names])
        m.setObjective(obj, GRB.MAXIMIZE)
        
        m.addConstr(sum([allCosts[i]*player_vars[i] for i in all_names])<= budget)
        
        m.addConstr(sum([(allPOS[i]=='C')*player_vars[i] for i in all_names]) == 1)
        
        # update these based on position depth
        m.addConstr(sum([(allPOS[i]=='1B')*player_vars[i] for i in all_names]) == 2)
        m.addConstr(sum([(allPOS[i]=='2B')*player_vars[i] for i in all_names]) == 2)
        m.addConstr(sum([(allPOS[i]=='3B')*player_vars[i] for i in all_names]) == 1)
        m.addConstr(sum([(allPOS[i]=='SS')*player_vars[i] for i in all_names]) == 2)
        
        m.addConstr(sum([(allPOS[i]=='OF')*player_vars[i] for i in all_names]) == 6)
        
        m.addConstr(sum([(allPOS[i]=='SP')*player_vars[i] for i in all_names]) == 8)
        
        m.addConstr(sum([(allPOS[i]=='RP')*player_vars[i] for i in all_names]) == 3)
        m.addConstr(sum([(allPOS[i]=='DH')*player_vars[i] for i in all_names]) == 1)
        
        
        m.addConstr(sum([allCosts[i]*player_vars[i]*(allPOS[i]=='RP' or allPOS[i]=='SP') for i in all_names]) <= 120)
        m.addConstr(sum([allCosts[i]*player_vars[i]*(allPOS[i]!='RP' and allPOS[i]!='SP') for i in all_names]) <= 140)
        
        
        # ensure no player is selected twice

        for f in all_names:
            m.addConstr(player_vars[f]>= player_chosen[all_players.iloc[f]['Name']]*0.01)
            m.addConstr(player_vars[f]<= player_chosen[all_players.iloc[f]['Name']]*1e8)
        
        
        m.addConstr(sum(player_chosen.values())==26)
        
        for s in selected:
            m.addConstr(player_chosen[s] >= 0.7)
        
        m.setParam(GRB.Param.PoolSolutions,10)
        m.setParam(GRB.Param.PoolSearchMode,2)
        
        m.setParam(GRB.Param.OutputFlag,0)

        m.optimize()
        
        all_players['AB'] = all_players['AB'].apply(lambda x: 0 if x == 0 else 1/x)
        nSolns = m.SolCount
        max_tot = 0
        best = 0
        for e in range(nSolns):
            Team = pd.DataFrame()
            m.setParam(GRB.Param.SolutionNumber,e)
            for v in m.getVars():
                if v.Xn > 0.01 and not 'chosen' in v.varName:
                    Team = Team.append(all_players.iloc[int(v.varName.split('[')[1].split(']')[0])])
            Team = Team.append(Team.append({'Name':'Total','AVG':sum(Team['H'])/sum(Team['AB']),'R':sum(Team['R']),'RBI':sum(Team['RBI']),'HR':sum(Team['HR']),'SB':sum(Team['SB']),'WHIP':(sum(Team['BB'])+sum(Team['Hits']))/sum(Team['IP']),'ERA':(sum(Team['ER'])/sum(Team['IP']))*9,'W':sum(Team['W']),'SV':sum(Team['SV']),'K':sum(Team['K']),'$':sum(Team['$'])},ignore_index=True))
            sc = self.get_score(Team[Team['Name'] == 'Total'].iloc[0])['Total']
            if (sc > max_tot):
                best = e
                max_tot = sc
        Team = pd.DataFrame()
        m.setParam(GRB.Param.SolutionNumber,best)
        for v in m.getVars():
            if v.Xn > 0.01 and not 'chosen' in v.varName:
                Team = Team.append(all_players.iloc[int(v.varName.split('[')[1].split(']')[0])])
        
        
        Team['ERA'] = Team['ERA'].apply(lambda x: 0 if x == 0 else 1/x)
        Team['WHIP'] = Team['WHIP'].apply(lambda x: 0 if x == 0 else 1/x)
        return Team.append({'Name':'Total','AVG':(sum(Team['H'])/sum(Team['AB'])),'R':sum(Team['R']),'RBI':sum(Team['RBI']),'HR':sum(Team['HR']),'SB':sum(Team['SB']),'WHIP':(sum(Team['BB'])+sum(Team['Hits']))/sum(Team['IP']),'ERA':(sum(Team['ER'])/sum(Team['IP']))*9,'W':sum(Team['W']),'SV':sum(Team['SV']),'K':sum(Team['K']),'$':sum(Team['$'])},ignore_index=True)

    def add_player_to_team(self, player, teamName, position, price):
        team = self.Teams[teamName]
        pl = self.all_players[self.all_players['Name'].str.contains(player,case=False)].reset_index(drop=True).iloc[0]
        if (position == 'SP' or position == 'RP' or position == "SP/RP"):
            team.add_pitcher_to_team(pl)
        else:
            team.add_hitter_to_team(pl)
        team.budget -= price
        #player.Team = teamName

    def remove_player_from_team(self, player, teamName, position):
        team = self.Teams[teamName]
        if(player in team.Hitters):
            team.Hitters.pop(player)
        elif(player in team.Pitchers):
            team.Pitchers.pop(player)
        elif(player in team.Bench):
            team.Bench.pop(player)

    def print_team(self, teamName):
        tm = self.Teams[teamName]
        selected={}
        for m in tm.Bench:
            if (m != ""):
                player = self.all_players[self.all_players['Name'] == m].iloc[0]
                selected[player['Name']] = player['$']
        for m in tm.Hitters:
            if (m != ""):
                player = self.all_players[self.all_players['Name'] == m].iloc[0]
                selected[player['Name']] = player['$']
        for m in tm.Pitchers:
            if (m != ""):
                player = self.all_players[self.all_players['Name'] == m].iloc[0]
                selected[player['Name']] = player['$']
        pl = pd.DataFrame()
        for key,val in selected.items():
            pl = pl.append(self.all_players[self.all_players['Name'] == key])
            pl.loc[pl['Name'] == key,'$'] = val
        if not pl.empty:
            return pl[['Name','POS','R', 'HR', 'RBI', 'SB', 'AVG','W', 'SV', 'K', 'ERA', 'WHIP','Ovr','$']]
        return 'No Players on team'