
import os
import json
import pandas as pd
import plotly.graph_objects as go
import re
from typing import List
import plotly.express as px
# solr library
import unidecode

# bing library for automation image
from bing_image_urls import bing_image_urls
from statsbombpy import sb
# streamlit libraries
import streamlit as st 
from streamlit_searchbox import st_searchbox

# cosine similarity libraries
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage


st.set_page_config(page_title="Player Scouting Recommendation System", layout="wide")
def home():
    st.title("Home")
    st.write("Welcome to the Home page!")

# Function to display the about page
def about():
    st.title("About")
    st.write("This is the About page.")

def player_scouting():
    st.markdown("<h1 style='text-align: center;'>Player Scouting Recommendation System</h1>", unsafe_allow_html=True)

    ############### Simple Search Engine with Auto-Complete Query Suggestion ##############
    press = False
    choice = None

    # Initialises the streamlit session state useful for page reloading
    if 'expanded' not in st.session_state:
        st.session_state.expanded = True

    if 'choice' not in st.session_state:
        st.session_state.choice = None

    # Carica i dati dal file CSV
    df_player = pd.read_csv('football-player-stats-2023.csv')


    def remove_accents(text: str) -> str:
        return unidecode.unidecode(text)

    def search_csv(searchterm: str) -> List[str]:
        if searchterm:
            normalized_searchterm = remove_accents(searchterm.lower())
            df_player['NormalizedPlayer'] = df_player['Player'].apply(lambda x: remove_accents(x.lower()))
            filtered_df = df_player[df_player['NormalizedPlayer'].str.contains(normalized_searchterm, case=False, na=False)]
            suggestions = filtered_df['Player'].tolist()
            return suggestions
        else:
            return []

    selected_value = st_searchbox(
        search_csv,
        key="csv_searchbox",
        placeholder="🔍 Search a Football Player"
    )

    st.session_state.choice = selected_value
    choice = st.session_state.choice

    ################### Organic result ###########################
    if choice:
        
        # Extract column names from the JSON result
        columns_to_process = list(df_player.columns)

        # Create a normalized copy of the player DataFrame
        df_player_norm = df_player.copy()

        # Define a custom mapping for the 'Pos' column
        custom_mapping = {
            'GK': 1,
            'DF,FW': 4,
            'MF,FW': 8,
            'DF': 2,
            'DF,MF': 3,
            'MF,DF': 5,
            'MF': 6,
            'FW,DF': 7,
            'FW,MF': 9,
            'FW': 10
        }

        # Apply the custom mapping to the 'Pos' column
        df_player_norm['Pos'] = df_player_norm['Pos'].map(custom_mapping)

        # Select a subset of features for analysis
        selected_features = ['Pos', 'Age', 'Int',
        'Clr', 'KP', 'PPA', 'CrsPA', 'PrgP', 'Playing Time MP',
        'Performance Gls', 'Performance Ast', 'Performance G+A',
        'Performance G-PK', 'Performance Fls', 'Performance Fld',
        'Performance Crs', 'Performance Recov', 'Expected xG', 'Expected npxG', 'Expected xAG',
        'Expected xA', 'Expected A-xAG', 'Expected G-xG', 'Expected np:G-xG',
        'Progression PrgC', 'Progression PrgP', 'Progression PrgR',
        'Tackles Tkl', 'Tackles TklW', 'Tackles Def 3rd', 'Tackles Mid 3rd',
        'Tackles Att 3rd', 'Challenges Att', 'Challenges Tkl%',
        'Challenges Lost', 'Blocks Blocks', 'Blocks Sh', 'Blocks Pass',
        'Standard Sh', 'Standard SoT', 'Standard SoT%', 'Standard Sh/90', 'Standard Dist', 'Standard FK',
        'Performance GA', 'Performance SoTA', 'Performance Saves',
        'Performance Save%', 'Performance CS', 'Performance CS%',
        'Penalty Kicks PKatt', 'Penalty Kicks Save%', 'SCA SCA',
        'GCA GCA', 
        'Aerial Duels Won', 'Aerial Duels Lost', 'Aerial Duels Won%',
        'Total Cmp', 'Total Att', 'Total Cmp', 'Total TotDist',
        'Total PrgDist', '1/3'
        ]



        ####################### Cosine Similarity #######################################

        # Normalization using Min-Max scaling
        scaler = MinMaxScaler()
        df_player_norm[selected_features] = scaler.fit_transform(df_player_norm[selected_features])

        # Calculate cosine similarity between players based on selected features
        similarity = cosine_similarity(df_player_norm[selected_features])

        # Find the Rk associated with the selected player's name
        index_player = df_player.loc[df_player['Player'] == choice, 'Rk'].values[0]

        # Calculate similarity scores and sort them in descending order
        similarity_score = list(enumerate(similarity[index_player]))
        similar_players = sorted(similarity_score, key=lambda x: x[1], reverse=True)

        # Create a list to store data of similar players
        similar_players_data = []

        # Loop to extract information from similar players
        for player in similar_players[1:11]:  # Exclude the first player (self)
            index = player[0]
            player_records = df_player[df_player['Rk'] == index]
            if not player_records.empty:
                player_data = player_records.iloc[0]  # Get the first row (there should be only one)
                similar_players_data.append(player_data)

        # Create a DataFrame from the data of similar players
        similar_players_df = pd.DataFrame(similar_players_data)

        ########################## Analytics of the player chosen ##########################
        # url_player = bing_image_urls(choice+ " "+df_player.loc[df_player['Player'] == choice, 'Squad'].iloc[0]+" 2023", limit=1, )[0]

        with st.expander("Features of The Player selected.", expanded=True):

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader(choice)
                # st.image(url_player, width=356)

            with col2:
                st.caption("📄 Information of Player")
                col_1, col_2, col_3 = st.columns(3)

                with col_1:
                    st.metric("Nation", df_player.loc[df_player['Player'] == choice, 'Nation'].iloc[0], None)
                    st.metric("Position", df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0], None)

                with col_2:
                    st.metric("Born", df_player.loc[df_player['Player'] == choice, 'Born'].iloc[0], None)
                    st.metric("Match Played", df_player.loc[df_player['Player'] == choice, 'Playing Time MP'].iloc[0], None, help="In 2022/2023")

                with col_3:
                    st.metric("Age", df_player.loc[df_player['Player'] == choice, 'Age'].iloc[0], None)

                st.metric(f"🏆 League: {df_player.loc[df_player['Player'] == choice, 'Comp'].iloc[0]}", df_player.loc[df_player['Player'] == choice, 'Squad'].iloc[0], None)

            with col3:
                st.caption("⚽ Information target of Player")
                # GK
                if df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "GK":
                        col_1, col_2 = st.columns(2)

                        with col_1:
                            st.metric("Saves", df_player.loc[df_player['Player'] == choice, 'Performance Saves'].iloc[0], None, help="Total number of saves made by the goalkeeper.")
                            st.metric("Clean Sheet", df_player.loc[df_player['Player'] == choice, 'Performance CS'].iloc[0], None, help="Total number of clean sheets (matches without conceding goals) by the goalkeeper.")

                        with col_2:
                            st.metric("Goals Against", df_player.loc[df_player['Player'] == choice, 'Performance GA'].iloc[0], None, help="Total number of goals conceded by the goalkeeper.")
                            st.metric("ShoTA", df_player.loc[df_player['Player'] == choice, 'Performance SoTA'].iloc[0], None, help="Total number of shots on target faced by the goalkeeper.")

                # DF
                if df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "DF" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "DF,MF" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "DF,FW":
                    col_1, col_2, col_3 = st.columns(3)

                    with col_1:
                        st.metric("Assist", df_player.loc[df_player['Player'] == choice, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the defender.")
                        st.metric("Goals", df_player.loc[df_player['Player'] == choice, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the defender.")

                    with col_2:
                        st.metric("Aerial Duel", df_player.loc[df_player['Player'] == choice, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the defender.")
                        st.metric("Tackle", df_player.loc[df_player['Player'] == choice, 'Tackles TklW'].iloc[0], None, help="Total number of successful tackles made by the defender in 2022/2023.")

                    with col_3:
                        st.metric("Interception", df_player.loc[df_player['Player'] == choice, 'Int'].iloc[0], None, help="Total number of interceptions made by the defender.")
                        st.metric("Key Passes", df_player.loc[df_player['Player'] == choice, 'KP'].iloc[0], None, help="Total number of key passes made by the defender.")

                # MF
                if df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "MF" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "MF,DF" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "MF,FW":
                    col_1, col_2, col_3 = st.columns(3)

                    with col_1:
                        st.metric("Assist", df_player.loc[df_player['Player'] == choice, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the player.")
                        st.metric("Goals", df_player.loc[df_player['Player'] == choice, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the player.")
                        st.metric("Aerial Duel", df_player.loc[df_player['Player'] == choice, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the player.")

                    with col_2:
                        st.metric("GCA", df_player.loc[df_player['Player'] == choice, 'GCA GCA'].iloc[0], None, help="Total number of goal-creating actions by the player.")
                        st.metric("Progressive PrgP", df_player.loc[df_player['Player'] == choice, 'Progression PrgP'].iloc[0], None, help="Total number of progressive passes by the player.")

                    with col_3:
                        st.metric("SCA", df_player.loc[df_player['Player'] == choice, 'SCA SCA'].iloc[0], None, help="Total number of shot-creating actions by the player.")
                        st.metric("Key Passes", df_player.loc[df_player['Player'] == choice, 'KP'].iloc[0], None, help="Total number of key passes by the player.")

                # FW
                if df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "FW" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "FW,MF" or df_player.loc[df_player['Player'] == choice, 'Pos'].iloc[0] == "FW,DF":
                    col_1, col_2, col_3 = st.columns(3) 

                    with col_1:
                        st.metric("Assist", df_player.loc[df_player['Player'] == choice, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the player.")
                        st.metric("Goals", df_player.loc[df_player['Player'] == choice, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the player.")
                        st.metric("Aerial Duel", df_player.loc[df_player['Player'] == choice, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the player.")

                    with col_2:
                        st.metric("SCA", df_player.loc[df_player['Player'] == choice, 'SCA SCA'].iloc[0], None, help="Total number of shot-creating actions by the player.")
                        st.metric("xG", df_player.loc[df_player['Player'] == choice, 'Expected xG'].iloc[0], None, help="Expected goals (xG) by the player.")
                        st.metric("xAG", df_player.loc[df_player['Player'] == choice, 'Expected xAG'].iloc[0], None, help="Expected assists (xAG) by the player.")

                    with col_3:
                        st.metric("GCA", df_player.loc[df_player['Player'] == choice, 'GCA GCA'].iloc[0], None, help="Total number of goal-creating actions by the player.")
                        st.metric("Key Passes", df_player.loc[df_player['Player'] == choice, 'KP'].iloc[0], None, help="Total number of key passes by the player.")

                                
                        
        ################# Radar and Rank ######################### 
        col1, col2 = st.columns([1.2, 2])

        with col1:
            ###### Similar Players Component ###############
            st.subheader(f'Similar Players to {choice}')
            # st.caption("This ranking list is determined through the application of a model based on **Cosine Similarity**. It should be noted that, being a ranking, the result obtained is inherently subjective.")
            selected_columns = ["Player", "Nation", "Squad", "Pos", "Age"]
            st.dataframe(similar_players_df[selected_columns], hide_index=True, use_container_width=True)

        with col2:
            ###### Radar Analytics #########################
            categories = ['Performance Gls', 'Performance Ast', 'KP', 'GCA GCA','Aerial Duels Won', 'Int', 'Tackles TklW', 'Performance Saves', 'Performance CS', 'Performance GA','Performance SoTA']
            selected_players = similar_players_df.head(10)

            fig = go.Figure()

            for index, player_row in selected_players.iterrows():
                player_name = player_row['Player']
                values = [player_row[col] for col in categories]
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=player_name
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                    )
                ),
                showlegend=True,  
                legend=dict(
                    orientation="v", 
                    yanchor="top",  
                    y=1,  
                    xanchor="left",  
                    x=1.02,  
                ),
                width=750,  
                height=520  
            )

            st.plotly_chart(fig, use_container_width=True)

        ####################### Scouter AI Component ##################################

        dis = True
        st.header('Player Finder AI')
        # message = f"Select the ideal characteristics for your team. Scouter AI will evaluate the most suitable player from the players most similar to **{choice}**"
        # st.caption(message)

        api_key = st.text_input("You need to enter the Open AI API Key:", placeholder="sk-...", type="password")
        os.environ['OPENAI_API_KEY'] = api_key

        if api_key:
            dis = False

        col1, col2 = st.columns([1, 2], gap="large")

        with col1:
            with st.form("my_form"):
                st.write("P R O M P T")
                # List of game styles and their descriptions
                game_styles = {
                    "Tiki-Taka": "This style of play, focuses on ball possession, control, and accurate passing.",
                    "Counter-Attack": "Teams adopting a counter-attacking style focus on solid defense and rapid advancement in attack when they regain possession of the ball.",
                    "High Press": "This style involves intense pressure on the opposing team from their half of the field. Teams practicing high pressing aim to quickly regain possession in the opponent's area, forcing mistakes under pressure.",
                    "Direct Play": "This style of play is more direct and relies on long and vertical passes, often targeting forwards or exploiting aerial play.",
                    "Pragmatic Possession": "Some teams aim to maintain ball possession as part of a defensive strategy, slowing down the game pace and limiting opponent opportunities.",
                    "Reactive": "In this style, a team adapts to the ongoing game situations, changing their tactics based on what is happening on the field. It can be used to exploit opponent weaknesses or respond to unexpected situations.",
                    "Physical and Defensive": "Some teams place greater emphasis on solid defense and physical play, aiming to frustrate opponents and limit their attacking opportunities.",
                    "Positional Play": "This style aims to dominate the midfield and create passing triangles to overcome opponent pressure. It is based on player positioning and the ability to maintain ball possession for strategic attacking.",
                    "Catenaccio": "This style, originating in Italy, focuses on defensive solidity and counterattacks. Catenaccio teams seek to minimize opponent scoring opportunities, often through zone defense and fast transition play.",
                    "Counter Attacking": "This style relies on solid defensive organization and quick transition to attack when the team regains possession of the ball. Forwards seek to exploit spaces left open by the opposing team during the defense-to-attack transition.",
                    "Long Ball": "This style involves frequent use of long and direct passes to bypass the opponent's defense. It relies on the physical strength of attackers and can be effective in aerial play situations."
                }

                # List of player experience levels
                player_experience = {
                    "Veteran": "A player with a long career and extensive experience in professional football. Often recognized for their wisdom and leadership on the field.",
                    "Experienced": "A player with experience, but not necessarily in the late stages of their career. They have solid skills and tactical knowledge acquired over time.",
                    "Young": "A player in the early or mid-career, often under 25 years old, with considerable development potential and a growing presence in professional football.",
                    "Promising": "A young talent with high potential but still needs to fully demonstrate their skills at the professional level."
                }

                # List of the leagues
                leagues = {
                    "Serie A": "Tactical and defensive football with an emphasis on defensive solidity and tactical play.",
                    "Ligue 1": "Open games with a high number of goals and a focus on discovering young talents.",
                    "Premier League": "Fast-paced, physical, and high-intensity play with a wide diversity of playing styles.",
                    "Bundesliga": "High-pressing approach and the development of young talents.",
                    "La Liga": "Possession of the ball and technical play with an emphasis on constructing actions."
                }

                # List of formations
                formations = ["4-3-1-2", "4-3-3", "3-5-2", "4-4-2", "3-4-3", "5-3-2", "4-2-3-1","4-3-2-1","3-4-1-2","3-4-2-1"]

                # List of player skills
                player_skills = [
                    "Key Passing", "Dribbling", "Speed", "Shooting", "Defending",
                    "Aerial Ability", "Tackling", "Vision", "Long Passing", "Agility", "Strength",
                    "Ball Control", "Positioning", "Finishing", "Crossing", "Marking",
                    "Work Rate", "Stamina", "Free Kicks", "Leadership","Penalty Saves","Reactiveness","Shot Stopping",
                    "Off the Ball Movement", "Teamwork", "Creativity", "Game Intelligence"
                ]

                ######### Inside FORM #####################
                st.subheader("Select a game style:")
                selected_game_style = st.selectbox("Choose a game style:", list(game_styles.keys()), disabled=dis)

                st.subheader("Select player type:")
                selected_player_experience = st.selectbox("Choose player type:", list(player_experience.keys()), disabled=dis)

                st.subheader("Select league:")
                selected_league = st.selectbox("Choose a league:", list(leagues.keys()), disabled=dis)

                st.subheader("Select formation:")
                selected_formation = st.selectbox("Choose a formation:", formations, disabled=dis)

                st.subheader("Select player skills:")
                selected_player_skills = st.multiselect("Choose player skills:", player_skills, disabled=dis)

                form = st.form_submit_button("➡️ Confirm features", disabled=dis)


        with col2:

            ######### Inside REPORT #####################
            st.info('The text is generated by a GPT-3.5 artificial intelligence model. Please note that the accuracy and veracity of the content may vary. \
                The primary goal is to provide general information and assistance in choosing a football player, but it is always recommended to verify and confirm any information from reliable sources.', icon="ℹ️")

            if form:
                st.caption("Selected Options:")
                st.write(f"You have chosen a game style: {selected_game_style}. {game_styles[selected_game_style]} \
                This player must be {selected_player_experience} and have a good familiarity with the {selected_formation} and the skills of: {', '.join(selected_player_skills)}.")

                template = (
                    """You are a soccer scout and you must be good at finding the best talents in your team starting from the players rated by the similar player system."""
                )
                system_message_prompt = SystemMessagePromptTemplate.from_template(template)

                human_template = """
                    Generate a Football Talent Scout report based on the DATA PROVIDED (maximum 250 words) written in a formal tone FOLLOWING THE EXAMPLE.
                    It is essential to compare player attributes and select the most suitable candidate from the available options from among similar players, based on the TEAM REQUIREMENTS provided. It is important to note that the selection of players is not limited to the ranking of the players provided, as long as they meet the TEAM REQUIREMENTS.
                    THE PLAYER CHOSEN MUST NECESSARILY BE AMONG THE POSSIBLE PLAYERS CONSIDERED IN THE FOOTBALL SCOUT REPORT.
                    INDICATE the player chosen at the end of the REPORT.

                    DATA:
                    ------------------------------------
                    {content}
                    ------------------------------------ 

                    TEAM REQUIREMENTS:
                    Style of play: {style_t}
                    Player type required: {type_player}
                    Preferred league: {league}
                    Key ability: {ability}
                    Ideal formation: {formation}

                    EXAMPLE TO FOLLOW:
                    ### Report
                    After a detailed analysis of the data, we have identified candidates who best meet the requirements of your team. Below, we present three potential candidates:

                    ##### Three potential candidates:

                    **[Player X]**: Highlights strengths and addresses weaknesses based on data on the essential attributes for a player in his specific age group.
                    **[Player Y]**: Highlights strengths and addresses weaknesses based on data regarding the attributes a player must necessarily possess in his specific age group.
                    **[Player Z]**: Highlighting strengths and addressing weaknesses based on attribute data that a player must necessarily possess in his specific age group.
                    
                    [Provide the reasons for choosing the recommended player over the others].
                    
                    The recommended player: Name of player recommended.
                    """

                human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

                st.caption("Text generated by Scouter AI:")
                with st.spinner("Generating text. Please wait..."):
                    llm = ChatOpenAI(temperature=0.1, model="gpt-3.5-turbo") 
                    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
                    result = llm(
                        chat_prompt.format_prompt(
                            player=choice, 
                            content=similar_players_df, 
                            style_t=game_styles[selected_game_style], 
                            type_player=player_experience[selected_player_experience], 
                            league=leagues[selected_league], 
                            ability=selected_player_skills, 
                            formation=selected_formation                    
                        ).to_messages()
                    )

                # Extract the last item in the list
                st.markdown(result.content)

                # Use a regular expression to find the name after "The recommended player: "
                pattern = r"The recommended player:\s*([^:]+)"

                # find the correspondence in the entire text
                matches = re.findall(pattern, result.content, re.IGNORECASE)
                if matches:
                    ultimo_nome = matches[0].rstrip('.')  # remove extra dot
                    if ultimo_nome.startswith('**') and ultimo_nome.endswith('**'):
                        ultimo_nome = ultimo_nome.strip('*')

        ####### Analytics of the recommended player ##############
        if form:  
            if matches:
                st.subheader("🌟 The features of the recommended player:")
                url_player = bing_image_urls(ultimo_nome+ " "+df_player.loc[df_player['Player'] == ultimo_nome, 'Squad'].iloc[0]+" 2023", limit=1, )[0]

                with st.expander("Selected Player", expanded=True):

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.subheader(ultimo_nome)
                            st.image(url_player, width=356)

                        with col2:
                            st.caption("📄 Information of Player")
                            col_1, col_2, col_3 = st.columns(3)

                            with col_1:
                                st.metric("Nation", df_player.loc[df_player['Player'] == ultimo_nome, 'Nation'].iloc[0], None)
                                st.metric("Position", df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0], None)

                            with col_2:
                                st.metric("Born", df_player.loc[df_player['Player'] == ultimo_nome, 'Born'].iloc[0], None)
                                st.metric("Match Played", df_player.loc[df_player['Player'] == ultimo_nome, 'Playing Time MP'].iloc[0], None, help="In 2022/2023")

                            with col_3:
                                st.metric("Age", df_player.loc[df_player['Player'] == ultimo_nome, 'Age'].iloc[0], None)

                            st.metric(f"🏆 League: {df_player.loc[df_player['Player'] == ultimo_nome, 'Comp'].iloc[0]}", df_player.loc[df_player['Player'] == ultimo_nome, 'Squad'].iloc[0], None)

                        with col3:
                            st.caption("⚽ Information target of Player")
                            # GK
                            if df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "GK":
                                    col_1, col_2 = st.columns(2)

                                    with col_1:
                                        st.metric("Saves", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Saves'].iloc[0], None, help="Total number of saves made by the goalkeeper.")
                                        st.metric("Clean Sheet", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance CS'].iloc[0], None, help="Total number of clean sheets (matches without conceding goals) by the goalkeeper.")

                                    with col_2:
                                        st.metric("Goals Against", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance GA'].iloc[0], None, help="Total number of goals conceded by the goalkeeper.")
                                        st.metric("ShoTA", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance SoTA'].iloc[0], None, help="Total number of shots on target faced by the goalkeeper.")

                            # DF
                            if df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "DF" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "DF,MF" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "DF,FW":
                                col_1, col_2, col_3 = st.columns(3)

                                with col_1:
                                    st.metric("Assist", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the defender.")
                                    st.metric("Goals", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the defender.")

                                with col_2:
                                    st.metric("Aerial Duel", df_player.loc[df_player['Player'] == ultimo_nome, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the defender.")
                                    st.metric("Tackle", df_player.loc[df_player['Player'] == ultimo_nome, 'Tackles TklW'].iloc[0], None, help="Total number of successful tackles made by the defender in 2022/2023.")

                                with col_3:
                                    st.metric("Interception", df_player.loc[df_player['Player'] == ultimo_nome, 'Int'].iloc[0], None, help="Total number of interceptions made by the defender.")
                                    st.metric("Key Passes", df_player.loc[df_player['Player'] == ultimo_nome, 'KP'].iloc[0], None, help="Total number of key passes made by the defender.")

                            # MF
                            if df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "MF" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "MF,DF" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "MF,FW":
                                col_1, col_2, col_3 = st.columns(3)

                                with col_1:
                                    st.metric("Assist", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the player.")
                                    st.metric("Goals", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the player.")
                                    st.metric("Aerial Duel", df_player.loc[df_player['Player'] == ultimo_nome, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the player.")

                                with col_2:
                                    st.metric("GCA", df_player.loc[df_player['Player'] == ultimo_nome, 'GCA GCA'].iloc[0], None, help="Total number of goal-creating actions by the player.")
                                    st.metric("Progressive PrgP", df_player.loc[df_player['Player'] == ultimo_nome, 'Progression PrgP'].iloc[0], None, help="Total number of progressive passes by the player.")

                                with col_3:
                                    st.metric("SCA", df_player.loc[df_player['Player'] == ultimo_nome, 'SCA SCA'].iloc[0], None, help="Total number of shot-creating actions by the player.")
                                    st.metric("Key Passes", df_player.loc[df_player['Player'] == ultimo_nome, 'KP'].iloc[0], None, help="Total number of key passes by the player.")

                            # FW
                            if df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "FW" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "FW,MF" or df_player.loc[df_player['Player'] == ultimo_nome, 'Pos'].iloc[0] == "FW,DF":
                                col_1, col_2, col_3 = st.columns(3) 

                                with col_1:
                                    st.metric("Assist", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Ast'].iloc[0], None, help="Total number of assists provided by the player.")
                                    st.metric("Goals", df_player.loc[df_player['Player'] == ultimo_nome, 'Performance Gls'].iloc[0], None, help="Total number of goals scored by the player.")
                                    st.metric("Aerial Duel", df_player.loc[df_player['Player'] == ultimo_nome, 'Aerial Duels Won'].iloc[0], None, help="Percentage of aerial duels won by the player.")

                                with col_2:
                                    st.metric("SCA", df_player.loc[df_player['Player'] == ultimo_nome, 'SCA SCA'].iloc[0], None, help="Total number of shot-creating actions by the player.")
                                    st.metric("xG", df_player.loc[df_player['Player'] == ultimo_nome, 'Expected xG'].iloc[0], None, help="Expected goals (xG) by the player.")
                                    st.metric("xAG", df_player.loc[df_player['Player'] == ultimo_nome, 'Expected xAG'].iloc[0], None, help="Expected assists (xAG) by the player.")

                                with col_3:
                                    st.metric("GCA", df_player.loc[df_player['Player'] == ultimo_nome, 'GCA GCA'].iloc[0], None, help="Total number of goal-creating actions by the player.")
                                    st.metric("Key Passes", df_player.loc[df_player['Player'] == ultimo_nome, 'KP'].iloc[0], None, help="Total number of key passes by the player.")

# Function to display the contact page
def contact():
    st.title("Contact")
    st.write("This is the Contact page.")
def match_explorer():
    st.title("Football Match Explorer")

    def create_football_pitch():
        fig = go.Figure()

        # Full pitch
        fig.add_shape(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white"), layer="below")

        # Left penalty area
        fig.add_shape(type="rect", x0=0, y0=22.3, x1=14.6, y1=57.6, line=dict(color="white"), layer="below")

        # Right penalty area
        fig.add_shape(type="rect", x0=105.4, y0=22.3, x1=120, y1=57.6, line=dict(color="white"), layer="below")

        # Center line
        fig.add_shape(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white"), layer="below")

        # Left goal area
        fig.add_shape(type="rect", x0=0, y0=32, x1=4.9, y1=48, line=dict(color="white"), layer="below")

        # Right goal area
        fig.add_shape(type="rect", x0=115.1, y0=32, x1=120, y1=48, line=dict(color="white"), layer="below")

        # Center circle
        fig.add_shape(type="circle", x0=50.9, y0=30.9, x1=69.1, y1=49.1, line=dict(color="white"), layer="below")

        # Center spot
        fig.add_shape(type="circle", x0=59.67, y0=39.67, x1=60.33, y1=40.33, fillcolor="white", line=dict(color="white"), layer="below")

        # Left penalty spot
        fig.add_shape(type="circle", x0=9.37, y0=39.67, x1=10.03, y1=40.33, fillcolor="white", line=dict(color="white"), layer="below")

        # Right penalty spot
        fig.add_shape(type="circle", x0=109.97, y0=39.67, x1=110.63, y1=40.33, fillcolor="white", line=dict(color="white"), layer="below")

        # Left arc
        fig.add_shape(type="path",
                    path="M 9.7 48.1 A 8.1 8.1 0 0 0 9.7 31.9",
                    line=dict(color="white"), layer="below")

        # Right arc
        fig.add_shape(type="path",
                    path="M 110.3 31.9 A 8.1 8.1 0 0 1 110.3 48.1",
                    line=dict(color="white"), layer="below")

        # Set axis limits
        fig.update_xaxes(range=[0, 120], visible=False)
        fig.update_yaxes(range=[0, 80], visible=False)

        return fig
    # Function to plot events on the football pitch
    def plot_events(fig, events, event_type):
        event_data = events[events['type'] == event_type]
        
        fig.add_trace(
            go.Scatter(
                x=event_data['location_x'],
                y=event_data['location_y'],
                mode='markers',
                marker=dict(size=10, symbol="circle", line=dict(color='black', width=1), color='white'),
                text=event_data['player'],
                name=event_type
            )
        )
    # Function to display player positions
    def plot_shots(fig, shots):
        for _, shot in shots.iterrows():
            marker_symbol = 'star' if shot['shot_outcome'] == 'Goal' else 'circle'
            # marker_size = max(shot['shot_statsbomb_xg'] * 20, 15)  # Scaling xG for marker size
            player_name = shot['player'].split()[-1] if shot['shot_outcome'] == 'Goal' else ""

            fig.add_trace(
                go.Scatter(
                    x=[shot['location_x']],
                    y=[shot['location_y']],
                    mode='markers+text' if shot['shot_outcome'] == 'Goal' else 'markers',
                    marker=dict(
                        size=10,
                        symbol=marker_symbol,
                        color=shot['team_color'],
                        line=dict(color='white', width=0.5)
                    ),
                    text=[player_name],
                    textposition="top center",
                    name='Shot'
                )
            )
    # Function to get competition data and create filters
    def get_competitions():
        competitions = sb.competitions()
        competition_options = competitions[['competition_name', 'competition_id']].drop_duplicates()
        return competition_options

    # Function to get season data based on selected competition
    def get_seasons(competition_id):
        competitions = sb.competitions()
        seasons = competitions[competitions['competition_id'] == competition_id][['season_name', 'season_id']].drop_duplicates()
        return seasons
    def get_matches(competition_id, season_id):
        matches = sb.matches(competition_id=competition_id, season_id=season_id)
        match_options = matches[['home_team', 'away_team', 'match_id']]
        match_options['match'] = match_options['home_team'] + " vs " + match_options['away_team']
        return match_options

    # Function to display match events
    def display_match_events(match_id):
        events = sb.events(match_id=match_id)
        return events

    # Function to create event summary
    def create_event_summary(events):
        # Group by event type and team name, then count the occurrences
        event_summary = events.groupby(['type', 'team'])['id'].count().unstack(fill_value=0)
        event_summary.columns.name = "Team"
        event_summary.reset_index(inplace=True)
        event_summary.rename(columns={"type": "Event Type"}, inplace=True)
        
        return event_summary

    # Function to create a player event bar chart for a specific team
    def create_player_event_barchart(events, selected_event_type, team_name, color):
        # Filter events based on selected event type and team
        if selected_event_type:
            events = events[(events['type'] == selected_event_type) & (events['team'] == team_name)]
        
        # Group by player to count events
        player_events = events.groupby(['player'])['id'].count().reset_index()
        
        fig = px.bar(
            player_events, 
            x='id', 
            y='player', 
            orientation='h', 
            text='id',
            title=f"{team_name}",
            color_discrete_sequence=[color]
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside', textfont=dict(color='white'))
        fig.update_layout(
            xaxis_title=None, 
            yaxis_title=None, 
            showlegend=False,
            xaxis_showticklabels=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # Streamlit App Structure

    st.sidebar.title("Football Match Explorer")

    # Competition Filter
    competition_df = get_competitions()
    competition_choice = st.sidebar.selectbox("Select Competition", competition_df['competition_name'])
    selected_competition_id = competition_df[competition_df['competition_name'] == competition_choice]['competition_id'].values[0]

    # Season Filter
    season_df = get_seasons(selected_competition_id)
    season_choice = st.sidebar.selectbox("Select Season", season_df['season_name'])
    selected_season_id = season_df[season_df['season_name'] == season_choice]['season_id'].values[0]

    # Match Filter
    match_df = get_matches(selected_competition_id, selected_season_id)
    match_choice = st.sidebar.selectbox("Select Match", match_df['match'])
    selected_match_id = match_df[match_df['match'] == match_choice]['match_id'].values[0]

    # Display Match Events
    st.header(f"Match Events: {match_choice}")
    events = display_match_events(selected_match_id)
    events['location_x'] = events['location'].apply(lambda loc: loc[0] if isinstance(loc, (list, tuple)) else None)
    events['location_y'] = events['location'].apply(lambda loc: loc[1] if isinstance(loc, (list, tuple)) else None)


    # Create Event Summary
    event_summary = create_event_summary(events)


    # Scrollable Event Summary Table
    st.subheader("Event Summary")
    st.dataframe(event_summary, use_container_width=True, height=400)
    
    # Layout: Event Selection Dropdown and Two Columns for Bar Charts
    selected_event_type = st.selectbox("Select Event Type", event_summary['Event Type'].unique())

    # Get team names
    home_team = match_df['home_team'].iloc[0]
    away_team = match_df['away_team'].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        create_player_event_barchart(events, selected_event_type, home_team, color='blue')

    with col2:
        create_player_event_barchart(events, selected_event_type, away_team, color='green')
    
    st.subheader("Event Maps")
    fig = create_football_pitch()
    fig.update_layout(
        width=800,
        height=800 * 80 / 120,  # Adjust height to maintain aspect ratio
        showlegend=False,
        plot_bgcolor='green',
        margin=dict(l=0, r=0, t=0, b=0)
    )
        # Display the football pitch with events
    event_type = st.selectbox("Select Event Type", events['type'].unique())
    plot_events(fig, events, event_type)
    st.plotly_chart(fig)

    st.subheader("Shot Maps")
    shots = events[events['type'] == 'Shot']
    unique_teams = shots['team'].unique()
    team_colors = {unique_teams[0]: 'red', unique_teams[1]: 'blue'}
    shots['team_color'] = shots['team'].map(team_colors)



    # Filter shots by selected team
    home_team_shots = shots[shots['team'] == home_team]
    away_team_shots = shots[shots['team'] == away_team]

    # Create the football pitch
    fig1 = create_football_pitch()
    fig2 = create_football_pitch()
    fig1.update_layout(
        width=500,
        height=500 * 80 / 120,  # Adjust height to maintain aspect ratio
        showlegend=False,
        plot_bgcolor='green',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    fig2.update_layout(
        width=500,
        height=500 * 80 / 120,  # Adjust height to maintain aspect ratio
        showlegend=False,
        plot_bgcolor='green',
        margin=dict(l=0, r=0, t=0, b=0)
    )
    # Plot the filtered shots on the pitch
    plot_shots(fig1, home_team_shots)
    plot_shots(fig2, away_team_shots)
    col1, col2 = st.columns(2)

    with col1:
        st.text(home_team)
        st.plotly_chart(fig1)

    with col2:
        st.text(away_team)
        st.plotly_chart(fig2)

# Add a sidebar for navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", ["Player Search", "Match Analysis", "About", "Contact"])

# Display the selected page
if selection == "Home":
    home()
elif selection == 'Player Search':
    player_scouting()
elif selection == 'Match Analysis':
    match_explorer()
elif selection == "About":
    about()
elif selection == "Contact":
    contact()
