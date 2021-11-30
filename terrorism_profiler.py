import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


REGION_MAP = {
    "world": ['Central America & Caribbean', 'North America', 'Southeast Asia',
       'Western Europe', 'East Asia', 'South America', 'Eastern Europe',
       'Sub-Saharan Africa', 'Middle East & North Africa',
       'Australasia & Oceania', 'South Asia', 'Central Asia'],
    "asia": ['Southeast Asia', 'Middle East & North Africa', 'Australasia & Oceania', 'East Asia', 'South Asia', 'Central Asia'],
    "africa": ['Sub-Saharan Africa', 'Middle East & North Africa'],
    "europe": ['Western Europe', 'Eastern Europe'],
    "north america": ['Central America & Caribbean', 'North America'],
    "south america": ['Central America & Caribbean', 'South America'],
}

REGION_TXT = {
    'world': "The World",
    'asia': "Asia",
    'africa': "Africa",
    'europe': "Europe",
    'north america': "North America",
    'south america': "South America"
}


@st.cache
def load_dataset():
    df = pd.read_csv("globalterrorism.csv")
    df['continent'] = df['region_txt'].map(REGION_MAP)
    return df

@st.cache
def load_timerange_dataset(df, start, end):
    return df[(df['iyear']>= start) & (df['iyear'] <= end)]

@st.cache
def filter_continent_dataset(df, continent):
    if continent == 'africa':
        df = df[df['country_txt'] != 'Iraq']
    df = df[df['region_txt'].isin(REGION_MAP[continent])].copy()
    return df

@st.cache
def load_nkill_dataset(df):
    df_grp = df.groupby("country_txt", as_index=False)
    df = df_grp["nkill", "nkillus", "continent"].sum()
    df['Total attacks'] = df_grp.count()["nkill"]
    return df

@st.cache
def filter_attacktype_dataset(df, types):
    if not types or 'all' in types:
        return df
    return df[df['attacktype1_txt'].isin(types)]

@st.cache
def filter_gname_dataset(df, gname):
    if gname == 'all':
        return df
    return df[df['gname'] == gname]

@st.cache
def load_attacktype_counts_by_time(df):
    return df.groupby(["attacktype1_txt", "iyear"], as_index=False).size()

@st.cache
def load_historical_attacker_subdf(df, topk=11):
    top_gname = ['Taliban', 'Islamic State of Iraq and the Levant (ISIL)', 'Shining Path (SL)', 'Farabundo Marti National Liberation Front (FMLN)', 'Al-Shabaab', "New People's Army (NPA)", 'Irish Republican Army (IRA)', 'Revolutionary Armed Forces of Colombia (FARC)', 'Boko Haram', "Kurdistan Workers' Party (PKK)"]
    attacker_history_df = df[df['gname'].isin(top_gname)].groupby(["gname", "iyear"], as_index=False).size().sort_values("iyear")
    return attacker_history_df

@st.cache
def load_attacker_subdf(range_df, topk=15, dropunk=True):
    attacker_count_df = range_df.groupby("gname", as_index=False).size().sort_values("size", ascending=False)[1:topk]
    if dropunk:
        attacker_count_df = attacker_count_df[attacker_count_df['gname'] != 'Unknown']
    return attacker_count_df

@st.cache
def load_country_subdf(df, country):
    subdf = df[df['country_txt'] == country].copy()
    subdf = subdf[subdf['latitude'].notna()]
    subdf = subdf[subdf['longitude'].notna()]
    subdf['latitude']=pd.to_numeric(subdf['latitude']).astype(float) 
    subdf['longitude']=pd.to_numeric(subdf['longitude']).astype(float)
    print(subdf['latitude'].hasnans, subdf['longitude'].hasnans)
    subdf[['latitude', 'longitude']].to_csv("inspe.csv")
    return subdf

@st.cache
def gen_country_profile(country_df):
    country_group_df = country_df.value_counts('gname')[:5].to_frame("count").reset_index()
    country_target_df = country_df.value_counts('targtype1_txt')[:5].to_frame("count").reset_index()
    country_weapon_df = country_df.value_counts('weapsubtype1_txt')[:5].to_frame("count").reset_index()
    country_city_df = country_df.value_counts('city')[:5].to_frame("count").reset_index()
    return country_group_df, country_target_df, country_weapon_df, country_city_df

@st.cache
def country_list(df):
    return sorted(list(df['country_txt'].unique()))

@st.cache
def terrorism_groups(df):
    return ['all'] + sorted(list(df["gname"].unique()))

def colorscale():
    scale = px.colors.diverging.RdYlGn[::-1][2:]
    scale = scale + scale[-1:] * 5
    return scale

