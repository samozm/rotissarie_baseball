import pandas as pd
import numpy as np
import math
from curses import wrapper
import urwid
from gurobi import *
from sklearn import preprocessing
from tabulate import tabulate
import json

# globals 
# tables with available players at each position
hitter_tables = { 'C': "",
                  '1B': "",
                  '2B': "",
                  'SS': "",
                  '3B': "",
                  'inner': "",
                  'outer': "",
                  'OF': "",
                  'util': "" }

pitcher_tables = { 'SP': "",
                   'RP': "" }

HitterPositions = ['C', '1B', '2B', 'SS', '3B', 'OF', 'outer', 'inner', 'util']
HitterMetrics = ['R', 'HR', 'RBI', 'SB', 'AVG']

PitcherPositions = ['SP', 'RP']
PitcherMetrics = ['W', 'SV', 'K', 'ERA', 'WHIP']


class Team:
    def __init__(self):
        # players
        self.Hitters = []
        self.Pitchers = []
        self.Bench = []
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
        self.Walks = 0
        self.IP = 0
        self.PitcherHits = 0

    def addHitterToTeam(self,hitter):
        self.BatterHits = self.BatterHits + hitter.H
        self.AB = self.AB + hitter.AB

        self.R = hitter.R
        self.HR = hitter.HR
        self.RBI = hitter.RBI
        self.SB = hitter.SB
        self.AVG = self.BatterHits / self.AB
        if len(self.Hitters) < 14:
            self.Hitters.append(hitter)
        else:
            self.Bench.append(hitter)

    def addPitcherToTeam(self,pitcher):
        self.IP = self.IP + pitcher.IP
        self.ER = self.ER + pitcher.ER
        self.Walks = self.Walks + pitcher.Walks
        self.PitcherHits = self.PitcherHits + pitcher.Hits

        self.K = self.K + pitcher.K
        self.W = self.W + pitcher.W
        self.SV = self.SV + pitcher.SV

        self.ERA = (self.ER / self.IP) * 9
        self.WHIP = (self.Walks + self.PitcherHits) / self.IP
        if len(self.Pitchers) < 11:
            self.Pitchers.append(pitcher)
        else:
            self.Bench.append(pitcher)

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
        self.Walks = Walks
        self.Team = ""

MyTeam = Team()
Opponents = {'Mighty Melonheads': Team(), 
             'Bethesda Bombers': Team(), 
             'The Riders of Rohan': Team(), 
             'Team Mitchel': Team(),
             'Sho Time': Team(), 
             'Saber Metrey': Team(), 
             'Cleveland Spiders': Team(),
             'Paul Sewald': Team(),
             'Show Me Ur Tatis': Team(), 
             'Rocket City Trash Pandas': Team(), 
             'Team 25': Team() }

# menu options
options = [u'View Top Players To Add', u'Add a Player To My Team', u'Add a Player To An Opposing Team', u'View My Team', u'View Opposing Team']

opposing_teams = [u'Mighty Melonheads', u'Bethesda Bombers', u'The Riders of Rohan', u'Team Mitchel', u'Sho Time', u'Saber Metrey', u'Cleveland Spiders', u'Paul Sewald', u'Show Me Ur Tatis', u'Rocket City Trash Pandas', u'Team 25']

add_to_opposing_teams = [u'Add to Mighty Melonheads', u'Add to Bethesda Bombers', u'Add to The Riders of Rohan', u'Add to Team Mitchel', u'Add to Sho Time', u'Add to Saber Metrey', u'Add to Cleveland Spiders', u'Add to Paul Sewald', u'Add to Show Me Ur Tatis', u'Add to Rocket City Trash Pandas', u'Add to Team 25']

view_opposing_teams = [u'View Mighty Melonheads', u'View Bethesda Bombers', u'View The Riders of Rohan', u'View Team Mitchel', u'View Sho Time', u'View Saber Metrey', u'View Cleveland Spiders', u'View Paul Sewald', u'View Show Me Ur Tatis', u'View Rocket City Trash Pandas', u'View Team 25']

