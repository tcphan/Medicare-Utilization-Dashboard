import pandas as pd
import numpy as np
from urllib.request import urlopen
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import plotly as pyo
import plotly.graph_objects as go
import plotly.express as px
#pip install newsapi-python
from newsapi import NewsApiClient
import requests

#******************************************************************************
#SECTION I: READ IN INPUT FILES
#******************************************************************************

#home health compare file
hha_filepath = r"C:\Users\tcphan\OneDrive\Documents\kaggle_projects\medicare_dashboard\data\HH_Provider_Oct2020.csv"
hha_df = pd.read_csv(hha_filepath)

#hospice compare file
hs_filepath = r"C:\Users\tcphan\OneDrive\Documents\kaggle_projects\medicare_dashboard\data\Hospice_Provider_Nov2020.csv"
hs_df = pd.read_csv(hs_filepath)

#hospital compare file
ho_filepath = r"C:\Users\tcphan\OneDrive\Documents\kaggle_projects\medicare_dashboard\data\Payment_and_Value_of_Care-Hospital.csv"
ho_df = pd.read_csv(ho_filepath)

#******************************************************************************
#SECTION II: DEFINE FORMATTING PARAMETERS
#******************************************************************************

#color parameters
primary_color = "#375A7F"
secondary_color = "#444"
success_color = "#00BC8C"
info_color = "#3498DB"
warning_color = "#F39C12"
danger_color = "#E74C3C"
light_color = "#ADB5BD"
dark_color = "#303030"

#------------------------------------------------------------------------------                                          
 
#summary metric options for choropleth map
choro_metrics = ["Total Number of Providers",
                 "% of Providers Offering Nursing Care Services",
                 "% of Providers Offering Physical Therapy Services",
                 "% of Providers Offering Occupational Therapy Services",
                 "% of Providers Offering Speech Pathology Services",
                 "% of Providers Offering Medical Social Services",
                 "% of Providers Offering Home Health Aide Services",
                 "Quality of Patient Care",
                 "Medicare Spending per Episode per Provider"]

#description of each summary metric
choro_metric_descrip = ["The total number of Home Health Agencies for each U.S state.",
                        "The percent of Home Health Agencies offering nursing care services in each U.S state.",
                        "The percent of Home Health Agencies offering physical therapy services in each U.S state.",
                        "The percent of Home Health Agencies offering occupational therapy services in each U.S state.", 
                        "The percent of Home Health Agencies offering speech pathology services in each U.S state.", 
                        "The percent of Home Health Agencies offering medical social services in each U.S state.", 
                        "The percent of Home Health Agencies offering home health aide services in each U.S state.",
                        "The average (mean) quality of patient care star rating.", 
                        "The average (mean) amount Medicare spends on an episode of care per home health agencies, compared to the Medicare spending across all agencies nationally"]

#match each metric with its corresponding description
choro_metric_dict = {i[0]: i[1] for i in zip(choro_metrics, choro_metric_descrip)}

#list of U.S states found in HHA dataset
hha_choro_states = hha_df["State"].dropna().unique()
len_states = len(hha_choro_states)
ncol_for_states = 5
nstates_per_col = int(len_states/ncol_for_states)

#list of ownership type
hha_ownership_types = hha_df["Type of Ownership"].dropna().unique()
#list of PPR performance category types
hha_ppr_types = hha_df["PPR Performance Categorization"].dropna().unique()


#list of metric associated with Offers... data columns
offer_metric_lst = ["Offers Nursing Care Services",
                    "Offers Physical Therapy Services",
                    "Offers Occupational Therapy Services",
                    "Offers Speech Pathology Services",
                    "Offers Medical Social Services",
                    "Offers Home Health Aide Services"]    

#list of dropdown menu options for the summary metric for the home health histogram plot
hh_hist_metrics = ["Quality of patient care star rating",
                   "How often the home health team began their patients' care in a timely manner",
                   "How often the home health team checked patients' risk of falling",
                   "How often the home health team checked patients for depression",
                   "How often the home health team determined whether patients received a flu shot for the current flu season",
                   "How often the home health team made sure that their patients received a pneumococcal vaccine (pneumonia shot)",
                   "With diabetes, how often the home health team got doctor's orders, gave foot care, and taught patients about foot care",
                   "How often patients got better at walking or moving around",
                   "How often patients got better at getting in and out of bed",
                   "How often patients got better at bathing",
                   "How often patients' breathing improved",
                   "How often patients' wounds improved or healed after an operation",
                   "How often patients got better at taking their drugs correctly by mouth",
                   "How often home health patients had to be admitted to the hospital",
                   "How often patients receiving home health care needed urgent, unplanned care in the ER without being admitted",
                   "Changes in skin integrity post-acute care: pressure ulcer/injury",
                   "How often physician-recommended actions to address medication issues were completely timely",
                   "How much Medicare spends on an episode of care at this agency, compared to Medicare spending across all agencies nationally"
                   ]

#list of dropdown menu options for the comparison type for the home health histogram plot
hh_hist_compare_type = ["State", "Type of Ownership", "PPR Performance Categorization"]

#------------------------------------------------------------------------------

#remove quotation marks and equal sign from CCN column
hs_df["CMS Certification Number (CCN)"] = hs_df["CMS Certification Number (CCN)"].str.replace('"', "")
hs_df["CMS Certification Number (CCN)"] = hs_df["CMS Certification Number (CCN)"].str.replace('=', "")

#list of US states for hospice content page
hs_states = hs_df["State"].dropna().unique()

#list of hospice measures
hs_measures = hs_df["Measure Name"].dropna().unique()

#list of starting years for hospice content page
hs_df["Start Date"] = pd.to_datetime(hs_df["Start Date"])
hs_start_years = hs_df["Start Date"].dt.year.unique()

#list of ending years for hospice content page
hs_df["End Date"] = pd.to_datetime(hs_df["End Date"])
hs_end_years = hs_df["End Date"].dt.year.unique()

#------------------------------------------------------------------------------

#list of US states for hospital content page
ho_states = ho_df["State"].dropna().unique()

#list of hospital measure names
ho_measures = ho_df["Payment Measure Name"].dropna().str.replace("Payment for ", "").str.replace("patients", "").str.strip().unique()
ho_measures = [msr.title() + " Measure" for msr in ho_measures]
 
#list of value categories
ho_val_cat = ho_df["Value of Care Category"].dropna().unique()
#list of payment categories
ho_pmt_cat = ho_df["Payment Category"].dropna().unique()

#list of possible news category
news_categories = ["Business", "Entertainment", "General", "Health", "Science", "Sports", "Technology"]

#list of possible news outlets
apikey = "2cab0d8e7b89467e9a953f33281425b5"
#apikey = "da8e2e705b914f9f86ed2e9692e66012"
newsapi = NewsApiClient(api_key = apikey)
news_sources = newsapi.get_sources()
news_outlets = [(i["id"], i["name"]) for i in news_sources["sources"]]

#******************************************************************************
#SECTION III: CLEAN/PROCESS INPUT FILES AND SUMMARY STATISTICS
#******************************************************************************

hha_summ_df_st = hha_df.groupby("State").aggregate({"CMS Certification Number (CCN)": "nunique", #total number of unique hha provider by state
                                                    "Quality of patient care star rating": "mean", #average patient star rating by state
                                                    "How much Medicare spends on an episode of care at this agency, compared to Medicare spending across all agencies nationally": "mean"}).reset_index()
#rename columns
hha_summ_df_st = hha_summ_df_st.rename(columns = {"CMS Certification Number (CCN)": "Total Number of Providers", 
                                                  "Quality of patient care star rating": "Quality of Patient Care",
                                                  "How much Medicare spends on an episode of care at this agency, compared to Medicare spending across all agencies nationally": "Medicare Spending per Episode per Provider"})
#round results
hha_summ_df_st["Quality of Patient Care"] = round(hha_summ_df_st["Quality of Patient Care"], 2)
hha_summ_df_st["Medicare Spending per Episode per Provider"] = round(hha_summ_df_st["Medicare Spending per Episode per Provider"], 2)

