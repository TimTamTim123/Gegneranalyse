import pandas as pd #pip install pandas openpyxl
import streamlit as st #pip install streamlit
import plotly.express as px #pip install plotly-express
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title='Spielerdatenbank',
    page_icon=":bowling:",
    layout='wide')
tab1, tab2 = st.tabs(["Gegnerdatenbank", "Berechnungsprogramm"])

with tab1:



    # dataframe der Tabelle 'Eingabe'
    def get_data_from_excel():
        df_23 = pd.read_excel(io='Gegner_DB_23-24.xlsx', sheet_name='Datenbank',
                              usecols='A:L', header=0)
        df_24 = pd.read_excel(io='Gegner_DB_24-25.xlsx', sheet_name='Datenbank',
                              usecols='A:L', header=0)
        df_25 = pd.read_excel(io='Gegner_DB_25-26.xlsx', sheet_name='Datenbank',
                              usecols='A:L', header=0)
        df = pd.concat([df_23, df_24, df_25], ignore_index=True)
        df = df.reset_index(drop=True)
        df = df.drop(columns=['KW'])
        df = df[df.iloc[:, 3].notna() & (df.iloc[:, 3] != '')]  # Lösche alle leeren Zeilen
        df['Name'] = df['Name'].str.replace(r',\s*', ', ', regex=True)  # passt alle Namen an die richtige Syntax an
        df = df[~df['Name'].str.contains('/', na=False)]  # Nimmt alle Spieler mit / raus
        return df


    df = get_data_from_excel()

    # Sidebar

    st.sidebar.header('Nutze folgende Filter:')

    season = st.sidebar.multiselect('Wähle eine Saison:',
                                    options=df['Saison'].unique(),
                                    default='2024/2025'
                                    )
    if not season:
        season = df['Saison'].unique()

    league = st.sidebar.multiselect('Wähle die Liga:',
                                    options=df['Liga'].unique(),
                                    default=df['Liga'].unique()
                                    )
    if not league:
        league = df['Liga'].unique()

    df_selection = df[df['Saison'].isin(season) & df['Liga'].isin(league)]
    df_selection = df_selection.sort_values(by='Datum')
    # Datums Umformungen
    df_selection['Time'] = (df_selection['Datum'] - pd.Timestamp("2022-01-01")) // pd.Timedelta('1D')
    df_selection['Datum'] = df_selection['Datum'].dt.strftime("%d/%m/%Y")

    # Unterfilter für die Teams der Liga
    unique_teams = df_selection['Team'].unique()
    team = st.sidebar.multiselect(
        'Wähle ein Team:',
        options=unique_teams,
        default=[unique_teams[0]]
    )

    # If no selection is made, default to the first team as well
    if not team:
        team = [unique_teams[0]]

    wo = st.sidebar.multiselect('Wähle H/A:',
                                options=df['Wo'].unique(),
                                default=df['Wo'].unique()
                                )
    if not wo:
        wo = df['Wo'].unique()

    df_team = df_selection[df_selection['Team'].isin(team) & df_selection['Wo'].isin(wo)]
    df_team = df_team[df_team.iloc[:, 3].notna() & (df_team.iloc[:, 3] != 0)]  # Lösche alle leeren Zeilen

    # Unterfilter für die Personen des Teams
    person = st.sidebar.multiselect('Wähle eine Person:',
                                    options=df_team['Name'].unique(),
                                    default=df_team['Name'].unique()
                                    )
    if not person:
        person = df_team['Name'].unique()

    df_person = df_team[df_team['Name'].isin(person)]

    # Mainpage

    st.title(':eyes: Gegner Datenbank :eyes:')
    st.markdown("##")

    st.header("Übersicht-Tabelle :bowling:")
    df_to_display = df_person.iloc[:, :-1]
    st.dataframe(df_to_display)

    st.markdown('---')

    # Teamanalyse
    team = team[0]
    league_print = league[0]
    st.header('Teamanalyse - ' + str(team) + ':bar_chart:')
    # Erstelle den df für die Teamanalyse
    analysis_team = pd.DataFrame({'Name': df_team['Name'].unique()})
    analysis_team['Spiele'] = np.nan
    analysis_team['Schnitt'] = np.nan
    analysis_team['Streuung'] = np.nan
    analysis_team['MP'] = np.nan
    analysis_team['häufigste Position'] = np.nan
    analysis_team['Schnitt Hirschfeld'] = np.nan
    analysis_team['Trend 3 Spiele'] = np.nan
    analysis_team['Trend 5 Spiele'] = np.nan
    analysis_team['Trend gesamter Zeitraum'] = np.nan
    analysis_team['Bestes Spiel'] = np.nan
    analysis_team['Schlechtestes Spiel'] = np.nan
    num_rows = len(analysis_team)
    # Gehe für jeden Namen die Eigenschaften durch
    for j in range(num_rows):
        search_name = analysis_team.iat[j, 0]
        analysis_team.loc[j, 'Schnitt'] = int(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].mean())
        analysis_team.loc[j, 'Streuung'] = '± ' + str(
            round(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].std(), 0))
        analysis_team.loc[j, 'MP'] = str(
            round(df_team.loc[df_selection['Name'] == search_name, 'MP'].mean() * 100, 0)) + ' %'
        analysis_team.loc[j, 'Spiele'] = int(df_team['Name'].value_counts().get(search_name, 0))
        analysis_team.loc[j, 'häufigste Position'] = int(
            df_team.loc[df_selection['Name'] == search_name, 'Position'].value_counts().idxmax())
        analysis_team.loc[j, 'Schnitt Hirschfeld'] = round(df_team.loc[(df_selection['Name'] == search_name) &
                                                                       (df_team['Ort'].str.contains('Hirschfeld',
                                                                                                    na=False)), 'Ergebnis'].mean(),
                                                           0)
        analysis_team.loc[j, 'Bestes Spiel'] = int(df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].max())
        analysis_team.loc[j, 'Schlechtestes Spiel'] = int(
            df_team.loc[df_selection['Name'] == search_name, 'Ergebnis'].min())
        # Trend Berechnungen
        trend_person = df_team[df_team['Name'] == search_name][['Name', 'Ergebnis', 'Time']]
        trend_person['Time'] = pd.to_numeric(trend_person['Time'],
                                             errors='coerce')  # Will convert non-numeric values to NaN
        trend_person['Ergebnis'] = pd.to_numeric(trend_person['Ergebnis'], errors='coerce')
        trend_person = trend_person.sort_values(by='Time')
        trend_number = len(trend_person)
        if trend_number < 2:
            m = 0
        else:
            m, b = np.polyfit(trend_person['Time'], trend_person['Ergebnis'], 1)
        analysis_team.loc[j, 'Trend gesamter Zeitraum'] = round(m * 7, 2)

        if trend_number < 3:
            n = m
        else:
            n, b = np.polyfit(trend_person['Time'].tail(3), trend_person['Ergebnis'].tail(3), 1)
        analysis_team.loc[j, 'Trend 3 Spiele'] = round(n * 7, 2)

        if trend_number < 5:
            q = m
        else:
            q, b = np.polyfit(trend_person['Time'].tail(5), trend_person['Ergebnis'].tail(5), 1)
        analysis_team.loc[j, 'Trend 5 Spiele'] = round(q * 7, 2)

    analysis_team = analysis_team.sort_values(by='Schnitt', ascending=False)
    analysis_team = analysis_team[~analysis_team['Name'].str.contains('/', na=False)]  # Nimmt alle Spieler mit / raus

    st.dataframe(analysis_team)

    # Schnitt der Mannschaften
    df_group = df[['Ort', 'Ergebnis']]
    df_group['Ergebnis'] = pd.to_numeric(df_group['Ergebnis'], errors='coerce')
    df_group = round(df_group.groupby('Ort').mean(numeric_only=True), 0)
    schnitt_teams = df_group.loc[team, 'Ergebnis']

    # Schnitt der Mannschaft zu Hause
    p6_group = df_team[['Datum', 'Ergebnis', 'Wo']]
    p6_group = p6_group[~p6_group['Wo'].str.contains('A', na=False)]
    p6_group['Ergebnis'] = pd.to_numeric(p6_group['Ergebnis'], errors='coerce')
    p6_group = p6_group.groupby('Datum').sum(numeric_only=True)
    avg_Heimteam = round(p6_group['Ergebnis'].mean(), 0)

    st.subheader('Das Team - ' + str(team) + ' - hat einen Heimschnitt von ' + str(avg_Heimteam) + ' bzw. ' + str(
        round(avg_Heimteam / 6, 0)) + ' pro Person.')
    st.subheader(
        'Beim Team - ' + str(team) + ' - spielen die Gegner im Schnitt ' + str(schnitt_teams * 6) + ' bzw. ' + str(
            schnitt_teams) + ' pro Person.')

    st.subheader('Letzten Spiele:')
    last_games = df_team[['Datum', 'Ergebnis', 'Ort', 'Wo', 'Time']]
    last_games = last_games.groupby('Datum').agg({
        'Ergebnis': 'sum',
        'Ort': 'first',
        'Time': 'first'
    }).reset_index()

    last_games = last_games.sort_values(by='Time', ascending=False)
    last_games = last_games.iloc[:, :-1]
    last_games = last_games.head(6)
    st.dataframe(last_games)

    st.markdown('---')

    st.header('Ligaanalyse')
    st.markdown('Das Diagram zeigt das durchschnittliche Ergebnis auf den Bahnen der Liga -' + str(
        league_print) + '- an. Der rote Punkt gibt den Ligaschnitt an.')
    st.markdown('Der blaue Punkt das durchschnittliche Ergebnis, was auf der Bahn erspielt wird.')
    st.markdown('Der grüne Punkte zeigt an, wie ' + str(team) + ' auf der Bahn gespielt hat.')

    df_group = df_group.reset_index()
    df_fig = df_group[df_group['Ort'].isin(unique_teams)]  # suche die Teams der Liga und packe sie in einen df
    league = league[0]
    df_fig['Ligaschnitt'] = round(df_selection.loc[df_selection['Liga'] == league, 'Ergebnis'].mean(),
                                  0)  # ermittle den Ligaschnitt der Liga
    df_fig_size = len(df_fig)
    df_fig = df_fig.reset_index(drop=True)  # resette den Index damit die if Schleife laufen kann
    for k in range(df_fig_size):
        game_ort = df_fig.iat[k, 0]
        df_fig.loc[k, 'Team'] = round(df_team.loc[df_team['Ort'] == game_ort, 'Ergebnis'].mean(), 0)

    df_fig = df_fig.sort_values(by='Ergebnis', ascending=False)

    # Diagramm ----------------------------------------------------------
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

    # Add team marker
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

    st.markdown('---')