# urwid functions
def menu_button(caption, callback):
    button = urwid.Button(caption)
    urwid.connect_signal(button, 'click', callback)
    return urwid.AttrMap(button, None, focus_map='reversed')

def sub_menu(caption, choices):
    contents = menu(caption, choices)
    def open_menu(button):
        return top.open_box(contents)
    return menu_button([caption, u'...'], open_menu)

def menu(title, choices):
    body = [urwid.Text(title), urwid.Divider()]
    body.extend(choices)
    return urwid.ListBox(urwid.SimpleFocusListWalker(body))

def item_chosen(button):
    # display in new box the information needed or accept player to add
    if (button.label == 'View Top Players To Add'):
        # get top players to add
        # display them in a list
        tm = buildTeam()
        potential = tm[tm['$'] != 0]
        mine = tm[tm['$'] == 0]
        display = urwid.Text("Top Options\n" + "-"*65 + "\n"
                   + tabulate(potential[['Name','POS','R', 'HR', 'RBI', 'SB', 'AVG','W', 'SV', 'K', 'ERA', 'WHIP','Ovr','$']], headers='keys',tablefmt='psql')
                   + "\nScore\n"
                   + json.dumps(get_score(tm[tm['Name'] == 'Total'].iloc[0]))
                   + "\nMy Team\n"
                   + tabulate(mine[['Name','POS','R', 'HR', 'RBI', 'SB', 'AVG','W', 'SV', 'K', 'ERA', 'WHIP','Ovr','$']], headers='keys',tablefmt='psql'))
        open_print_box(display)
    elif (button.label == 'View My Team'):
        display = urwid.Text("Budget: ${0} \n {1}".format(MyTeam.budget,printTeam(MyTeam)))
        open_print_box(display)
    elif (button.label == 'Add a Player To My Team'):
        get_player_add('my team')
    elif (button.label in view_opposing_teams):
        idx = view_opposing_teams.index(button.label)
        display = urwid.Text("Team: {0} \n {1}".format(opposing_teams[idx], printTeam(Opponents[opposing_teams[idx]])))
        open_print_box(display)
    elif (button.label in add_to_opposing_teams):
        idx = add_to_opposing_teams.index(button.label)
        get_player_add(opposing_teams[idx])



def open_print_box(display):
    def up_one(arg):
        return top.up_one()
    done = menu_button(u'Ok',up_one) #return up one level
    top.open_box(urwid.Filler(urwid.Pile([display,done])))


def exit_program(button):
    raise urwid.ExitMainLoop()

def question():
    return urwid.Pile([urwid.Edit(('I say', u'Enter a player name-price \n'))])

class GetPlayer(urwid.ListBox):
    def __init__(self,tmNm):
        self.tmNm = tmNm
        self.all_players = get_hitter_prices(get_hitters()).append(get_pitcher_prices(get_starting_pitchers()),ignore_index=True).append(get_pitcher_prices(get_closing_pitchers()),ignore_index=True)
        for team in opposing_teams:
            opp_players = getTeamPlayers(Opponents[team])
            for pl in opp_players:
                self.all_players = self.all_players[self.all_players['Name'] != pl]

        my_players = getTeamPlayers(MyTeam)
        for pl in my_players:
            self.all_players = self.all_players[self.all_players['Name'] != pl[0]]
        body = urwid.SimpleFocusListWalker([question()])
        super(GetPlayer,self).__init__(body)
        
    def keypress(self, size, key):
        key = super(GetPlayer, self).keypress(size,key)
        if key != 'enter':
            return key

        nmpr = self.focus[0].edit_text.split('-')
        noSkip = True
        name = ""
        price = 0
        if len(nmpr) != 2:
            skip = False
        else:
            name = nmpr[0]
            price = nmpr[1]
        pl = self.all_players[self.all_players['Name'].str.contains(name,case=False)].reset_index(drop=True)
        
        if noSkip and pl['Name'].count() > 0:
            if (pl.loc[0,'POS'] == 'SP' or pl.loc[0,'POS'] == 'RP'):
                if (self.tmNm in opposing_teams):
                    addPlayerToTeam(Pitcher(pl['Name'], pl['POS'], pl['K'], pl['W'], pl['SV'], pl['ER'], pl['IP'], pl['Hits'], pl['BB'],price),Opponents[self.tmNm],self.tmNm)
                else:
                    addPlayerToTeam(Pitcher(pl['Name'], pl['POS'], pl['K'], pl['W'], pl['SV'], pl['ER'], pl['IP'], pl['Hits'], pl['BB'],price),MyTeam,'my team')
            else:
                if (self.tmNm in opposing_teams):
                    addPlayerToTeam(Hitter(pl['Name'], pl['POS'], pl['R'], pl['HR'], pl['RBI'], pl['SB'],pl['H'],pl['AB'], price),Opponents[self.tmNm],self.tmNm)
                else:
                    addPlayerToTeam(Hitter(pl['Name'], pl['POS'], pl['R'], pl['HR'], pl['RBI'], pl['SB'], pl['H'], pl['AB'], price),MyTeam,'my team')
            display = urwid.Text('{0} added to {1}'.format(pl.loc[0,'Name'],self.tmNm))
            open_print_box(display)
        else:
            pos = self.focus_position
            self.body.insert(pos + 1, question())
            self.focus_position = pos + 1