#loop through each column and calculate the percentage of providers in each state with Offers... equal to Yes
for off_val in offer_metric_lst:
    hha_df[off_val] = hha_df[off_val].map({"Yes": 1, "No": 0})
    inter_hha = hha_df.groupby("State").aggregate({off_val: "sum", "CMS Certification Number (CCN)": "nunique"}).reset_index()
    inter_hha["% of Providers Offering" + off_val.replace("Offers", "")] = round(inter_hha[off_val]/inter_hha["CMS Certification Number (CCN)"]*100, 1)
    if off_val == offer_metric_lst[0]:
        fin_offsumm_df = inter_hha[["State", "% of Providers Offering" + off_val.replace("Offers", "")]]
    else:
        fin_offsumm_df = pd.merge(fin_offsumm_df, inter_hha[["State", "% of Providers Offering" + off_val.replace("Offers", "")]], on = "State")
        
#merge results together
hha_summ_df_st = pd.merge(hha_summ_df_st, fin_offsumm_df, on = "State")

#******************************************************************************
#SECTION IV: DEFINE DASHBOARD
#******************************************************************************

#initialize dash application
app = dash.Dash(__name__, external_stylesheets = [dbc.themes.DARKLY])

#define sidebar
sidebar = html.Div(style = {"position": "fixed",
                            "top": 0,
                            "left": 0,
                            "bottom": 0,
                            "width": "25rem",
                            "padding": "2rem 1rem",
                            "textAlign": "left",
                            "backgroundColor": danger_color},
                    children = [
        
                        html.H3("Medicare Utilization Dashboard", style = {"fontWeight": "bold"}),
                        html.Hr(),
                        
                        html.H4("Overview:", style = {"fontWeight": "bold"}),
                        html.P("The following dashboard provides users the ability to explore various Medicare service utilization, beneficiaries, and provider metrics across different care settings."),
                        
                        html.H4("Care Settings:", style = {"fontWeight": "bold"}),
                        #define list of care delivery settings that users can navigate/select by in the sidebar
                        dbc.Nav(vertical = True,
                                pills = True,
                                children = [
                                        
                                            dbc.NavItem(children = dbc.NavLink(id = "ho_link",
                                                                               children = "Hospitals",
                                                                               href = "/hospitals",
                                                                               n_clicks = 0)),
                                                                 
                                            dbc.NavItem(children = dbc.NavLink(id = "hh_link",
                                                                               children = "Home Health Agencies",
                                                                               href = "/home-health-agencies",
                                                                               n_clicks = 0)),
                                                                    
                                            dbc.NavItem(children = dbc.NavLink(id = "hs_link",
                                                                               children = "Hospices",
                                                                               href = "/hospices",
                                                                               n_clicks = 0))
                                                                    
                                                                    
                                           ]),
                                            
                        html.Br(),
                        html.H4("Data Sources:", style = {"fontWeight": "bold"}),
                        #define list of data sources
                        dbc.Nav(vertical = True,
                                pills = True,
                                children = [
                                        
                                            dbc.NavItem(children = dbc.NavLink(id = "ho_source",
                                                                               children = "Hospital Compare Site",
                                                                               href = "https://data.cms.gov/provider-data/dataset/c7us-v4mf",
                                                                               target = "_blank",
                                                                               n_clicks = 0)),
                                                                 
                                            dbc.NavItem(children = dbc.NavLink(id = "hh_source",
                                                                               children = "Home Health Compare Site",
                                                                               href = "https://data.cms.gov/provider-data/dataset/6jpm-sxkc",
                                                                               target = "_blank",
                                                                               n_clicks = 0)),
                                                                    
                                            dbc.NavItem(children = dbc.NavLink(id = "hs_source",
                                                                               children = "Hospice Compare Site",
                                                                               href = "https://data.cms.gov/provider-data/dataset/252m-zfp9",
                                                                               target = "_blank",
                                                                               n_clicks = 0))
                                                                    
                                                                    
                                           ]),
                        
                        
                              ]) #end of sidebar

content_style = {"margin-left": "27rem", "margin-right": "2rem", "padding": "2rem 1rem"
                 }                            
#page content for home health
hh_page = html.Div(style = content_style,
                   children = [
                        
                        dbc.Card(children = [
                                    
                                    html.Div(style = {"display": "flex", "flexWrap": "wrap", "backgroundColor": danger_color},
                                             children = [
                                            
                                                #dropdown menu for choropleth metrics
                                                dbc.DropdownMenu(color = "danger",
                                                                 label = "Summary Metric",
                                                                 children = [dbc.DropdownMenuItem(id = "choro_metric"+str(mt_ind), children = mt_val, n_clicks = 0) for mt_ind, mt_val in enumerate(choro_metrics)]),
                                                
                                                #dropdown menu for U.S states
                                                dbc.DropdownMenu(color = "danger",
                                                                 label = "U.S State",
                                                                 children = [
                                                                              dbc.Row(style = {"width": "500px"},
                                                                                      children = [dbc.Col(width = {"size": 2, "order": 1},
                                                                                                          children = [dbc.DropdownMenuItem(id = "choro_stateall", children = "All", n_clicks = 0)])] +
                                                                                      
                                                                                                 [dbc.Col(width = {"size": 2, "order": i+2}, 
                                                                                                          children = [dbc.DropdownMenuItem(id = "choro_state"+st_val, children = st_val, n_clicks = 0)
                                                                                                          for st_val in hha_choro_states[nstates_per_col*i:nstates_per_col*(i+1)]])
                                                                                                  for i in range(ncol_for_states + (len_states%ncol_for_states))])
                                                                         
                                                                             ])
                                                
                                                        ]),
                                                                             
                                    dbc.CardBody(children = [
                                                             dbc.Row(children = [
                                                                     
                                                                                 #choropleth metric description and summary statistics
                                                                                 dbc.Col(width = {"size": 3, "order": 1},
                                                                                         children = [html.Div(id = "chorometric_descrip"),
                                                                                                     html.Div(id = "summ_box_top"),
                                                                                                     html.Div(id = "summ_box_bottom")
                                                                                                     ]),
    
                                                                                 #choropleth map of providers
                                                                                 dbc.Col(width = {"size": 9, "order": 2},
                                                                                         children = [dcc.Graph(id = "hh_choro_map")])
                                                                                         
                                                                                ])
                                                                     
                                                             ])
                        
                                            ]),
                                                                                 
                        html.Br(),                                                     
                    
                        dbc.Row(children = [
                                            dbc.Col(children = [
                                                                dbc.Card(style = {"width": "880px", "display": "inline-block"},
                                                                         children = [
                                                                                    dbc.CardBody(children = [
                                                                                                             dbc.Row(children = [
                                                                                                                                 
                                                                                                                                 dbc.Col(width = {"size": 3, "order": 1},
                                                                                                                                         children = [
                                                                                                                                                     #define the dropdown menu metric options for the home health histogram graph
                                                                                                                                                     dcc.Markdown("""**SELECT METRIC:**""", style = {"color": danger_color, "font-size": "12px"}),
                                                                                                                                                     dcc.Dropdown(id = "hist_metric_dp",
                                                                                                                                                                  style = {"color": "black", "width": "250px", "font-size": "12px"},
                                                                                                                                                                  optionHeight = 100,
                                                                                                                                                                  searchable = True,
                                                                                                                                                                  clearable = False,
                                                                                                                                                                  placeholder = "Summary Metric",
                                                                                                                                                                  value = hh_hist_metrics[0],
                                                                                                                                                                  options = [{"label": hist_val, "value": hist_val} for hist_val in hh_hist_metrics]),
                                                                                                                                                    
                                                                                                                                                    html.Br(),
                                                                                                                                                    
                                                                                                                                                    #define dropdown for the comparison variable type
                                                                                                                                                    dcc.Markdown("""**SELECT THE COMPARISON TYPE:**""", style = {"color": danger_color, "font-size": "12px"}),
                                                                                                                                                    dcc.Dropdown(id = "compare_type_dp",
                                                                                                                                                                 style = {"color": "black", "width": "250px", "font-size": "12px"},
                                                                                                                                                                 optionHeight = 35,
                                                                                                                                                                 searchable = True,
                                                                                                                                                                 clearable = False,
                                                                                                                                                                 placeholder = "Comparison Type",
                                                                                                                                                                 value = hh_hist_compare_type[0],
                                                                                                                                                                 options = [{"label": hist_val, "value": hist_val} for hist_val in hh_hist_compare_type]),
                                                                                                                                                    html.Br(),
                                                    
                                                                                                                                                    #define the compare versus dropdown menus
                                                                                                                                                    dcc.Markdown("""**SELECT THE COMPARISON GROUPS:**""", style = {"color": danger_color, "font-size": "12px"}),
                                                                                                                                                    dcc.Dropdown(id = "compare_grp1_dp",
                                                                                                                                                                 style = {"color": "black", "width": "250px", "font-size": "12px"},
                                                                                                                                                                 optionHeight = 50,
                                                                                                                                                                 searchable = True,
                                                                                                                                                                 clearable = False,
                                                                                                                                                                 placeholder = "Comparison Group 1"),
                                                                                                                                                    html.Br(),
                                                                                                                                                    dcc.Dropdown(id = "compare_grp2_dp", 
                                                                                                                                                                 style = {"color": "black", "width": "250px", "font-size": "12px"},
                                                                                                                                                                 optionHeight = 50,
                                                                                                                                                                 searchable = True,
                                                                                                                                                                 clearable = False,
                                                                                                                                                                 placeholder = "Comparison Group 2")
                                                                                                                                                    ]),
                                                                                                                                        
                                                                                                                                 dbc.Col(width = {"size": 8, "order": 2, "offset": 1},
                                                                                                                                         children = [dcc.Graph(id = "hh_histplot")]),
                                                                                                                                         
                                                                                                                     
                                                                                                                                ])
                                                                                            
                                                                                                            ])
                                                                            
                                                                                            ])
                                                                                                                                 
                                                            ]),
                                                                  
                                            dbc.Col(children = [
                                                                dbc.Card(style = {"width": "300px", "height": "365px"},
                                                                         color = "danger",
                                                                         children = [
                                                                                     dbc.CardBody(children = [
                                                                                                              dcc.Markdown("""**PERCENTILE DISTRIBUTION:**""", style = {"font-size": "16px"}),
                                                                                                              html.Div(id = "hist_summ_desc1"),
                                                                                                              html.Div(id = "hist_summ_box1"),
                                                                                                              html.Br(),
                                                                                                              html.Div(id = "hist_summ_desc2"),
                                                                                                              html.Div(id = "hist_summ_box2")
                                                                                                             ])
                                                                        
                                                                                    ])
                                                               ])
                              ])
    
                        ])
            


    
    
    
