#
# This is the user-interface definition of a Shiny web application. You can
# run the application by clicking 'Run App' above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(reticulate)
library(shinyWidgets)
library(tidyverse)

#conda_create(envname = "r-reticulate")
use_miniconda(condaenv = "r-reticulate", required=TRUE)
conda_install(envname="r-reticulate", packages=c("beautifulsoup4","requests","pandas","numpy","scikit-learn"))
system("python3 -m pip install -i https://pypi.gurobi.com gurobipy")
source_python("razzball_scraper.py")

opponents <- c()

#hitters <- read.csv("data/razzball-hitters.csv")
#pitchers <- read.csv("data/razzball-pitchers.csv")
#hitters <- unite(hitters, NamePos, c(Name, ESPN), remove=FALSE, sep="-")
#pitchers <- unite(pitchers, NamePos, c(Name, POS), remove=FALSE, sep="-")

#all_players <- c(hitters$NamePos, pitchers$NamePos)
all_players_picker <- c()

# Define server logic required to draw a histogram
server <- function(input, output, session) {
    RotisserieOptimizer <- import("RotisserieOptimizer")
    optimizer <- RotisserieOptimizer$Optimizer()
    all_players <- optimizer$get_all_players()
    #TODO: recombine players with multiple positions so they only show once here
    all_players <- all_players %>% group_by(Name) %>% summarise(POS = paste0(POS, collapse = "/"))
    all_players <- unite(all_players, NamePos, c(Name, POS), remove=FALSE, sep="-")
    all_players_picker <- all_players$NamePos
    updatePickerInput(session, "player", choices=all_players_picker)
    print(optimizer$get_budget("My Team"))
    output$budget <- renderUI(h5(sprintf("Budget: %d", optimizer$get_budget("My Team")[1]), class='budget'))
    
    observe({
        if (input$teamlist != "")
        {
            opponents <<- c(opponents, input$teamlist)
            updateCheckboxGroupInput(session, "teamchecks", choices=opponents)
            updateSearchInput(session, "teamlist", value="")
            updatePickerInput(session, "teamtoadd", choices=c(opponents,"My Team"))
            updatePickerInput(session, "teamToSee", choices=c(opponents,"My Team"))
            optimizer$add_team(input$teamlist)
        }
    })
    
    observeEvent(input$removeTeam, {
        opponents <<- opponents[! opponents %in% input$teamchecks]
        updateCheckboxGroupInput(session, "teamchecks", choices=opponents)
        updatePickerInput(session, "teamtoadd", choices=c(opponents,"My Team"))
        updatePickerInput(session, "teamToSee", choices=c(opponents,"My Team"))
        for (team in input$teamchecks)
        {
            optimizer$remove_team(team)
        }
    })
    
    observeEvent(input$submit, {
        player <- unlist(strsplit(input$player,"-"))[1]
        pos <- unlist(strsplit(input$player,"-"))[2]
        optimizer$add_player_to_team(player, input$teamtoadd, pos, input$price)
        all_players_picker <<- all_players_picker[all_players_picker != input$player]
        updatePickerInput(session, "player", choices=all_players_picker)
        bestTeam <- optimizer$build_team() %>% select('Name', 'POS', '$','R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K', 'ERA', 'WHIP','H','AB')
        output$topToAdd <- renderDataTable(bestTeam)
        output$budget <- renderUI(h5(sprintf("Budget: %d", optimizer$get_budget("My Team")[1]), class="budget"))
    })
    
    observeEvent(input$teamToSee,{
        output$draftedTeam <- renderDataTable(optimizer$print_team(input$teamToSee))
    })
    
    observeEvent(input$refreshPlayers,{
        bestTeam <- optimizer$build_team() %>% select('Name', 'POS', '$','R', 'HR', 'RBI', 'SB','adjAVG','W','SV','K', 'ERA', 'WHIP','H','AB')
        output$topToAdd <- renderDataTable(bestTeam)
    })
    
}

# Define UI for application
ui <- fluidPage(theme = "bootstrap.css",

    # Application title
    titlePanel(h1("DraftBot 3001", style = "font-family: 'Times New Roman';
        font-weight: 500; line-height: 1.1; 
        color: #4d3a7d;")),

    # Sidebar with a slider input for number of bins
    sidebarLayout(
        sidebarPanel(fluidRow(tabsetPanel(type="tabs",
                                   tabPanel("Settings", fluidPage(
                                       fluidRow(
                                           searchInput("teamlist", h3("Enter opposing teams"), btnSearch=icon("plus-square"))
                                       ),
                                       fluidRow(
                                           checkboxGroupInput("teamchecks","", choices=opponents)
                                       ),
                                       fluidRow(
                                           actionButton(inputId = "removeTeam", label="Remove selected teams")
                                       )
                                   )),
                                   tabPanel("Let's Draft!", fluidPage(
                                       fluidRow(
                                           pickerInput("player","Player to Add",all_players_picker),
                                       ),
                                       fluidRow(
                                           pickerInput("teamtoadd","Team to Add to",c(opponents,"My Team"))
                                       ),
                                       fluidRow(
                                           numericInput("price", "Price", 0)
                                       ),
                                       fluidRow(
                                           actionButton(inputId = "submit", label="Submit")
                                       ),
                                       fluidRow(
                                           uiOutput("budget")
                                       )
                                   ))
                                 )
                            ),
                     
        ),
        mainPanel(
            tabsetPanel(type="tabs",
                        tabPanel("Players to Add", fluidPage(
                            fluidRow(
                                actionButton(inputId = "refreshPlayers", label="", icon=icon('refresh'))
                            ),
                            fluidRow( # players to add
                                dataTableOutput("topToAdd")
                            ))
                        ),
                        tabPanel("View Teams",
                            fluidRow(
                                pickerInput("teamToSee", "View Team", c(opponents, "My Team"))
                            ),
                            fluidRow( # my team/opponents teams?
                                dataTableOutput("draftedTeam")
                            )
                        )
            )
        )
    )
)

shinyApp(ui = ui, server = server)