menu_top = menu(u'Main Menu', [
    menu_button(options[0], item_chosen), # view players to add
    menu_button(options[1], item_chosen), # add player to my team
    sub_menu(options[2], [
        menu_button(add_to_opposing_teams[0], item_chosen),
        menu_button(add_to_opposing_teams[1], item_chosen),
        menu_button(add_to_opposing_teams[2], item_chosen),
        menu_button(add_to_opposing_teams[3], item_chosen),
        menu_button(add_to_opposing_teams[4], item_chosen),
        menu_button(add_to_opposing_teams[5], item_chosen),
        menu_button(add_to_opposing_teams[6], item_chosen),
        menu_button(add_to_opposing_teams[7], item_chosen),
        menu_button(add_to_opposing_teams[8], item_chosen),
        menu_button(add_to_opposing_teams[9], item_chosen),
        menu_button(add_to_opposing_teams[10], item_chosen),
    ]),# add to opposing team
    menu_button(options[3], item_chosen),
    sub_menu(options[4], [
        menu_button(view_opposing_teams[0], item_chosen),
        menu_button(view_opposing_teams[1], item_chosen),
        menu_button(view_opposing_teams[2], item_chosen),
        menu_button(view_opposing_teams[3], item_chosen),
        menu_button(view_opposing_teams[4], item_chosen),
        menu_button(view_opposing_teams[5], item_chosen),
        menu_button(view_opposing_teams[6], item_chosen),
        menu_button(view_opposing_teams[7], item_chosen),
        menu_button(view_opposing_teams[8], item_chosen),
        menu_button(view_opposing_teams[9], item_chosen),
        menu_button(view_opposing_teams[10], item_chosen),
    ]),# view opposing team
])


class CascadingBoxes(urwid.WidgetPlaceholder):
    max_box_levels = 3

    def __init__(self, box):
        super(CascadingBoxes, self).__init__(urwid.SolidFill(u'/'))
        self.box_level=0
        self.open_box(box)

    def open_box(self, box):
        self.original_widget = urwid.Overlay(urwid.LineBox(box),
            self.original_widget,
            align='center', width=('relative', 80),
            valign='middle', height=('relative', 80),
            min_width=24, min_height=8,
            left=self.box_level * 3,
            right=(self.max_box_levels - self.box_level - 1) * 3,
            top=self.box_level * 2,
            bottom=(self.max_box_levels - self.box_level - 1) * 2)
        self.box_level += 1

    def keypress(self, size, key):
        if key == 'esc' and self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1
        else:
            return super(CascadingBoxes, self).keypress(size, key)
    
    def up_one(self):
        while self.box_level > 1:
            self.original_widget = self.original_widget[0]
            self.box_level -= 1


top = CascadingBoxes(menu_top)