#page content for hospice
hs_page = html.Div(style = content_style, 
                   children = [
                           
                               dbc.Row(children = [
                                                   dbc.Col(width = {"size": 8, "order": 1},
                                                           children = [
                                                                       dbc.Card(style = {"width": "800px"},
                                                                                children = [
                                                                                            dbc.CardBody(children = [
                                                                                                                     dbc.Row(children = [
                                                                                                                                        dbc.Col(width = {"size": 3, "order": 1},
                                                                                                                                                children = [dcc.Markdown("""**TOP 10 RANKING HOSPICES:**""", style = {"color": danger_color}), 
                                                                                                                                                            html.Div(id = "top10_rank_tble")]),
    
                                                                                                                                        dbc.Col(width = {"size": 3, "order": 2, "offset": 2},
                                                                                                                                                children = [dcc.Markdown("""**BOTTOM 10 RANKING HOSPICES:**""", style = {"color": danger_color}),
                                                                                                                                                            html.Div(id = "last10_rank_tble")]),
    
                                                                                                                                        ])
                                                                                                                         
                                                                                                                    
                                                                                                                    
                                                                                                                    ])
                                                                                           ])
                                                                      ]),
    
                                                   dbc.Col(width = {"size": 4, "order": 2},
                                                           children = [dbc.Card(color = "danger",
                                                                                style = {"height": "425px"},
                                                                                children = [
                                                                                           dbc.CardBody(children = [
                                                                                                   
                                                                                                                    dcc.Markdown("""**INSTRUCTION:**"""),
                                                                                                                    dcc.Markdown("""Use the following parameters to filter the data by U.S state, quality measure, and study period.
                                                                                                                                    Results shown in ranking tables and bar graphs will update accordingly."""),
                                                                                                                    
                                                                                                                    
                                                                                                                    #define dropdown for U.S states
                                                                                                                    dcc.Markdown("""**SELECT U.S STATE:**"""),
                                                                                                                    dcc.Dropdown(id = "hs_states_dp",
                                                                                                                                 value = "All",
                                                                                                                                 style = {"color": "black", "width": "250px", "font-size": "12px", "display": "inline-block"},
                                                                                                                                 searchable = True,
                                                                                                                                 clearable = False,
                                                                                                                                 options = [{"label": "All", "value": "All"}] +
                                                                                                                                           [{"label": hs_opt, "value": hs_opt} for hs_opt in hs_states]),
                                                                                                                                 
                                                                                                                    html.Br(),
                                                                                                                    html.Br(),
                                                                                                                    
                                                                                                                    #define dropdown for quality measure type
                                                                                                                    dcc.Markdown("""**SELECT QUALITY MEASURE:**"""),
                                                                                                                    dcc.Dropdown(id = "hs_measures_dp",
                                                                                                                                 value = hs_measures[0],
                                                                                                                                 style = {"color": "black", "width": "250px", "font-size": "12px", "display": "inline-block"},
                                                                                                                                 searchable = True,
                                                                                                                                 clearable = False,
                                                                                                                                 optionHeight = 50,
                                                                                                                                 options = [{"label": hs_opt, "value": hs_opt} for hs_opt in hs_measures]),
                                                                                                                    
                                                                                                                    html.Br(),
                                                                                                                    html.Br(),
                                                                                                                    
                                                                                                                    #define the study period slider option
                                                                                                                    dcc.Markdown("""**SELECT STUDY PERIOD:**"""),
                                                                                                                    html.Div(style = {"width": "300px", "margin-left": "10px"}, 
                                                                                                                             children = [dcc.RangeSlider(id = "hs_yr_sl",
                                                                                                                                                         min = min(hs_start_years), 
                                                                                                                                                         max = max(hs_end_years),                
                                                                                                                                                         value = [min(hs_start_years), max(hs_end_years)],
                                                                                                                                                         marks = {hs_opt: {"label": hs_opt, "style": {"color": "white"}} for hs_opt in range(min(hs_start_years), max(hs_end_years)+1)})]) 
                                                                                                   
                                                                                                                   ])
                                                                                           ])
                                                           
                                                           
                                                                      ])
                                       
                                                  ]),
                               html.Br(),
                               
                               dbc.Row(children = [
                                                   #bar graph comparing state to national median/mean score
                                                   dbc.Col(width = {"size": 6, "order": 1},
                                                           children = [dbc.Card(children = [dbc.CardHeader(dbc.RadioItems(id = "hs_comp_rd",
                                                                                                                          value = "Mean",
                                                                                                                          inline = True,
                                                                                                                          options = [{"label": "Mean", "value": "Mean"},
                                                                                                                                     {"label": "Median", "value": "Median"}])),
                                                                                            dbc.CardBody(children = [dcc.Graph(id = "hs_msr_comp_bar")])])]),
                                                   
                                                   #bar graph comparing the median score among the top/bottom 5 ranking county
                                                   dbc.Col(width = {"size": 6, "order": 2},
                                                           children = [dbc.Card(children = [dbc.CardHeader(dbc.RadioItems(id = "hs_reg_rd", 
                                                                                                                          value = "Top 5",
                                                                                                                          inline = True,
                                                                                                                          options = [{"label": "Top 5", "value": "Top 5"},
                                                                                                                                     {"label": "Bottom 5", "value": "Bottom 5"}])),
    
                                                                                            dbc.CardBody(children = [dcc.Graph(id = "hs_reg_comp_bar")])])])
                                       
                                                  ])
                           
                              ])

    
    
    
