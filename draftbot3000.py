import pandas as pd
import numpy as np
import math
from curses import wrapper
import urwid

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

# menu options
options = [u'View Top Players To Add', u'Add a Player To My Team', u'Add a Player To An Opposing Team', u'View My Team', u'View Opposing Team']

opposing_teams = [u'Mighty Melonheads', u'Bethesda Bombers', u'The Riders of Rohan', u'Team Mitchel', u'Sho Time', u'Saber Metrey', u'Cleveland Spiders', u'Paul Sewald', u'Show Me Ur Tatis', u'Rocket City Trash Pandas', u'Team 25']


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
        print(button)
    elif (button.label == 'View My Team'):
        print(button)
    elif (button.label == 'Add a Player To My Team'):
        print(button)
    elif (button.label in opposing_teams):
        print(button)

def exit_program(button):
    raise urwid.ExitMainLoop()

menu_top = menu(u'Main Menu', [
    menu_button(options[0], item_chosen), # view players to add
    menu_button(options[1], item_chosen), # add player to my team
    sub_menu(options[2], [
        menu_button(opposing_teams[0], item_chosen),
        menu_button(opposing_teams[1], item_chosen),
        menu_button(opposing_teams[2], item_chosen),
        menu_button(opposing_teams[3], item_chosen),
        menu_button(opposing_teams[4], item_chosen),
        menu_button(opposing_teams[5], item_chosen),
        menu_button(opposing_teams[6], item_chosen),
        menu_button(opposing_teams[7], item_chosen),
        menu_button(opposing_teams[8], item_chosen),
        menu_button(opposing_teams[9], item_chosen),
        menu_button(opposing_teams[10], item_chosen),
    ]),
    menu_button(options[3], item_chosen),
    sub_menu(options[4], [
        menu_button(opposing_teams[0], item_chosen),
        menu_button(opposing_teams[1], item_chosen),
        menu_button(opposing_teams[2], item_chosen),
        menu_button(opposing_teams[3], item_chosen),
        menu_button(opposing_teams[4], item_chosen),
        menu_button(opposing_teams[5], item_chosen),
        menu_button(opposing_teams[6], item_chosen),
        menu_button(opposing_teams[7], item_chosen),
        menu_button(opposing_teams[8], item_chosen),
        menu_button(opposing_teams[9], item_chosen),
        menu_button(opposing_teams[10], item_chosen),
    ]),
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
    

top = CascadingBoxes(menu_top)

class Team:
    def __init__(self, teamName):
        # players
        self.name = teamName
        self.First = ""
        self.Second = ""
        self.Third = ""
        self.SS = ""
        self.inner = ""
        self.outer = ""
        self.OF = []*5
        self.util = ""
        self.Pitchers = []*9
        self.Bench = []*3

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

    def addPitcherToTeam(self,pitcher):
        self.IP = self.IP + pitcher.IP
        self.ER = self.ER + pitcher.ER
        self.Walks = self.Walks + pitcher.Walks
        self.PitcherHits = self.PitcherHits + pitcher.PitcherHits

        self.K = self.K + pitcher.K
        self.W = self.W + pitcher.W
        self.SV = self.SV + pitcher.SV

        self.ERA = (self.ER / self.IP) * 9
        self.WHIP = (self.Walks + self.PitcherHits) / self.IP

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

    def __init__(self, name, positions, K, W, SV, ER, IP, H, estPrice):
        self.Name = name
        self.Pos = positions
        self.K = K
        self.W = W
        self.SV = SV
        self.ER = ER
        self.IP = IP
        self.H = H
        self.Price = estPrice
        self.Team = ""


def buildTeam(team):
    

def main():
    # Clear screen
    urwid.MainLoop(top, palette=[('reversed', 'standout', '')]).run()

def addPlayerToTeam(player, team):
    if (player.Type == 'Pitcher'):
        team.addPitcherToTeam(player)
        for key in pitcher_tables:
            contains = pitcher_tables[key]['Name'].str.contains(player.Name)
            if (any(contains)):
                pitcher_tables[key].drop(index=pitcher_tables[key].index[contains].tolist()[0],inplace=True)
    else:
        team.addHitterToTeam(player);
        for key in hitter_tables:
            contains = hitter_tables[key]['Name'].str.contains(player.Name)
            if (any(contains)):
                hitter_tables[key].drop(index=hitter_tables[key].index[contains].tolist()[0],inplace=True)
    player.Team = team.Name


if __name__ == '__main__':
    main()