def get_player_add(tmNm):
    player_sel = False
    top.open_box(GetPlayer(tmNm))

def printTeam(tm):
    selected=[]
    for m in tm.Bench:
        if (m != ""):
            selected.append(m.Name)
    for m in tm.Hitters:
        if (m != ""):
            selected.append(m.Name)
    for m in tm.Pitchers:
        if (m != ""):
            selected.append(m.Name)
    all_players = get_hitter_prices(get_hitters()).append(get_pitcher_prices(get_starting_pitchers()),ignore_index=True).append(get_pitcher_prices(get_closing_pitchers()),ignore_index=True)
    pl = pd.DataFrame()
    for s in selected:
        pl = pl.append(all_players[all_players['Name'] == s[0]])
    if not pl.empty:
        return tabulate(pl[['Name','POS','R', 'HR', 'RBI', 'SB', 'AVG','W', 'SV', 'K', 'ERA', 'WHIP','Ovr','$']],headers='keys',tablefmt='psql')
    return 'No Players on team'
    #urwid.Text(tabulate(pl[['Name','POS','R', 'HR', 'RBI', 'SB', 'AVG','W', 'SV', 'K', 'ERA', 'WHIP','Ovr','$']], headers='keys',tablefmt='psql'))


def getTeamPlayers(tm):
    selected = []
    for m in tm.Bench:
        if (m != ""):
            selected.append(m.Name)
    for m in tm.Hitters:
        if (m != ""):
            selected.append(m.Name)
    for m in tm.Pitchers:
        if (m != ""):
            selected.append(m.Name)
    return selected

def get_hitters():
    hitters = pd.read_csv('razzball-hitters.csv', index_col='#', usecols=['#','Name','Team','ESPN','R','HR', 'RBI', 'SB','AVG','AB','H'])
    hitters.rename_axis('Razzball_Rank', inplace=True)
    hitters.reset_index(inplace=True)

    # sort and rank
    for metric in HitterMetrics:
        hitters.sort_values(by=[metric],inplace=True, ascending=False)
        hitters.reset_index(inplace=True, drop=True)
        hitters.index.rename('{} rank'.format(metric), inplace=True)
        hitters.reset_index(inplace=True)
    hitters['Ovr'] = (hitters['AVG rank'] + hitters['SB rank'] + hitters['RBI rank'] + hitters['HR rank'] + hitters['R rank']) / 5
    #hitters['Ovr'] = (hitters['Ovr'] + hitters['Razzball_Rank']) / 2
    hitters.rename(columns={'ESPN':'POS'}, inplace=True)
    
    hitters = hitters.assign(POS=hitters.POS.str.split('/')).explode('POS')
    hitters.sort_values(by=['Ovr'],inplace=True,ascending=True)
    return hitters

def get_starting_pitchers():
    pitchers = pd.read_csv('razzball-pitchers.csv', index_col='#', usecols=['#','Name','Team','POS','W', 'SV', 'K', 'ERA', 'WHIP','IP','BB','H', 'ER'])
    pitchers.rename_axis('Razzball_Rank', inplace=True)
    pitchers.reset_index(inplace=True)
    pitchers.rename(columns={'H':'Hits'}, inplace=True)
    
    pitchers = pitchers.assign(POS=pitchers.POS.str.split('/')).explode('POS')
    sp = pitchers[pitchers['POS'] == 'SP'].reset_index(drop=True)
    rp = pitchers[pitchers['POS'] == 'RP'].reset_index(drop=True)
    
    for metric in PitcherMetrics:
        if(metric != 'SV'):
            sp.sort_values(by=[metric],inplace=True, ascending=(metric=='WHIP' or metric=='ERA'))
            sp.reset_index(inplace=True, drop=True)
            sp.rename_axis('{} rank'.format(metric), inplace=True)
            sp.reset_index(inplace=True)
    
    sp['Ovr'] = (sp['W rank'] + sp['K rank'] + sp['ERA rank'] + sp['WHIP rank']) / 4
    sp.sort_values(by=['Ovr'],inplace=True,ascending=True)
    
    return sp