#content page for hospitals
ho_page = html.Div(style = content_style,
                   children = [
                               dbc.Row(children = [
                                                  dbc.Col(children = [dbc.Card(children = [
                                                                                          #create dropdown allowings users to select the news outlet of interest
                                                                                          dbc.CardHeader(style = {"backgroundColor": danger_color},
                                                                                                         children = [dbc.Select(id = "news_outlet_sl",
                                                                                                                                style = {"display": "inline-block", "color": "black", "width": "200px", "font-size": "12px"},
                                                                                                                                options = [{"label": out_opt[1], "value": out_opt[0]} for out_opt in news_outlets],
                                                                                                                                value = news_outlets[0][0])
                                                                                                                     ]),
    
                                                                                          #output of top 5 most recent health related stories in the respective news outlet                                                  
                                                                                          dbc.CardBody(id = "top5news_by_cat"),
                                                                            
                                                                                          ]),
                                                                                            
                                                                    ]),        
                                                                                    
                                                  dbc.Col(children = [dbc.Card(children = [
                                                                                          #create input for news topic of interest
                                                                                          dbc.CardHeader(style = {"backgroundColor": danger_color},
                                                                                                         children = [dbc.Input(id = "news_topic_inp",
                                                                                                                               style = {"display": "inline-block", "width": "300px", "font-size": "12px"},
                                                                                                                               bs_size = "md",
                                                                                                                               placeholder = "Enter a news topic to search for."),
    
                                                          
                                                                                                                    ]),
    
                                                                                          #output of top 5 most recents stories  for the topic of interest
                                                                                          dbc.CardBody(id = "top5news_by_topic")
                                                                                          
                                                                                          ])
                                                                     ]),
                                                  ]),                                                         
                               
                               html.Br(),
                               
                               dbc.Row(children = [
                                                  dbc.Col(children = [
                                                                      dbc.Card(children = [
                                                                                          dbc.CardHeader(style = {"backgroundColor": danger_color},
                                                                                                         children = [
                                                                                                                      html.Div(style = {"display": "inline-block"},
                                                                                                                               children = [
                                                                                                                                          #list of states to choose from for hospital content pgae
                                                                                                                                          dcc.Dropdown(id = "ho_state_dp",
                                                                                                                                                       value = "All", 
                                                                                                                                                       searchable = True,
                                                                                                                                                       clearable = False,
                                                                                                                                                       style = {"color": "black", "width": "100px", "font-size": "12px"},
                                                                                                                                                       options = [{"label": "All", "value": "All"}] + [{"label": ho_st, "value": ho_st} for ho_st in ho_states]),
                                                                                                                                           ]),
                                                                                                                                                       
                                                                                                                      html.Div(style = {"width": "30px", "display": "inline-block"}),
                                                                                                                      
                                                                                                                      html.Div(style = {"display": "inline-block"},
                                                                                                                               children = [
                                                                                                                                           #list of measure options for the hospital content page          
                                                                                                                                           dcc.Dropdown(id = "ho_msr_dp",
                                                                                                                                                        value = ho_measures[0],
                                                                                                                                                        searchable = True,
                                                                                                                                                        clearable = False,
                                                                                                                                                        style = {"color": "black", "width": "250px", "font-size": "12px"},
                                                                                                                                                        options = [{"label": ho_msr, "value": ho_msr} for ho_msr in ho_measures])
                                                                                                                                            
                                                                                                                                          ])
                                                                                                                      
                                                                                                                     
                                                                                                                    ]),
                                                                                                                     
                                                                                         dbc.CardBody(children = [
                                                                                                                 dbc.Row(children = [
                                                                                                                                     #pie chart for hospital value
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 1}, children = dcc.Graph(id = "ho_value_pie")),
                                                                                                                                     #pie chart for hospital payment cost                                                                                                                                              
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 2}, children = dcc.Graph(id = "ho_cost_pie"))
                                                                                                                                    ]),
    
                                                                                                                 html.Br(),
                                                                                                                 
                                                                                                                 #selection menu for cost or value category of interest
                                                                                                                 dbc.Row(children = [
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 1}, 
                                                                                                                                             children = dbc.Select(id = "ho_val_sl",
                                                                                                                                                                   value = ho_val_cat[0],
                                                                                                                                                                   style = {"font-size": "10px"},
                                                                                                                                                                   options = [{"label": ho_cat, "value": ho_cat} for ho_cat in ho_val_cat])),
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 2}, 
                                                                                                                                             children = dbc.Select(id = "ho_pmt_sl", 
                                                                                                                                                                   value = ho_pmt_cat[0],
                                                                                                                                                                   style = {"font-size": "10px"},
                                                                                                                                                                   options = [{"label": ho_cat, "value": ho_cat} for ho_cat in ho_pmt_cat]))
                                                                                                                                     ]),
                                                                                                                
                                                                                                                html.Br(),
                                                                                                                
                                                                                                                dbc.Row(children = [
                                                                                                                                     #table summarizing hospitals with top hospital value
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 1},
                                                                                                                                             children = [dcc.Markdown("""TOP 5 HIGHEST STATE/CITY BY VALUE CATEGORY:""", style = {"font-size": "10px", "color": light_color}),
                                                                                                                                                         html.Div(id = "ho_value_tble")]),
                                                                                                                                     #table summarizing hospitals with hospital cost
                                                                                                                                     dbc.Col(width = {"size": 6, "order": 2},
                                                                                                                                             children = [dcc.Markdown("""TOP 5 HIGHEST STATE/CITY BY PAYMENT CATEGORY""", style = {"font-size": "10px", "color": light_color}),
                                                                                                                                                         html.Div(id = "ho_cost_tble")])
                                                                                                                                    ])
                                                                                                 
                                                                                                                 ])
                                                                              
                                                                              
                                                                                          ])
                                                          
                                                          
                                                                     ]) 
                                       
                                       
                                       
                                                  ])
        
        
        
                              ])


    
app.layout = html.Div(children = [
        
                        dcc.Location(id = "url", refresh = False),
                        sidebar,
                        html.Div(id = "page_content"),
                        
                        #empty container to hold selected input values to be passed into callbacks later on
                        html.Div(id = "hh_chorometric_input", hidden = True),
                        html.Div(id = "hh_chorostate_input", hidden = True)
        
                                 ]) #end of app.layout


#******************************************************************************
#SECTION V: DEFINE CALLBACKS
#******************************************************************************

#------------------------------------------------------------------------------
#CALLBACK APPLIED ACROSS CONTENT PAGES
#------------------------------------------------------------------------------

#callback to update the curretn url
@app.callback(Output(component_id = "url", component_property = "pathname"),
              [Input(component_id = "ho_link", component_property = "n_clicks"),
               Input(component_id = "hh_link", component_property = "n_clicks"),
               Input(component_id = "hs_link", component_property = "n_clicks")],
              [State(component_id = "ho_link", component_property = "href"),
               State(component_id = "hh_link", component_property = "href"),
               State(component_id = "hs_link", component_property = "href")])
def update_url_link(ho_nclicks, hh_nclicks, hs_nclicks, ho_ref, hh_ref, hs_ref):
    
    if (ho_nclicks == 0) and (hh_nclicks == 0) and (hs_nclicks == 0): new_link = "/"
    else:
        #update pathname based on the selected care setting 
        ctx = dash.callback_context    
        url_param = ctx.triggered[0]["prop_id"].split(".")[0]
        if (url_param == "ho_link"): new_link = ho_ref
        elif (url_param == "hh_link"): new_link = hh_ref
        elif (url_param == "hs_link"): new_link = hs_ref
    
    return new_link

