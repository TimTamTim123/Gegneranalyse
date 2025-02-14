import pandas as pd #pip install pandas openpyxl
import streamlit as st #pip install streamlit
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title='Spielerdatenbank',
                   page_icon=":bowling:",
                   layout='wide')

#dataframe der Tabelle 'Eingabe'
def get_data_from_excel():
    df = pd.read_excel(io='Gegner_DB.xlsx', sheet_name='Datenbank',
                       usecols='A:L', header=0)
    df=df.reset_index(drop=True)
    df = df.drop(columns=['KW'])
    df=df[df.iloc[:,3].notna()&(df.iloc[:,3] !='')] #Lösche alle leeren Zeilen
    df['Name']=df['Name'].str.replace(r',\s*', ', ', regex=True) #passt alle Namen an die richtige Syntax an
    return df

df=get_data_from_excel()

#Sidebar

st.sidebar.header('Nutze folgende Filter:')

season = st.sidebar.multiselect('Wähle eine Saison:',
                              options=df['Saison'].unique(),
                              default=df['Saison'].unique()
                                                            )
if not season:
    season=df['Saison'].unique()

league= st.sidebar.multiselect('Wähle die Liga:',
                              options=df['Liga'].unique(),
                              default=df['Liga'].unique()
                              )
if not league:
    league=df['Liga'].unique()

wo= st.sidebar.multiselect('Wähle H/A:',
                              options=df['Wo'].unique(),
                              default=df['Wo'].unique()
                              )
if not wo:
    wo=df['Wo'].unique()


df_selection = df[df['Saison'].isin(season) & df['Liga'].isin(league) & df['Wo'].isin(wo)]
df_selection=df_selection.sort_values(by='Datum')
#Datums Umformungen
df_selection['Time']=(df_selection['Datum']-pd.Timestamp("2022-01-01"))// pd.Timedelta('1D')
df_selection['Datum']=df_selection['Datum'].dt.strftime("%d/%m/%Y")

#Unterfilter für die Teams der Liga
unique_teams=df_selection['Team'].unique()
team = st.sidebar.multiselect(
    'Wähle ein Team:',
    options=unique_teams,
    default=[unique_teams[0]]
)

# If no selection is made, default to the first team as well
if not team:
    team = [unique_teams[0]]

df_team = df_selection[df_selection['Team'].isin(team)]
df_team=df_team[df_team.iloc[:,3].notna()&(df_team.iloc[:,3] !=0)] #Lösche alle leeren Zeilen

#Unterfilter für die Personen des Teams
person=st.sidebar.multiselect('Wähle eine Person:',
                            options=df_team['Name'].unique(),
                            default=df_team['Name'].unique()
                            )
if not person:
    person=df_team['Name'].unique()

df_person = df_team[df_team['Name'].isin(person)]


# Mainpage

st.title(':eyes: Gegner Datenbank :eyes:')
st.markdown("##")

st.header("Übersicht-Tabelle :bowling:")
df_to_display=df_person.iloc[:, :-1]
st.dataframe(df_to_display)

st.markdown('---')

#Teamanalyse
team=team[0]
league_print=league[0]
st.header('Teamanalyse - ' + str(team) + ':bar_chart:')
#Erstelle den df für die Teamanalyse
analysis_team=pd.DataFrame({'Name':df_team['Name'].unique()})
analysis_team['Spiele']=np.nan
analysis_team['Schnitt']=np.nan
analysis_team['Streuung']=np.nan
analysis_team['MP']=np.nan
analysis_team['häufigste Position']=np.nan
analysis_team['Schnitt Hirschfeld']=np.nan
analysis_team['Trend 3 Spiele']=np.nan
analysis_team['Trend 5 Spiele']=np.nan
analysis_team['Trend gesamter Zeitraum']=np.nan
analysis_team['Bestes Spiel']=np.nan
analysis_team['Schlechtestes Spiel']=np.nan
num_rows=len(analysis_team)
#Gehe für jeden Namen die Eigenschaften durch
for j in range(num_rows):
    search_name=analysis_team.iat[j,0]
    analysis_team.loc[j, 'Schnitt'] = int(df_team.loc[df_selection['Name']==search_name, 'Ergebnis'].mean())
    analysis_team.loc[j, 'Streuung'] = '± ' + str(round(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].std(),0))
    analysis_team.loc[j, 'MP'] = str(round(df_team.loc[df_selection['Name'] == search_name, 'MP'].mean()*100,0)) + ' %'
    analysis_team.loc[j, 'Spiele'] = int(df_team['Name'].value_counts().get(search_name,0))
    analysis_team.loc[j, 'häufigste Position'] = int(df_team.loc[df_selection['Name'] == search_name, 'Position'].value_counts().idxmax())
    analysis_team.loc[j, 'Schnitt Hirschfeld'] = round(df_team.loc[(df_selection['Name'] == search_name) &
                                                                 (df_team['Ort'].str.contains('Hirschfeld', na=False)), 'Ergebnis'].mean(),0)
    analysis_team.loc[j, 'Bestes Spiel'] = int(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].max())
    analysis_team.loc[j, 'Schlechtestes Spiel'] = int(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].min())
    #Trend Berechnungen
    trend_person=df_team[df_team['Name'] == search_name][['Name', 'Ergebnis', 'Time']]
    trend_person['Time'] = pd.to_numeric(trend_person['Time'],errors='coerce')  # Will convert non-numeric values to NaN
    trend_person['Ergebnis'] = pd.to_numeric(trend_person['Ergebnis'], errors='coerce')
    trend_person=trend_person.sort_values(by='Time')
    trend_number=len(trend_person)
    if trend_number < 2:
        m=0
    else: m, b = np.polyfit(trend_person['Time'], trend_person['Ergebnis'], 1)
    analysis_team.loc[j, 'Trend gesamter Zeitraum'] = round(m * 7, 2)

    if trend_number < 3:
        n=m
    else: n, b = np.polyfit(trend_person['Time'].tail(3), trend_person['Ergebnis'].tail(3), 1)
    analysis_team.loc[j, 'Trend 3 Spiele'] = round(n * 7, 2)

    if trend_number < 5:
        q=m
    else: q, b = np.polyfit(trend_person['Time'].tail(5), trend_person['Ergebnis'].tail(5), 1)
    analysis_team.loc[j, 'Trend 5 Spiele'] = round(q * 7, 2)