def get_closing_pitchers():
    pitchers = pd.read_csv('razzball-pitchers.csv', index_col='#', usecols=['#','Name','Team','POS','W', 'SV', 'K', 'ERA', 'WHIP','IP','BB','H', 'ER'])
    pitchers.rename_axis('Razzball_Rank', inplace=True)
    pitchers.reset_index(inplace=True)
    pitchers.rename(columns={'H':'Hits'}, inplace=True)
    
    pitchers = pitchers.assign(POS=pitchers.POS.str.split('/')).explode('POS')
    rp = pitchers[pitchers['POS'] == 'RP'].reset_index(drop=True)
    
    for metric in PitcherMetrics:
        if(metric != 'W'):
            rp.sort_values(by=[metric],inplace=True, ascending=(metric=='WHIP' or metric=='ERA'))
            rp.reset_index(inplace=True, drop=True)
            rp.rename_axis('{} rank'.format(metric), inplace=True)
            rp.reset_index(inplace=True)
    
    rp['Ovr'] = (rp['SV rank'] + rp['K rank'] + rp['ERA rank'] + rp['WHIP rank']) / 4
    rp.sort_values(by=['Ovr'],inplace=True,ascending=True)
    
    return rp
    
def get_hitter_prices(hitters):
    prices = pd.read_csv('razzball-hitters-prices.csv', index_col='#', usecols=['#', 'Name', 'Team', '5×5 $', '$R', '$HR', '$RBI', '$SB', '$AVG (no OBP)'])
    prices.rename(columns={'5×5 $': '$'},inplace=True)
    prices['$'] = prices['$'].apply(lambda x: 1 if x <=1 else x)
    hitters = hitters.merge(prices, left_on=['Name', 'Team'], right_on=['Name','Team'], how='left')
    return hitters

def get_pitcher_prices(pitchers):
    prices = pd.read_csv('razzball-pitchers-prices.csv', index_col='#', usecols=['#','Name','Team','5×5 $','$W (no QS)','$SV (no HLD)','$K','$WHIP','$ERA'])
    prices.rename(columns={'5×5 $': '$'},inplace=True)
    prices['$'] = prices['$'].apply(lambda x: 1 if x <=1 else x)
    pitchers = pitchers.merge(prices, left_on=['Name', 'Team'], right_on=['Name','Team'], how='left')
    return pitchers

def get_score(tm):
    score = {'R': 0,'HR':0,'RBI':0,'SB':0,'AVG':0,'K':0,'W':0,'SV':0,'ERA':0,'WHIP':0,'Total':0}
    R = sorted([1174,1136,1067,1006,1241,1110,974,997,1159,966,898])
    HR = sorted([433,352,353,284,382,321,291,332,355,302,260])
    RBI = sorted([1198,1088,1077,1030,1147,1016,955,1000,1075,905,897])
    SB = sorted([113,141,97,106,94,110,127,121,123,73,72])
    AVG = sorted([0.2735,0.2592,0.2740,0.2642,0.2768,0.2710,0.2620,0.2601,0.2705,0.2645,0.2641])
    K = sorted([1643,1531,1788,1598,1330,1387,1480,1725,1132,1391,1336])
    W = sorted([97,98,109,112,80,93,85,99,64,84,74])
    SV = sorted([59,73,3,55,115,79,105,42,39,59,54])
    ERA = sorted([3.907, 3.898,4.144,3.665,4.444,4.107,3.760,4.217,3.493,4.112,4.616],reverse=True)
    WHIP = sorted([1.216,1.244,1.262,1.102,1.339,1.247,1.210,1.291,1.131,1.267,1.284],reverse=True)
    
    hitter_scores = {'R':R,'HR':HR,'RBI':RBI,'SB':SB,'AVG':AVG}
    pitcher_scores = {'K':K,'W':W,'SV':SV,'ERA':ERA,'WHIP':WHIP}
    
    for metric in HitterMetrics:
        for s in range(len(hitter_scores[metric])):
            if(tm[metric] < hitter_scores[metric][s]):
                score[metric] = s+1
                score['Total'] += s+1
                break
        if (score[metric] == 0):
            score[metric] = 12
            score['Total'] += 12
    
    for metric in PitcherMetrics:
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