#callback to update page content based on the selected care setting
@app.callback([Output(component_id = "page_content", component_property = "children"),
               Output(component_id = "ho_link", component_property = "active"),
               Output(component_id = "hh_link", component_property = "active"),
               Output(component_id = "hs_link", component_property = "active")],
              [Input(component_id = "url", component_property = "pathname")])
def return_content_page(pathname):

    if pathname == "/":
        return [ho_page, True, False, False]
    elif pathname == "/hospitals":
        return [ho_page, True, False, False]
    elif pathname == "/home-health-agencies":
        return [hh_page, False, True, False]
    elif pathname == "/hospices":
        return [hs_page, False, False, True]


#------------------------------------------------------------------------------
#FOR HOME HEALTH CONTENT PAGE
#------------------------------------------------------------------------------
        
#callback to return the value of the selected choropleth summary metric
@app.callback(Output(component_id = "hh_chorometric_input", component_property = "children"),
              [Input(component_id = "choro_metric"+str(mt_ind), component_property = "n_clicks") for mt_ind in range(len(choro_metrics))])
def get_chorometric_input(*args):
    ctx = dash.callback_context
    if (sum(args) == 0):
        return choro_metrics[0]
    else:
        #find the index associated with the selected metric option
        metric_ind = int(ctx.triggered[0]["prop_id"].split(".")[0].replace("choro_metric", ""))
        return choro_metrics[metric_ind]
    

#callback to return the value of the selected choropleth state
@app.callback(Output(component_id = "hh_chorostate_input", component_property = "children"),
              [Input(component_id = "choro_stateall", component_property = "n_clicks")] +
              [Input(component_id = "choro_state"+st_val, component_property = "n_clicks") for st_val in hha_choro_states])
def get_chorostate_input(*args):
    ctx = dash.callback_context
    if (sum(args) == 0):
        return "All"
    else:
        #find the index associated with the selected state option
        state_ind = ctx.triggered[0]["prop_id"].split(".")[0].replace("choro_state", "")
        if (state_ind == "all"):
            return "All"
        else:
            return state_ind
        

#callback to return the value of the possible dropdown options based on the selected comparison type in the home health histogram plot
@app.callback([Output(component_id = "compare_grp1_dp", component_property = "options"),
               Output(component_id = "compare_grp2_dp", component_property = "options"),
               Output(component_id = "compare_grp1_dp", component_property = "value"),
               Output(component_id = "compare_grp2_dp", component_property = "value")],
              [Input(component_id = "compare_type_dp", component_property = "value")])
def show_histgrp_options(compare_type):
    
    if compare_type == "State":
        options_lst = [{"label": st_val, "value": st_val} for st_val in hha_choro_states]
        grp1_val = hha_choro_states[0]
        grp2_val = hha_choro_states[1]
    elif compare_type == "Type of Ownership":
        options_lst = [{"label": owner_val, "value": owner_val} for owner_val in hha_ownership_types]
        grp1_val = hha_ownership_types[0]
        grp2_val = hha_ownership_types[1]
    elif compare_type == "PPR Performance Categorization": 
        options_lst = [{"label": ppr_val, "value": ppr_val} for ppr_val in hha_ppr_types]
        grp1_val = hha_ppr_types[0]
        grp2_val = hha_ppr_types[1]

    return options_lst, options_lst, grp1_val, grp2_val


#callback for return the description for each choropleth summary metric
@app.callback(Output(component_id = "chorometric_descrip", component_property = "children"),
              [Input(component_id = "hh_chorometric_input", component_property = "children")])
def show_chorometric_descrip(hh_chorometric):
    
    return [dcc.Markdown("""**SUMMARY METRIC:**""", style = {"color": danger_color, "font-size": "12px"}),
            dcc.Markdown("""{0}""".format(hh_chorometric), style = {"font-size": "12px"}),
            dcc.Markdown("""**DESCRIPTION:**""", style = {"color": danger_color, "font-size": "12px"}),
            dcc.Markdown("""{0}""".format(choro_metric_dict[hh_chorometric]), style = {"font-size": "12px"})]

#callback for returning the summary description and statistic in the bottom and top boxes to the left of the choropleth map
@app.callback([Output(component_id = "summ_box_top", component_property = "children"),
               Output(component_id = "summ_box_bottom", component_property = "children")],
              [Input(component_id = "hh_chorometric_input", component_property = "children"),
               Input(component_id = "hh_chorostate_input", component_property = "children")])
def show_sum_boxes(hh_chorometric, hh_chorostate):
    
    #determine whether to include a percent sign in shown results
    perc_sign = "%" if hh_chorometric in ["% of Providers Offering" + x.replace("Offers", "") for x in offer_metric_lst] else ""
    
    if hh_chorostate == "All":
    
        #find the state that has the highest value for the given metric. if there is a tie, then the first state in alphabetical order will be used
        max_ind = np.argwhere(hha_summ_df_st[hh_chorometric] == hha_summ_df_st[hh_chorometric].max())[0][0]
        max_state = hha_summ_df_st.loc[max_ind, "State"]
        max_val = hha_summ_df_st[hh_chorometric].max()
        
        #find the state that has the lowest value for the given metric. if there is a tien, then the first state in alphabetrical order wll be used
        min_ind = np.argwhere(hha_summ_df_st[hh_chorometric] == hha_summ_df_st[hh_chorometric].min())[0][0]
        min_state = hha_summ_df_st.loc[min_ind, "State"]
        min_val = hha_summ_df_st[hh_chorometric].min()
    
        #define the text to display
        box_top_text = [dcc.Markdown("""**STATE WITH HIGHEST VALUE:**""", style = {"color": danger_color, "font-size": "12px"}),
                        dcc.Markdown("""{0} ({1:,}{2})""".format(max_state, max_val, perc_sign), style = {"font-size": "12px"})]
        box_bottom_text = [dcc.Markdown("""**STATE WITH LOWEST VALUE:**""", style = {"color": danger_color, "font-size": "12px"}),
                           dcc.Markdown("""{0} ({1:,}{2})""".format(min_state, min_val, perc_sign), style = {"font-size": "12px"})]
            
    else:
        
        if (hh_chorometric == "Total Number of Providers"):
            
            #define the name of the table header
            table_header = [html.Thead(html.Tr([html.Th("Type of Ownership"), html.Th("# of Providers")]))]
    
            #count the number of providers by ownership type
            ownership_cnt = hha_df[hha_df["State"] == hh_chorostate]["Type of Ownership"].value_counts()
            body_lst = [html.Tr([html.Td(i), html.Td(ownership_cnt[i])]) for i in ownership_cnt.index]
            table_body = [html.Tbody(body_lst)]
            
            table = dbc.Table(table_header + table_body, bordered = True, size = "sm", style = {"font-size": "10px"})
            
            box_top_text = [dcc.Markdown("""**NUMBER OF PROVIDERS BY OWNERSHIP TYPE:**""", style = {"color": danger_color, "font-size": "12px"}),
                            table]
            
            box_bottom_text = ""
      
        elif (hh_chorometric in ["Quality of Patient Care", "Medicare Spending per Episode per Provider"]):
            
            if (hh_chorometric == "Quality of Patient Care"):
                varname = "Quality of patient care star rating"
            elif (hh_chorometric == "Medicare Spending per Episode per Provider"):
                varname = "How much Medicare spends on an episode of care at this agency, compared to Medicare spending across all agencies nationally"
            
            #filter to the specific state
            state_df = hha_df[hha_df["State"] == hh_chorostate]
            
            #find the provider CCN with the highest star rating
            max_val = state_df[varname].max()
            max_ind = np.argwhere(state_df[varname] == max_val)[0][0]
            max_ccn = state_df.iloc[max_ind]["CMS Certification Number (CCN)"]
            max_name = state_df.iloc[max_ind]["Provider Name"]
            box_top_text = [dcc.Markdown("""**PROVIDER WITH HIGHEST VALUE:**""", style = {"color": danger_color, "font-size": "12px"}),
                            dcc.Markdown("""{0} (CCN# {1}): {2}{3}""".format(max_name, str(max_ccn).zfill(5), max_val, perc_sign), style = {"font-size": "12px"})]
            
            #find the provider CCN with the lowest star rating
            min_val = state_df[varname].min()
            min_ind = np.argwhere(state_df[varname] == min_val)[0][0]
            min_ccn = state_df.iloc[min_ind]["CMS Certification Number (CCN)"]
            min_name = state_df.iloc[min_ind]["Provider Name"]
            box_bottom_text = [dcc.Markdown("""**PROVIDER WITH LOWEST VALUE:**""", style = {"color": danger_color, "font-size": "12px"}),
                               dcc.Markdown("""{0} (CCN# {1}): {2}{3}""".format(min_name, str(min_ccn).zfill(5), min_val, perc_sign), style = {"font-size": "12px"})]
            
        elif (hh_chorometric in ["% of Providers Offering" + x.replace("Offers", "") for x in offer_metric_lst]):
            
            #get the variable name in the hh dataset
            offer_ind = ["% of Providers Offering" + x.replace("Offers", "") for x in offer_metric_lst].index(hh_chorometric)
            varname = offer_metric_lst[offer_ind]
            
            #define the name of the table header
            table_header = [html.Thead(html.Tr([html.Th("Offers Services"), html.Th("# of Providers")]))]
            
            #count the number of providers by whether the provider does or does not offer a given service
            offer_cnt = hha_df[hha_df["State"] == hh_chorostate][varname].map({1: "Yes", 0: "No"}).value_counts()
            body_lst = [html.Tr([html.Td(i), html.Td(offer_cnt[i])]) for i in offer_cnt.index]
            table_body = [html.Tbody(body_lst)]
            
            table = dbc.Table(table_header + table_body, bordered = True, size = "sm", style = {"font-size": "10px"})
            
            box_top_text = [dcc.Markdown("""**NUMBER OF PROVIDERS BY SERVICE OFFERINGS:**""", style = {"color": danger_color, "font-size": "12px"}),
                            table]
            
            box_bottom_text = ""
            
    return box_top_text, box_bottom_text
    