#Berechnungsprogramm

with tab2:
    st.header("Berechnungsprogramm 🖥️")
    st.write('In der Filterschablone am besten die aktuelle Saison wählen. '
             'Ist eine Liga im Filter ausgewählt, werden nur die Mannschaften der entsprechenden Liga angezeigt.')

    col1, col2= st.columns(2) #Erstelle 2 Spalten

    with col1:
        selected_hometeam = st.selectbox("Wähle eine Heimteam", unique_teams)
        df_selected_hometeam=df[df['Team']==selected_hometeam]
        df_selected_hometeam=df_selected_hometeam[~df_selected_hometeam['Name'].str.contains('/',na=False)]
        df_selected_hometeam=df_selected_hometeam[df_selected_hometeam['Wo']=='H']
        df_selected_hometeam['Time'] = (df_selected_hometeam['Datum'] - pd.Timestamp("2022-01-01")) // pd.Timedelta('1D')

        analysis_hometeam = pd.DataFrame({'Name': df_selected_hometeam['Name'].unique()})
        analysis_hometeam['Spiele'] = np.nan
        analysis_hometeam['Schnitt'] = np.nan
        analysis_hometeam['Streuung'] = np.nan
        analysis_hometeam['MP'] = np.nan
        analysis_hometeam['häufigste Position'] = np.nan
        analysis_hometeam['Trend 3 Spiele'] = np.nan
        num_rows = len(analysis_hometeam)
        for j in range(num_rows):
            search_name = analysis_hometeam.iat[j, 0]
            analysis_hometeam.loc[j, 'Schnitt'] =df_selected_hometeam.loc[df_selected_hometeam['Name'] == search_name, 'Ergebnis'].mean()
            analysis_hometeam.loc[j, 'Streuung'] = df_selected_hometeam.loc[df_selected_hometeam['Name'] == search_name, 'Ergebnis'].std()
            analysis_hometeam.loc[j, 'MP'] =df_selected_hometeam.loc[df_selected_hometeam['Name'] == search_name, 'MP'].mean()
            analysis_hometeam.loc[j, 'Spiele'] = df_selected_hometeam['Name'].value_counts().get(search_name, 0)
            analysis_hometeam.loc[j, 'häufigste Position'] =df_selected_hometeam.loc[df_selected_hometeam['Name'] == search_name, 'Position'].value_counts().idxmax()
            # Trend Berechnungen
            trend_person = df_selected_hometeam[df_selected_hometeam['Name'] == search_name][['Name', 'Ergebnis', 'Time']]
            trend_person['Time'] = pd.to_numeric(trend_person['Time'],
                                                 errors='coerce')  # Will convert non-numeric values to NaN
            trend_person['Ergebnis'] = pd.to_numeric(trend_person['Ergebnis'], errors='coerce')
            trend_person = trend_person.sort_values(by='Time')
            trend_number = len(trend_person)
            if trend_number < 3:
                n = m
            else:
                n, b = np.polyfit(trend_person['Time'].tail(3), trend_person['Ergebnis'].tail(3), 1)
            analysis_hometeam.loc[j, 'Trend 3 Spiele'] = n * 7
        analysis_hometeam = analysis_hometeam.sort_values(by='Spiele', ascending=False)
        st.write(analysis_hometeam[['Name','Spiele','Schnitt']])
        hometeamplayer1=  st.selectbox("Wähle Heimspieler:in 1",analysis_hometeam['Name'].unique(),index=0)
        hometeamplayer2 = st.selectbox("Wähle Heimspieler:in 2", analysis_hometeam['Name'].unique(),index=1)
        hometeamplayer3 = st.selectbox("Wähle Heimspieler:in 3", analysis_hometeam['Name'].unique(),index=2)
        hometeamplayer4 = st.selectbox("Wähle Heimspieler:in 4", analysis_hometeam['Name'].unique(),index=3)
        hometeamplayer5 = st.selectbox("Wähle Heimspieler:in 5", analysis_hometeam['Name'].unique(),index=4)
        hometeamplayer6 = st.selectbox("Wähle Heimspieler:in 6", analysis_hometeam['Name'].unique(),index=5)
        selected_homeplayer=[hometeamplayer1, hometeamplayer2, hometeamplayer3, hometeamplayer4, hometeamplayer5, hometeamplayer6]
        analysis_hometeam=analysis_hometeam[analysis_hometeam['Name'].isin(selected_homeplayer)]
        st.write(analysis_hometeam)

    with col2:
        selected_awayteam = st.selectbox("Wähle eine Auswärtsteam", unique_teams)
        selected_awayteam = df[df['Team'] == selected_awayteam]
        selected_awayteam = selected_awayteam[~selected_awayteam['Name'].str.contains('/', na=False)]
        selected_awayteam = selected_awayteam[selected_awayteam['Wo'] == 'A']
        selected_awayteam['Time'] = (selected_awayteam['Datum'] - pd.Timestamp("2022-01-01")) // pd.Timedelta(
            '1D')

        analysis_awayteam = pd.DataFrame({'Name': selected_awayteam['Name'].unique()})
        analysis_awayteam['Spiele'] = np.nan
        analysis_awayteam['Schnitt'] = np.nan
        analysis_awayteam['Streuung'] = np.nan
        analysis_awayteam['MP'] = np.nan
        analysis_awayteam['häufigste Position'] = np.nan
        analysis_awayteam['Trend 3 Spiele'] = np.nan
        num_rows = len(analysis_awayteam)
        for j in range(num_rows):
            search_name = analysis_awayteam.iat[j, 0]
            analysis_awayteam.loc[j, 'Schnitt'] = selected_awayteam.loc[
                selected_awayteam['Name'] == search_name, 'Ergebnis'].mean()
            analysis_awayteam.loc[j, 'Streuung'] = selected_awayteam.loc[
                selected_awayteam['Name'] == search_name, 'Ergebnis'].std()
            analysis_awayteam.loc[j, 'MP'] = selected_awayteam.loc[
                selected_awayteam['Name'] == search_name, 'MP'].mean()
            analysis_awayteam.loc[j, 'Spiele'] = selected_awayteam['Name'].value_counts().get(search_name, 0)
            analysis_awayteam.loc[j, 'häufigste Position'] = selected_awayteam.loc[
                selected_awayteam['Name'] == search_name, 'Position'].value_counts().idxmax()
            # Trend Berechnungen
            trend_person = selected_awayteam[selected_awayteam['Name'] == search_name][
                ['Name', 'Ergebnis', 'Time']]
            trend_person['Time'] = pd.to_numeric(trend_person['Time'],
                                                 errors='coerce')  # Will convert non-numeric values to NaN
            trend_person['Ergebnis'] = pd.to_numeric(trend_person['Ergebnis'], errors='coerce')
            trend_person = trend_person.sort_values(by='Time')
            trend_number = len(trend_person)
            if trend_number < 3:
                n = m
            else:
                n, b = np.polyfit(trend_person['Time'].tail(3), trend_person['Ergebnis'].tail(3), 1)
            analysis_awayteam.loc[j, 'Trend 3 Spiele'] = n * 7
        analysis_awayteam = analysis_awayteam.sort_values(by='Spiele', ascending=False)
        st.write(analysis_awayteam[['Name','Spiele','Schnitt']])
        awayteamplayer1 = st.selectbox("Wähle Auswärtsspieler:in 1", analysis_awayteam['Name'].unique(), index=0)
        awayteamplayer2 = st.selectbox("Wähle Auswärtsspieler:in 2", analysis_awayteam['Name'].unique(), index=1)
        awayteamplayer3 = st.selectbox("Wähle Auswärtsspieler:in 3", analysis_awayteam['Name'].unique(), index=2)
        awayteamplayer4 = st.selectbox("Wähle Auswärtsspieler:in 4", analysis_awayteam['Name'].unique(), index=3)
        awayteamplayer5 = st.selectbox("Wähle Auswärtsspieler:in 5", analysis_awayteam['Name'].unique(), index=4)
        awayteamplayer6 = st.selectbox("Wähle Auswärtsspieler:in 6", analysis_awayteam['Name'].unique(), index=5)
        selected_awayplayer = [awayteamplayer1, awayteamplayer2, awayteamplayer3, awayteamplayer4, awayteamplayer5,
                               awayteamplayer6]
        analysis_awayteam = analysis_awayteam[analysis_awayteam['Name'].isin(selected_awayplayer)]
        st.write(analysis_awayteam)

    st.markdown('---')

    #Berechnungs des Bahnenbonus

    selected_league=df.loc[df['Team']== selected_hometeam, 'Liga'].values[0]
    selected_league_average = df.loc[(df['Liga'] == selected_league) & (df['Wo'] == 'A'),'Ergebnis'].mean()
    selected_hometeam_average= df.loc[(df['Ort'] == selected_hometeam) & (df['Wo'] == 'A'),'Ergebnis'].mean()
    alley_bonus=round(selected_hometeam_average-selected_league_average,0)

    #Berechnungsprogramm
    st.write("Klicke hier um die Berechnung durchzuführen!")
    def run_my_program():
        st.write("🚀 Program is running!")
        # Lade Möglichkeiten
        SM = pd.read_excel('Spiele_Möglichkeiten.xlsx')
        N = SM.shape[0]  # Anzahl der Möglichkeiten
        n = 10000  # Umläufe

        # Lade die jeweiligen Daten der Spieler aus den Excel-Datein
        D_H =analysis_hometeam.drop(columns=['Spiele','MP','häufigste Position'])
        D_A =analysis_awayteam.drop(columns=['Spiele','MP','häufigste Position'])
        # Kombiniere die Daten
        D = pd.concat([D_H, D_A], axis=0)
        D = D.reset_index()
        D = D.drop('index', axis=1)

        # Leere Matrix der Ergebnisse
        E = np.zeros((N, 5))

        for z in range(N):
        # leerer Dataframe
            Z = np.zeros((n, 21))

        # Standartnormalverteilte Spalten mit dem Trend addiert
            for x in range(0, 6):
                Z[:, x] = (np.round(np.random.normal(loc=D.loc[x, 'Schnitt'], scale=D.loc[x, 'Streuung'], size=(n)), 0)
                       + D.loc[x, 'Trend 3 Spiele'] + np.random.randint(-10, 11))

            for x in range(6, 12):
                Z[:, x] = (np.round(np.random.normal(loc=D.loc[x, 'Schnitt'], scale=D.loc[x, 'Streuung'], size=(n)), 0)
                       + D.loc[x, 'Trend 3 Spiele'] + np.random.randint(-10, 11) + alley_bonus)

            # Gesamtholz der Teams:
            Z[:, 12] = Z[:, 0] + Z[:, 1] + Z[:, 2] + Z[:, 3] + Z[:, 4] + Z[:, 5]  # HSV
            Z[:, 13] = Z[:, 6] + Z[:, 7] + Z[:, 8] + Z[:, 9] + Z[:, 10] + Z[:, 11]  # GEG

            # Differenzen der Duelle und gleichzeitig die Anwendung der Sigunmsfunktion
            Z[:, 14] = np.sign(Z[:, SM.iloc[z, 1]] - Z[:, SM.iloc[z, 0]])  # Duell 1
            Z[:, 15] = np.sign(Z[:, SM.iloc[z, 3]] - Z[:, SM.iloc[z, 2]])  # Duell 2
            Z[:, 16] = np.sign(Z[:, SM.iloc[z, 5]] - Z[:, SM.iloc[z, 4]])  # Duell 3
            Z[:, 17] = np.sign(Z[:, SM.iloc[z, 7]] - Z[:, SM.iloc[z, 6]])  # Duell 4
            Z[:, 18] = np.sign(Z[:, SM.iloc[z, 9]] - Z[:, SM.iloc[z, 8]])  # Duell 5
            Z[:, 19] = np.sign(Z[:, SM.iloc[z, 11]] - Z[:, SM.iloc[z, 10]])  # Duell 6

            # Ersetze die Normale sign durch die MP 0, 0.5, 1
            Z_Duelle = Z[:, [14, 15, 16, 17, 18, 19, 20]]
            Z_Duelle[Z_Duelle == 0] = 0.5
            Z_Duelle[Z_Duelle == -1] = 0
            Z_Duelle[:, 6] = (Z_Duelle[:, 0] + Z_Duelle[:, 1] + Z_Duelle[:, 2] + Z_Duelle[:, 3] + Z_Duelle[:, 4]
                              + Z_Duelle[:, 5])  # Summe MP der Spieler
            # Addiere die Spieler MP mit den Summe MP
            Z[:, 20] = Z_Duelle[:, 6] + np.sign(Z[:, 12] - Z[:, 13]) + 1

            E[z, 0] = np.sum(Z[:, 20] > 4) / n * 100  # %WIN Heim
            E[z, 1] = np.sum(Z[:, 20] == 4) / n * 100  # %TIE
            E[z, 2] = np.sum(Z[:, 20] < 4) / n * 100  # %Win Auswärts
            E[z, 3] = round(np.mean(Z[:, 12]))  # Schnitt Heimteam
            E[z, 4] = round(np.mean(Z[:, 13]))  # Schnitt Gegnerteam


        # wandele E in Dataframe um und lass den Index von 1 Starten
        E = pd.DataFrame(E, columns=['Heimsieg (%)', 'Unentschieden (%)', 'Auswärtssieg (%)', 'Heim', 'Auswärts'])
        E.index = range(1, len(E) + 1)  # Index von 1 an
        E[['Heimsieg (%)', 'Unentschieden (%)', 'Auswärtssieg (%)']] = E[['Heimsieg (%)', 'Unentschieden (%)', 'Auswärtssieg (%)']].round(2)

        # ersetze die Zahlen der Aufstellungsmatrix durch die richtigen Namen
        NM = SM.astype(str)
        NM.index = range(1, len(NM) + 1)  # Index von 1 an

        for v in range(12):
            w = str(v + 1)
            NM = NM.replace(w, D.loc[v, 'Name'])

        # Kombiniere die beiden Dataframes
        result = pd.concat([E, NM], axis=1)
        result = result.sort_values(by='Heimsieg (%)', ascending=False)
        st.dataframe(result.reset_index(drop=True))



    # Button to trigger the program
    if st.button("Aufstellungsrechner"):
        run_my_program()

#other things to do:
#Überlegen, ob weitere Informationen nötig.