def buildTeam():
    budget = MyTeam.budget
    selected = getTeamPlayers(MyTeam)

    m = Model("mip1")
    # this works really well without using the maxes
    
    scaler = preprocessing.StandardScaler(with_std=False)
    all_players = get_hitter_prices(get_hitters()).nsmallest(150,'Ovr').append(get_pitcher_prices(get_starting_pitchers()).nsmallest(120,'Ovr'),ignore_index=True).append(get_pitcher_prices(get_closing_pitchers()).nsmallest(22,'SV rank'),ignore_index=True)
    
    for team in opposing_teams:
        opp_players = getTeamPlayers(Opponents[team])
        for pl in opp_players:
            all_players = all_players[all_players['Name'] != pl.iloc[0]].reset_index(drop=True)

    all_players.fillna(0, inplace=True)
    all_players['ERA'] = all_players['ERA'].apply(lambda x: 0 if x == 0 else 1/x)
    all_players['WHIP'] = all_players['WHIP'].apply(lambda x: 0 if x == 0 else 1/x)
    all_players['AB'] = all_players['AB'].apply(lambda x: 0 if x == 0 else 1/x)
    all_players['adjAVG'] = all_players['AVG']*100
    norm_players = all_players[['R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K','ERA','WHIP','AB','H']]
    
    norm_players = pd.DataFrame(scaler.fit_transform(norm_players),columns=['R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K', 'ERA', 'WHIP','H','AB'])
    
    for h in HitterMetrics:
        if h == 'AVG':
            all_players['normAVG'] = norm_players['adjAVG']
        else:
            all_players['norm{}'.format(h)] = norm_players[h]
    for p in PitcherMetrics:
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
    m.addConstr(sum([(allPOS[i]=='DH')*player_vars[i] for i in all_names]) == 0)
    
    
    m.addConstr(sum([allCosts[i]*player_vars[i]*(allPOS[i]=='RP' or allPOS[i]=='SP') for i in all_names]) <= 120)
    m.addConstr(sum([allCosts[i]*player_vars[i]*(allPOS[i]!='RP' and allPOS[i]!='SP') for i in all_names]) <= 140)
    
    
    # ensure no player is selected twice

    for f in all_names:
        m.addConstr(player_vars[f]>= player_chosen[all_players.iloc[f]['Name']]*0.01)
        m.addConstr(player_vars[f]<= player_chosen[all_players.iloc[f]['Name']]*1e8)
    
    
    m.addConstr(sum(player_chosen.values())==25)
    
    for s in selected:
        m.addConstr(player_chosen[s] >= 0.7)
    
    m.setParam(GRB.Param.PoolSolutions,10)
    m.setParam(GRB.Param.PoolSearchMode,2)
    
    m.setParam(GRB.Param.OutputFlag,0)

    m.optimize()
    
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
        sc = get_score(Team[Team['Name'] == 'Total'].iloc[0])['Total']
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
    return Team.append({'Name':'Total','AVG':sum(Team['H'])/sum(Team['AB']),'R':sum(Team['R']),'RBI':sum(Team['RBI']),'HR':sum(Team['HR']),'SB':sum(Team['SB']),'WHIP':(sum(Team['BB'])+sum(Team['Hits']))/sum(Team['IP']),'ERA':(sum(Team['ER'])/sum(Team['IP']))*9,'W':sum(Team['W']),'SV':sum(Team['SV']),'K':sum(Team['K']),'$':sum(Team['$'])},ignore_index=True)    

        

def main():
    # Clear screen
    urwid.MainLoop(top, palette=[('reversed', 'standout', '')]).run()

def addPlayerToTeam(player, team, teamName):
    if (player.Type == 'Pitcher'):
        team.addPitcherToTeam(player)
    else:
        team.addHitterToTeam(player);
    player.Team = teamName


if __name__ == '__main__':
    main()