#callback to render the choropleth map on the HHA tab
@app.callback(Output(component_id = "hh_choro_map", component_property = "figure"),
              [Input(component_id = "hh_chorometric_input", component_property = "children"),
               Input(component_id = "hh_chorostate_input", component_property = "children")])
def render_hh_choropleth(hh_chorometric, hh_chorostate):
    
    #if not All then subset to the relevant state
    plot_df = hha_summ_df_st if hh_chorostate == "All" else hha_summ_df_st[hha_summ_df_st["State"] == hh_chorostate]
    
    #define data parameters for choropleth figure
    hh_choro_data = [go.Choropleth(locations = plot_df["State"],
                                   locationmode = "USA-states",
                                   z = plot_df[hh_chorometric],
                                   colorscale = "Blues",
                                   marker_line_width = 0,
                                   colorbar = dict(title = dict(text = "<b>"+hh_chorometric+"</b>",
                                                                side = "right",
                                                                font = dict(size=10, color = "white")),
                                                   x = 0.95,
                                                   separatethousands = True,
                                                   showticklabels = True,
                                                   thickness = 10,
                                                   tickfont = dict(size = 8, color = "white"))
                                   )]
    #define layout parameters for choropleth figure
    hh_choro_layout = go.Layout(geo_scope = "usa",
                                geo = dict(bgcolor = dark_color, showlakes = False, showocean = False, showrivers = False),
                                paper_bgcolor = dark_color,
                                plot_bgcolor = dark_color,
                                margin = dict(l=0, r=0, b=0, t=0),
                                hoverlabel = {"font": {"size": 10}} #set the font size for text in hoverlabel         
                                )
    
    hh_choro_fig = go.Figure(data = hh_choro_data, layout = hh_choro_layout)
    
    hh_choro_fig.update_traces(customdata = np.stack((plot_df["State"], plot_df[hh_chorometric]), axis = -1),
                               hovertemplate = "<b>%{customdata[0]}:</b> %{customdata[1]:,}" +
                                               ("%" if hh_chorometric in ["% of Providers Offering" + x.replace("Offers", "") for x in offer_metric_lst] else "") +
                                               "<extra></extra>" #define formatting for hoverlabel
                               )
    
    #set to highlight only the selected state on the map
    if (hh_chorostate != "All"):
        hh_choro_fig.update_geos(fitbounds = "locations", visible = False)
        
    return hh_choro_fig

@app.callback([Output(component_id = "hh_histplot", component_property = "figure"),
               Output(component_id = "hist_summ_desc1", component_property = "children"),
               Output(component_id = "hist_summ_desc2", component_property = "children"),
               Output(component_id = "hist_summ_box1", component_property = "children"),
               Output(component_id = "hist_summ_box2", component_property = "children")],
              [Input(component_id = "hist_metric_dp", component_property = "value"),
               Input(component_id = "compare_type_dp", component_property = "value"), 
               Input(component_id = "compare_grp1_dp", component_property = "value"),
               Input(component_id = "compare_grp2_dp", component_property = "value")])
def render_hh_histplot(metric_type, compare_type, compare_grp1, compare_grp2):
    
    #filter to the respective comparison group
    metric_grp1 = hha_df[hha_df[compare_type] == compare_grp1][metric_type]
    metric_grp2 = hha_df[hha_df[compare_type] == compare_grp2][metric_type]
    
    #create histogram
    fig = go.Figure()
    fig.add_trace(go.Histogram(x = metric_grp1, name = compare_grp1, marker = {"color": "#776AC8"} ))
    fig.add_trace(go.Histogram(x = metric_grp2, name = compare_grp2, marker = {"color": "#E8A134"}))
    
    #overlay the two histograms
    fig.update_layout(barmode = "overlay",
                      margin = dict(l=10, r=5, b=10, t=10),
                      width = 550,
                      height = 325,
                      hoverlabel = {"font": dict(size=8)},
                      paper_bgcolor = dark_color,
                      plot_bgcolor = dark_color,
                      xaxis = {"linecolor": danger_color},
                      yaxis = {"title": "# of Providers", "gridcolor": danger_color},
                      font = {"size": 8},
                      font_color = light_color)
    #reduce the opacity of each histogram
    fig.update_traces(opacity = 0.75,
                      showlegend = False,
                      hovertemplate = "<b>Metric Value:</b> %{x}<br>" +
                                      "<b># of Providers:</b> %{y}")
    
    #define the table header
    table_header = [html.Thead(html.Tr([html.Th("MIN"), html.Th("25th"), html.Th("50th"), html.Th("75th"), html.Th("MAX")]))]
    #define the percentile values to be shown in table 1
    table1_row = html.Tr([html.Td(pval) for pval in metric_grp1.quantile([0, 0.25, 0.5, 0.75, 1])])
    table1_body = [html.Tbody([table1_row])]
    table1 = dbc.Table(table_header + table1_body, bordered = True, size = "sm")
    #define the percentile values to be shown in table 2
    table2_row = html.Tr([html.Td(pval) for pval in metric_grp2.quantile([0, 0.25, 0.5, 0.75, 1])])
    table2_body = [html.Tbody([table2_row])]
    table2 = dbc.Table(table_header + table2_body, bordered = True, size = "sm")
    
    desc1 = dcc.Markdown("""**""" + str(compare_grp1) + """:**""")
    desc2 = dcc.Markdown("""**""" + str(compare_grp2) + """:**""")
    
    return fig, desc1, desc2, table1, table2
    

#------------------------------------------------------------------------------
#FOR HOSPICE CONTENT PAGE
#------------------------------------------------------------------------------
       
#callback to return a table showing the top and bottom 10 ranking hospice providers
@app.callback([Output(component_id = "top10_rank_tble", component_property = "children"),
               Output(component_id = "last10_rank_tble", component_property = "children"),
               Output(component_id = "hs_msr_comp_bar", component_property = "figure"),
               Output(component_id = "hs_reg_comp_bar", component_property = "figure")],
              [Input(component_id = "hs_states_dp", component_property = "value"), 
               Input(component_id = "hs_measures_dp", component_property = "value"), 
               Input(component_id = "hs_yr_sl", component_property = "value"),
               Input(component_id = "hs_reg_rd", component_property = "value"),
               Input(component_id = "hs_comp_rd", component_property = "value")])