analysis_team = analysis_team.sort_values(by='Schnitt', ascending=False)
analysis_team=analysis_team[~analysis_team['Name'].str.contains('/',na=False)] #Nimmt alle Spieler mit / raus

st.dataframe(analysis_team)


#Schnitt der Mannschaften
df_group = df[['Ort','Ergebnis']]
df_group['Ergebnis']=pd.to_numeric(df_group['Ergebnis'],errors='coerce')
df_group = round(df_group.groupby('Ort').mean(numeric_only=True),0)
schnitt_teams=df_group.loc[team,'Ergebnis']


#Schnitt der Mannschaft zu Hause
p6_group=df_team[['Datum','Ergebnis','Wo']]
p6_group=p6_group[~p6_group['Wo'].str.contains('A',na=False)]
p6_group['Ergebnis']=pd.to_numeric(p6_group['Ergebnis'],errors='coerce')
p6_group = p6_group.groupby('Datum').sum(numeric_only=True)
avg_Heimteam=round(p6_group['Ergebnis'].mean(),0)

st.subheader('Das Team - '+ str(team) +' - hat einen Heimschnitt von ' + str(avg_Heimteam) + ' bzw. ' + str(round(avg_Heimteam/6,0)) + ' pro Person.')
st. subheader('Beim Team - ' + str(team) + ' - spielen die Gegner im Schnitt ' + str(schnitt_teams*6)+ ' bzw. ' + str(schnitt_teams) + ' pro Person.')

st.subheader('Letzten Spiele:')
last_games=df_team[['Datum','Ergebnis','Ort','Wo','Time']]
last_games=last_games.groupby('Datum').agg({
    'Ergebnis':'sum',
    'Ort': 'first',
    'Time': 'first'
}).reset_index()

last_games=last_games.sort_values(by='Time',ascending=False)
last_games=last_games.iloc[:,:-1]
last_games=last_games.head(6)
st.dataframe(last_games)

st.markdown('---')

st.header('Ligaanalyse')
st.markdown('Das Diagram zeigt das durchschnittliche Ergebnis auf den Bahnen der Liga -' + str(league_print) +  '- an. Der rote Punkt gibt den Ligaschnitt an.')
st.markdown('Der blaue Punkt das durchschnittliche Ergebnis, was auf der Bahn erspielt wird.')
st.markdown('Der grüne Punkte zeigt an, wie ' + str(team) +  ' auf der Bahn gespielt hat.')

df_group=df_group.reset_index()
df_fig=df_group[df_group['Ort'].isin(unique_teams)] #suche die Teams der Liga und packe sie in einen df
league=league[0]
df_fig['Ligaschnitt']=round(df_selection.loc[df_selection['Liga']==league, 'Ergebnis'].mean(),0) #ermittle den Ligaschnitt der Liga
df_fig_size=len(df_fig)
df_fig=df_fig.reset_index(drop=True) #resette den Index damit die if Schleife laufen kann
for k in range(df_fig_size):
    game_ort=df_fig.iat[k,0]
    df_fig.loc[k,'Team']=round(df_team.loc[df_team['Ort']==game_ort,'Ergebnis'].mean(),0)

df_fig=df_fig.sort_values(by='Ergebnis',ascending=False)

#Diagramm ----------------------------------------------------------
fig = go.Figure()

# Add lines connecting 'Ligaschnitt' and 'Ergebnis' for each row
for idx, row in df_fig.iterrows():
    fig.add_trace(go.Scatter(
        x=[row['Ligaschnitt'], row['Ergebnis']],
        y=[row['Ort'], row['Ort']],
        mode='lines',
        line=dict(color='gray', width=2),
        showlegend=False
    ))

# Add markers for the 'Ligaschnitt' values
fig.add_trace(go.Scatter(
    x=df_fig['Ligaschnitt'],
    y=df_fig['Ort'],
    mode='markers',
    marker=dict(color='red', size=10),
    name='Ligaschnitt'
))

# Add markers for the 'Ergebnis' values
fig.add_trace(go.Scatter(
    x=df_fig['Ergebnis'],
    y=df_fig['Ort'],
    mode='markers',
    marker=dict(color='blue', size=10),
    name='Bahn-Schnitt',
    ))

#Add team marker
fig.add_trace(go.Scatter(
    x=df_fig['Team'],
    y=df_fig['Ort'],
    mode='markers',
    marker=dict(color='green', size=10),
    name='Team',
    ))

# Update layout for clarity
fig.update_layout(
    xaxis_title="Holz",
    yaxis_title="Ort",
    xaxis=dict(showgrid=True),
    yaxis=dict(autorange="reversed"),  # optional: reverse order of categories if desired
    template="plotly_white",
   )

st.plotly_chart(fig)

#other things to do:
#Überlegen, ob weitere Informationen nötig.