def attackTypes(df):
    return ['all'] + list(df['attacktype1_txt'].unique())

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    df = load_dataset()
    st.title("Global Terrorist Attacks from 1970 to 2017")
    st.write("Author: Yunxuan Xiao,  Last Update: Oct 17, 2021")
    st.image("headerimg.jpeg", width=1000)
    st.subheader("Introduction")
    st.markdown("Terrorism poses a direct threat to the security, international stability and prosperity of the people of the world. It is a persistent global threat that knows no border, nationality or religion, and is a challenge that the international community must tackle together. ")
    st.markdown("This study analyzed 181691 terrorist attack records over 205 countries during 1970-2017. We try to explore the historical trend and patterns of global terrorism and provide with fine-grained analysis on `location`, `fatalities`, `assailants`, `weapon` and other categories. In this website, you can freely explore when, where and how the terrorism attacks happend, so as to better understand the history and current situation of global terrorism.")

    # add_selectbox = st.sidebar.button("link")

    # with kill_sidebar:
    st.sidebar.header("Configurations for Section 1")
    scope_selectbox = st.sidebar.selectbox(
    "Scope",
    ('world', 'europe', 'asia', 'africa', 'north america', 'south america'))

    attacktypes = st.sidebar.multiselect('Attack Types', attackTypes(df), ['all'])
    selectgroup = st.sidebar.selectbox("Terrorism Groups", options=terrorism_groups(df))
    killstart, killend = st.sidebar.slider('Years', 1970, 2017, (1986, 2002), 1)

    # Global Terrorism Density:
    # ====================================================================================
    st.header("1. Geographical Distribution of Terrorist Activities")
    st.markdown("In this section, we visualized the distribution of historical terrorist attacks geographically. You can select the `region`, `timerange`, and `attack type` on the sidebar. The choropleth map chart can answer the questions like:")
    st.markdown("- What was the distribution of terrorism attacks in Asia during 1980-2001?") 
    st.markdown("- What was the major terrorism groups in North America?")
    st.subheader(f"1.1 Density of Terrorist Attacks in *{REGION_TXT[scope_selectbox]}*")
    subdf_1 = load_timerange_dataset(df, killstart, killend)
    subdf_2 = filter_attacktype_dataset(subdf_1, attacktypes)
    subdf_3 = filter_continent_dataset(subdf_2, scope_selectbox)
    subdf_4 = filter_gname_dataset(subdf_3, selectgroup)
    killdf = load_nkill_dataset(subdf_4)
    fig_1 = px.choropleth(killdf, locations="country_txt", 
                        locationmode="country names",
                        color="nkill", # lifeExp is a column of gapminder
                        hover_name="country_txt", # column to add to hover information
                        hover_data=["nkill", 'Total attacks'],
                        color_continuous_scale=colorscale(),
                        width=3100, height=700,
                        scope=scope_selectbox,
                        labels={'nkill': 'Total fatalities', 'country_txt': 'country'}
                        )
    borders=[0.4 for x in range(len(killdf))]
    fig_1.update_traces(marker_line_width=borders, marker={"opacity": 0.7})
    fig_1.update_layout(
        margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=0  #top margin
        )
    )
    st.plotly_chart(fig_1, use_container_width=True)

    # Attacker Analysis
    attacker_year_df = load_attacker_subdf(subdf_3, dropunk=True)

    st.subheader(f"1.2 Top 15 Terrorism Groups in *{REGION_TXT[scope_selectbox]}* from *{killstart}* to *{killend}*")
    fig_4 = px.bar(attacker_year_df, x='size',y='gname',orientation='h',
                   color='gname', labels={'gname': "Group Name", "size": "Number of Attacks"})
    st.plotly_chart(fig_4, use_container_width=True)
    
    # Country Browser
    # ==============================================================================
    st.header("2. Country-level Terrorism Profile")
    st.markdown("You may want to know which area of a country is more likely to have terrorist attacks, and which terrorist groups are rampant in a country.")
    st.markdown("In this section, we provide a country-level terrorism activity profiler, you can see the goegraphical distribution of attacks in one country. More detailed profile of `attack_target`, `weapons_used`, `major_cities`, and `major_terrorism_group` can be found in the expander.")
    select_country = st.selectbox(label='Country', options=country_list(df))
    country_subdf = load_country_subdf(df, select_country)

    with st.expander("Expand for Detailed Statistics"):
        profile_panel1, profile_panel2, profile_panel3, profile_panel4 = st.columns((1, 1, 1, 1))
        country_group_df, country_target_df, country_weapon_df, country_city_df = gen_country_profile(country_subdf)
        with profile_panel1:
            fig_131 = px.pie(country_group_df, names='gname', values='count', hover_name='gname', height=270,
            title="Top Terrorism Groups")
            fig_131.update_layout(showlegend=False,margin=go.layout.Margin(
                    l=0, #left margin
                    r=0, #right margin
                    b=0, #bottom margin
                    t=80  #top margin
                ))
            st.plotly_chart(fig_131, use_container_width=True)
            # st.dataframe(country_target_df)

        with profile_panel2:
            fig_132 = px.pie(country_target_df, names='targtype1_txt', values='count', hover_name='targtype1_txt', height=270,
            title="Top Attack Targets")
            fig_132.update_layout(showlegend=False,margin=go.layout.Margin(
                    l=0, #left margin
                    r=0, #right margin
                    b=0, #bottom margin
                    t=80  #top margin
                ))
            st.plotly_chart(fig_132, use_container_width=True)

        with profile_panel3:
            fig_133 = px.pie(country_weapon_df, names='weapsubtype1_txt', values='count', hover_name='weapsubtype1_txt', 
            title="Top Weapons Used", height=270)
            fig_133.update_layout(showlegend=False,margin=go.layout.Margin(
                    l=0, #left margin
                    r=0, #right margin
                    b=0, #bottom margin
                    t=80  #top margin
                ))
            st.plotly_chart(fig_133, use_container_width=True)
        
        with profile_panel4:
            fig_134 = px.pie(country_city_df, names='city', values='count', hover_name='city', height=270,
            title="Top Attacked Cities", color_discrete_map=px.colors.qualitative.Set3)
            fig_134.update_layout(showlegend=False,margin=go.layout.Margin(
                    l=0, #left margin
                    r=0, #right margin
                    b=0, #bottom margin
                    t=80  #top margin
                ))
            st.plotly_chart(fig_134, use_container_width=True)

    st.map(country_subdf)


    # Composition
    # ==============================================================================
    st.header("3. Composition of terrorist activities")
    st.markdown("Now let's navigate the evolution of attacks over the past 50 years." + " "*80)
    attack_type_timerange, attack_type_sunburst = st.columns((3, 2))
    with attack_type_timerange:
        df_attacktype = load_attacktype_counts_by_time(df)
        print(df_attacktype.head())
        fig_2 = px.line(df_attacktype, x="iyear", y="size", color='attacktype1_txt', 
                    markers=True, height=500, width=300,
                    title="2.1 Number of Attacks over time grouped by attack type",
                    labels={"iyear": "Year", "attacktype1_txt": "Attack Type", "size": "Number of Events"})
        fig_2.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01),
            margin=go.layout.Margin(
                l=0, #left margin
                r=100, #right margin
                b=0, #bottom margin
                t=100  #top margin
            ))
        st.plotly_chart(fig_2, use_container_width=True)
        st.markdown("From the chat above, we notice that the number of such events increased dramatically in recent years. The number of terrorism attacks increased by 10 times from 2004 to 2017.")
    
    with attack_type_sunburst:
        pie_path = ["region_txt", "attacktype1_txt"]
        sunburst_df = df[["region_txt", "attacktype1_txt", "nkill"]].copy()
        sunburst_df.dropna(inplace=True)
        fig_3 = px.sunburst(sunburst_df, path=pie_path, values='nkill', width=100, title="2.2 Composition of Attack Types in Regions")
        fig_3.update_layout(
            autosize=False,
            width=500,
            height=500,   
            margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=100  #top margin
            ))
        st.plotly_chart(fig_3, use_container_width=True)
        st.markdown("[Zoom in by clicking the fan area.]")
        st.markdown("We can see that Bombing/Explosion was the most frequent type of attack in Middle East&North Afirca and South Asia, followed by Armed Assault in other regions.")
    
    attacker_history_df = load_historical_attacker_subdf(df)
    fig_5 = px.line(attacker_history_df, x='iyear', y='size', color='gname', markers=True, title="2.3 Top 10 Terrorism Group over the Years")

    fig_5.update_layout(
            autosize=False,
            width=500,
            height=500, 
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),  
            margin=go.layout.Margin(
                l=0, #left margin
                r=90, #right margin
                b=0, #bottom margin
                t=30  #top margin
            ))
    st.plotly_chart(fig_5, use_container_width=True)
    st.markdown("From the chart above, we observed that in 1980-1995, South American terrorism groups Shining Path (SL) and Farabundo Marti National Liberation Front (FMLN) carried out most of the attacks. Since 2004, Taliban and Islamic State of Iraq and the Levant (ISIL) has carried out more terrorist attacks than ever before, which brought serious threat to international security.")
    st.subheader("References")
    st.markdown("Dataset: The Global Terrorism Database (GTD) from Kaggle (https://www.kaggle.com/START-UMD/gtd)")