def create_rank_table(state, measure, year_range, rank5_opt, avg_type):
    
    #national hospice dataset containig providers from across all US states
    national_hs_df = hs_df[(hs_df["Measure Name"] == measure) & 
                           (hs_df["Start Date"].dt.year.between(year_range[0], year_range[1]))]
    
    if (state == "All"):
        #filter the hospice dataset based on the selected parameters
        filtered_hs_df = hs_df[(hs_df["Measure Name"] == measure) & 
                               (hs_df["Start Date"].dt.year.between(year_range[0], year_range[1]))]
        
    else:
        #filter the hospice dataset based on the selected parameters
        filtered_hs_df = hs_df[(hs_df["State"] == state) & 
                               (hs_df["Measure Name"] == measure) & 
                               (hs_df["Start Date"].dt.year.between(year_range[0], year_range[1]))]
        
    
    #remove records where score is not available from consideration
    filtered_hs_df = filtered_hs_df[filtered_hs_df["Score"] != "Not Available"] 
    national_hs_df = national_hs_df[national_hs_df["Score"] != "Not Available"]
    #convert to numeric data type
    filtered_hs_df["Score"] = pd.to_numeric(filtered_hs_df["Score"])
    national_hs_df["Score"] = pd.to_numeric(national_hs_df["Score"])
    
    #calculate the median/mean score for the filtered dataset
    filtered_df_median = filtered_hs_df.groupby(filtered_hs_df["Start Date"].dt.year).aggregate({"Score": avg_type.lower()}).reset_index()
    national_df_median = national_hs_df.groupby(national_hs_df["Start Date"].dt.year).aggregate({"Score": avg_type.lower()}).reset_index()
    
    #sort by score and obtain the top and bottom 10 rows
    filtered_hs_df = filtered_hs_df.sort_values(by = "Score", ascending = False)
    filtered_hs_df = filtered_hs_df.rename(columns = {"CMS Certification Number (CCN)": "CCN"})
    top10_rank = filtered_hs_df.head(10)[["CCN", "Facility Name", "Score"]]
    last10_rank = filtered_hs_df.tail(10)[["CCN", "Facility Name", "Score"]]
    
    #--------------------------------------------------------------------------
    
    #format the layout of rank tables
    top10_table = dbc.Table.from_dataframe(top10_rank,
                                           bordered = True,
                                           size = "sm", 
                                           style = {"font-size":"10px", "width": "300px"})
    last10_table = dbc.Table.from_dataframe(last10_rank,
                                            striped = True, 
                                            bordered = True,
                                            size = "sm", 
                                            style = {"font-size": "10px", "width": "300px"})
    
    #--------------------------------------------------------------------------
    
    #define the data for the bar charts
    filtered_df_msr_bar = go.Bar(x = filtered_df_median["Start Date"],
                                 y = filtered_df_median["Score"],
                                 marker = {"color": "#776AC8"},
                                 name = state,
                                 width = [0.3 for i in filtered_df_median["Start Date"]])
    national_df_msr_bar = go.Bar(x = national_df_median["Start Date"],
                                 y = national_df_median["Score"],
                                 marker = {"color": "#E8A134"},
                                 name = "National",
                                 width = [0.3 for i in national_df_median["Start Date"]])
    
    #define the layout for the bar graphs
    msr_layout = go.Layout(paper_bgcolor = dark_color,
                           plot_bgcolor = dark_color,
                           font_color = light_color,
                           bargroupgap = 0.1,
                           bargap = 0.3,
                           legend = dict(orientation = "h", yanchor = "middle", xanchor = "center", y = -0.15, x = 0.5),
                           font = {"size": 8},
                           title = {"text": "<b>COMPARISON OF STATE AND NATIONAL " + avg_type.upper() + " MEASURE SCORE:</b>",
                                    "font": {"color": danger_color, "size": 12}},
                           xaxis = {"linecolor": danger_color},
                           yaxis = {"title": avg_type + " Score", "gridcolor": danger_color})
        
    msr_data = [filtered_df_msr_bar, national_df_msr_bar]
    
    msr_figure = go.Figure(data = msr_data, layout = msr_layout)
    msr_figure.update_traces(hovertemplate = "<b>" + avg_type + ":</b> %{y}<extra></extra>")
    
    #--------------------------------------------------------------------------
    
    #calculate the median score by county
    filtered_df_reg = filtered_hs_df.groupby("County Name").aggregate({"CCN": "nunique", "Score": "median"}).reset_index()
    filtered_df_reg = filtered_df_reg.sort_values(by = "Score", ascending = False if rank5_opt == "Top 5" else True)
    #filter to the top or bottom 5 county
    rank5_reg = filtered_df_reg.head(5)
    
    #define the data format for the county comparison bar graph
    filtered_df_reg_bar = go.Bar(x = rank5_reg["County Name"],
                                 y = rank5_reg["Score"], 
                                 marker = {"color": "#3E84DF"})
    reg_data = [filtered_df_reg_bar]
    
    #define the layout for the county comparison bar graph
    reg_layout = go.Layout(paper_bgcolor = dark_color,
                           plot_bgcolor = dark_color,
                           font_color = light_color,
                           bargroupgap = 0.1,
                           bargap = 0.3,
                           font = {"size": 8},
                           title = {"text": "<b>COMPARISON OF MEASURE SCORE FOR TOP/BOTTOM 5 COUNTIES:</b>", 
                                    "font":{"color": danger_color, "size": 12}},
                           xaxis = {"linecolor": danger_color},
                           yaxis = {"title": "Median Score", "gridcolor": danger_color})
    
    reg_figure = go.Figure(data = reg_data, layout = reg_layout)
    reg_figure.update_traces(showlegend = False,
                             customdata = rank5_reg["CCN"],
                             hovertemplate = "<b># of CCNs:</b> %{customdata}<br>" +
                                             "<b>Median:</b> %{y}<extra></extra>")
    
    return top10_table, last10_table, msr_figure, reg_figure


#------------------------------------------------------------------------------
#FOR HOSPITAL CONTENT PAGE
#------------------------------------------------------------------------------

#create cost and value hospital pie charts
@app.callback([Output(component_id = "ho_value_pie", component_property = "figure"),
              Output(component_id = "ho_cost_pie", component_property = "figure"),
              Output(component_id = "ho_value_tble", component_property = "children"),
              Output(component_id = "ho_cost_tble", component_property = "children")],
              [Input(component_id = "ho_state_dp", component_property = "value"),
               Input(component_id = "ho_msr_dp", component_property = "value"),
               Input(component_id = "ho_val_sl", component_property = "value"),
               Input(component_id = "ho_pmt_sl", component_property = "value")])
def create_hospital_pies(state, measure, value_cat, pmt_cat):
    
    measure = measure.replace("Measure", "").strip().lower()
    
    #filter data to the appropriate state and measure of interest
    if state == "All":
        filtered_ho_df = ho_df[ho_df["Payment Measure Name"].str.contains(measure)]
    else:
        filtered_ho_df = ho_df[(ho_df["State"] == state) &
                               (ho_df["Payment Measure Name"].str.contains(measure))]
    
    #count the number of providers in each payment/value category
    nprov_by_pmt = filtered_ho_df.groupby("Payment Category").aggregate({"Facility ID": "nunique"}).reset_index()
    nprov_by_val = filtered_ho_df.groupby("Value of Care Category").aggregate({"Facility ID": "nunique"}).reset_index()

    #pie chart for value
    val_data = go.Pie(labels = nprov_by_val["Value of Care Category"],
                      values = nprov_by_val["Facility ID"],
                      hole = 0.5,
                      marker = dict(colors = px.colors.sequential.Blues))
    val_layout = go.Layout(title = {"text": "<b>% OF HOSPITALS BY VALUE CARE CATEGORY:</b>", "font": {"size": 12, "color": danger_color}},
                           legend = dict(orientation = "h", yanchor = "middle", xanchor = "center", y = -0.7, x = 0.5),
                           font = {"size": 8, "color": "white"},
                           paper_bgcolor = dark_color,
                           plot_bgcolor = dark_color,
                           margin = dict(l=0))
    val_fig = go.Figure(data = val_data, layout = val_layout)
    val_fig.update_traces(hoverlabel = {"font": {"size": 10}},
                          hovertemplate = "%{label}:<br>" +
                                          "# of Hospitals: %{value:,}<br>" +
                                          "% of Hospitals: %{percent}" +
                                          "<extra></extra>")

    #pie chart for payment
    pmt_data = go.Pie(labels = nprov_by_pmt["Payment Category"],
                      values = nprov_by_pmt["Facility ID"],
                      hole = 0.5,
                      marker = dict(colors = px.colors.sequential.Oryel))
    pmt_layout = go.Layout(title = {"text": "<b>% OF HOSPITALS BY PAYMENT CATEGORY:</b>", "font": {"size": 12, "color": danger_color}},
                           legend = dict(orientation = "h", yanchor = "middle", xanchor = "center", y = -0.7, x = 0.5),
                           font = {"size": 8, "color": "white"},
                           paper_bgcolor = dark_color,
                           plot_bgcolor = dark_color,
                           margin = dict(l=0))
    pmt_fig = go.Figure(data = pmt_data, layout = pmt_layout)
    pmt_fig.update_traces(hoverlabel = {"font": {"size": 10}},
                          hovertemplate = "%{label}:<br>" + 
                                          "# of Hospitals: %{value:,}<br>" +
                                          "% of Hospitals: %{percent}" + 
                                          "<extra></extra>")
    
    #--------------------------------------------------------------------------
    
    #count the number of providers by value care category and state/city
    nprov_by_val_st = filtered_ho_df.groupby(["Value of Care Category", "State" if state == "All" else "City"]).aggregate({"Facility ID": "nunique"}).reset_index()
    
    #sort the number of hospitals from highest to lowest for each value care category
    df = nprov_by_val_st[nprov_by_val_st["Value of Care Category"] == value_cat].sort_values(by = "Facility ID", ascending = False)
    #get the top 5 states with the highest number of hospitals
    df = df.head(5)
    df = df.rename(columns = {"Facility ID": "# of Hospitals"})
   
    #create data table
    val_table = dbc.Table.from_dataframe(df[["State" if state == "All" else "City", "# of Hospitals"]], 
                                        striped = True,
                                        bordered = True,
                                        hover = False,
                                        style = {"font-size": "10px"})
    
    
    #--------------------------------------------------------------------------

    #remove records where payment is not available
    costdf = filtered_ho_df[filtered_ho_df["Payment"] != "Not Available"]
    #convert text dollar string into integer amount
    costdf["Payment"] = costdf["Payment"].str.replace("$", "").str.replace(",", "").astype(int)
    #calculate the average payment amount by state
    costdf_by_pmt_st = costdf.groupby(["Payment Category", "State" if state == "All" else "City"]).aggregate({"Payment": "mean"}).reset_index()
    
    #sort states from highest to lowest based on average cost
    df = costdf_by_pmt_st[costdf_by_pmt_st["Payment Category"] == pmt_cat].sort_values(by = "Payment", ascending = False)
    #get the top 5 states with the highest cost
    df = df.head(5)
    df = df.rename(columns = {"Payment": "Avg Hospital Payment"})
    df["Avg Hospital Payment"] = df["Avg Hospital Payment"].apply(lambda x: "$ {0:,}".format(round(x,2)))
    #create data table
    cost_table = dbc.Table.from_dataframe(df[["State" if state == "All" else "City", "Avg Hospital Payment"]],
                                          striped = True,
                                          bordered = True,
                                          hover = False,
                                          style = {"font-size": "10px"})
 
    return val_fig, pmt_fig, val_table, cost_table


#callback to return news article from the specified news category and news outlet
@app.callback(Output(component_id = "top5news_by_cat", component_property = "children"),
              [Input(component_id = "news_outlet_sl", component_property = "value")])
def get_top5_news_by_cat(news_outlet):
    
    #pull all health related articles
    news_request = requests.get("https://newsapi.org/v2/top-headlines?country=us&category=health" + "&apiKey=" + apikey)
    news_data = pd.DataFrame(news_request.json()["articles"])
    news_data = news_data[["source", "title", "author", "publishedAt", "url"]]
    news_data["id"] = news_data["source"].str.get("id")
    news_data["name"] = news_data["source"].str.get("name")
        
    #subset to articles belonging to the specified news outlet
    news_data = news_data[news_data["id"] == news_outlet]
    
    #sort data from most recent to latest
    news_data["publishedAt"] = pd.to_datetime(news_data["publishedAt"])
    news_data = news_data.sort_values(by = "publishedAt", ascending = False)
    
    #keep only the top 5 articles
    news_data = news_data.head(5)
    
    #format into table
    table_header = [html.Thead(html.Tr([html.Th("Article Title"), html.Th("Author"), html.Th("Published Date")]))]
    table_body = [html.Tbody([html.Tr([html.Td(children = html.A(children = row["title"], href = row["url"], target = "_blank")), 
                                       html.Td(row["author"]),
                                       html.Td(row["publishedAt"])]) for index, row in news_data.iterrows()])]


    top5_table = dbc.Table(table_header + table_body, 
                           striped = True, 
                           bordered = True,
                           hover = False,
                           style = {"font-size": "10px"})
    
    #title for current table
    table_title = dcc.Markdown("""TOP 5 MOST RECENT HEALTH-RELATED NEW ARTICLES:""",
                               style = {"font-size": "10px", "color": light_color})
    
    return [table_title, html.Br(), top5_table]
    

#callback to return news articles that references the specified news topic
@app.callback(Output(component_id = "top5news_by_topic", component_property = "children"),
              [Input(component_id = "news_topic_inp", component_property = "value")])
def get_top5_news_by_inp(news_topic):
    
    if news_topic == None:
        
        news_data = pd.DataFrame({"Article Title": [], "Author": [], "Published Date": []})
        top5_table = dbc.Table.from_dataframe(news_data, 
                                              striped = True,
                                              bordered = True,
                                              hover = False,
                                              style = {"font-size": "10px"})
    
 
    else:
    
        #pull all article that references the specified input topic
        news_request = requests.get("https://newsapi.org/v2/everything?q=" + news_topic + "&apiKey=" + apikey)
        news_data = pd.DataFrame(news_request.json()["articles"])
        news_data = news_data[["title", "author", "publishedAt", "url"]]
        
        #sort data from most recent to latest
        news_data["publishedAt"] = pd.to_datetime(news_data["publishedAt"])
        news_data = news_data.sort_values(by = "publishedAt", ascending = False)
        
        #keep only the top 5 articles
        news_data = news_data.head(5)
        
        #format into table
        table_header = [html.Thead(html.Tr([html.Th("Article Title"), html.Th("Author"), html.Th("Published Date")]))]
        table_body = [html.Tbody([html.Tr([html.Td(children = html.A(children = row["title"], href = row["url"], target = "_blank")), 
                                           html.Td(row["author"]),
                                           html.Td(row["publishedAt"])]) for index, row in news_data.iterrows()])]
    
    
        top5_table = dbc.Table(table_header + table_body, 
                               striped = True, 
                               bordered = True,
                               hover = False,
                               style = {"font-size": "10px"})
        
    #title for current table
    table_title = dcc.Markdown("""TOP 5 MOST RECENT NEWS ARTICLES REFERENCING THE SPECIFIED TOPIC:""",
                               style = {"font-size": "10px", "color": light_color})

    return [table_title, html.Br(), top5_table]
 

if __name__ == "__main__":
    app.run_server(debug = False)
