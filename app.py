#Importing the necessary libraries
from http.client import responses

import streamlit as st
import pandas as pd
import plost
import requests
import isodate
st.set_page_config(
    page_title="Youtube Rewind 2024",
    page_icon="https://cdn3.iconfinder.com/data/icons/pixel-social-media-2/16/Youtube-512.png",
    layout="wide",
)
st.image('https://cdn3.iconfinder.com/data/icons/pixel-social-media-2/16/Youtube-512.png', width=100)
st.title('YouTube Rewind 2024')
uploaded_file = st.file_uploader("Upload watch-history.json", type=["json"])

def load_data(file):
    #load data
    df1 = pd.read_json(file)
    #Data Cleaning and Preprocessing
    df1 = df1.drop(columns=['header', 'products', 'activityControls', ])
    df1['modified_title'] = df1['title'].apply(lambda x: x[8:])
    df1 = df1.drop(columns=['title'], axis=1)
    df1['Type'] = df1['details'].apply(lambda x: 'Valid' if type(x) == float else 'Invalid')
    df1 = df1[df1['Type'] == 'Valid']
    df1['Type'] = df1['subtitles'].apply(lambda x: 'Invalid' if type(x) == float else 'Valid')
    df1 = df1[df1['Type'] == 'Valid']
    df1['Type'] = df1['titleUrl'].apply(lambda x: 'Invalid' if type(x) == float else 'Valid')
    df1 = df1[df1['Type'] == 'Valid']
    df1['Type'] = df1.loc[:, 'titleUrl'].apply(lambda x: 'Video' if len(x) == 43 else 'Post')
    df1 = df1[df1['Type'] == 'Video']
    df1['channel'] = df1.loc[:, 'subtitles'].apply(lambda x: x[0]['name'])
    df1['channelId'] = df1.loc[:, 'subtitles'].apply(lambda x: x[0]['url'][32:])
    df1['video_id'] = df1.loc[:, 'titleUrl'].apply(lambda x: x[32:])
    df1.drop(columns=['subtitles', 'titleUrl', 'Type', 'details'], axis=1, inplace=True)
    df1['time'] = pd.to_datetime(df1['time'], format='mixed')
    df1['day'] = df1['time'].dt.day
    df1['month'] = df1['time'].dt.month_name()
    df1['day_of_week'] = df1['time'].dt.day_name()
    df1['year'] = df1['time'].dt.year
    df1 = df1[df1['year'] == 2024]
    subtitles_count = df1['channel'].value_counts().reset_index()
    subtitles_count = subtitles_count.merge(df1[['channelId', 'channel']], on='channel').drop_duplicates().reset_index(drop=True)
    month_count = df1['month'].value_counts().reset_index()
    month_count.columns = ['month', 'number of videos']
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                   'November', 'December']
    month_count['month'] = pd.Categorical(month_count['month'], categories=month_order, ordered=True)
    month_count = month_count.sort_values('month')
    df1.reset_index(drop=True, inplace=True)
    vid_count = df1['video_id'].value_counts().reset_index()
    vid_count = vid_count.merge(df1[['video_id', 'modified_title']], on='video_id').drop_duplicates().reset_index(
        drop=True)
    df1['date'] = df1['time'].dt.date
    heat_map = df1['date'].value_counts().reset_index()
    heat_map.columns = ['date', 'count']

    return subtitles_count,month_count,vid_count,df1,heat_map

def get_video_details(video_ids, api_key):

    topic_genre_mapping = {
    'https://en.wikipedia.org/wiki/Film': 'Entertainment',
    'https://en.wikipedia.org/wiki/Music': 'Music',
    'https://en.wikipedia.org/wiki/Entertainment': 'Entertainment',
    'https://en.wikipedia.org/wiki/Videoblogging': 'Vlogging',
    'https://en.wikipedia.org/wiki/Lifestyle_(sociology)': 'Lifestyle',
    'https://en.wikipedia.org/wiki/Society': 'Society & Culture',
    'https://en.wikipedia.org/wiki/Knowledge': 'Educational',
    'https://en.wikipedia.org/wiki/Hobby': 'Hobbies',
    'https://en.wikipedia.org/wiki/Technology': 'Technology',
    'https://en.wikipedia.org/wiki/Gaming': 'Gaming',
    'https://en.wikipedia.org/wiki/Video_game_culture': 'Gaming',
    'https://en.wikipedia.org/wiki/Sport': 'Sports',
    'https://en.wikipedia.org/wiki/Basketball': 'Sports',
    'https://en.wikipedia.org/wiki/Food': 'Food & Cooking',
    'https://en.wikipedia.org/wiki/Health': 'Health & Fitness',
    'https://en.wikipedia.org/wiki/Travel': 'Travel & Adventure',
    'https://en.wikipedia.org/wiki/Politics': 'Politics',
    'https://en.wikipedia.org/wiki/Science': 'Science',
    'https://en.wikipedia.org/wiki/Fashion': 'Fashion & Beauty',
    'https://en.wikipedia.org/wiki/History': 'History',
    'https://en.wikipedia.org/wiki/Business': 'Business & Finance',
    'https://en.wikipedia.org/wiki/Religion': 'Religion & Spirituality',
    'https://en.wikipedia.org/wiki/Animals': 'Animals & Pets'
}

    details = {'genre': [], 'duration': [], 'video_id': []}
    base_url = "https://www.googleapis.com/youtube/v3/videos"

    for i in range(0, len(video_ids), 50):
        # Process in chunks of 50
        chunk = video_ids[i:i+50]
        params = {
            'part': 'snippet,topicDetails,contentDetails',
            'id': ','.join(chunk),
            'key': api_key
        }
        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            data = response.json().get('items', [])

            for video in data:
                video_id = video['id']
                topics = video.get('topicDetails', {}).get('topicCategories', [])
                duration_iso = video.get('contentDetails', {}).get('duration', 'PT0S')

                # Assign genre based on topics
                video_genre = 'Other'
                for topic in topics:
                    if topic in topic_genre_mapping:
                        video_genre = topic_genre_mapping[topic]
                        break  # Use the first matched genre

                # Convert ISO duration to seconds
                duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())

                details['genre'].append(video_genre)
                details['duration'].append(duration_seconds)
                details['video_id'].append(video_id)

        else:
            print(f"Error: {response.status_code}, {response.text}")

    return details

#Creating the Web App
if uploaded_file is not None:
    key = st.secrets['key']
    most_liked,month_data,vid_data,df_tot,activity = load_data(uploaded_file)
    st.write("## Here's a summary of your YouTube activity in 2024 ⏬")
    total_vids = df_tot.shape[0]
    st.write("")
    st.write(f'#### ➡️You watched a total of **{total_vids}** videos this year.')
    st.write("##### _Thats a lot of content!_")
    st.header('📺Lets see who you watched the most')
    st.write('### At number one we have,')
    url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet&id={most_liked['channelId'][0]}&key={key}'
    response = requests.get(url).json()
    thumbnail_url = response['items'][0]['snippet']['thumbnails']['default']['url']
    col1,col2,col3 = st.columns([1,5,1])
    with col2:
        col4, col5 = st.columns([1, 5])
        with col4:
            st.image(thumbnail_url, width=50)
        with col5:
            st.write(f'### **{most_liked["channel"][0]}**')
        st.write(f'### _with a total of ___{most_liked["count"][0]}___ videos watched_.')
    st.write('#### While its not a competition, here are the top 10 channels you watched this year:')

    for i in range(10):
        url = f'https://www.googleapis.com/youtube/v3/channels?part=snippet&id={most_liked['channelId'][i]}&key={key}'
        response = requests.get(url).json()
        thumbnail_url = response['items'][0]['snippet']['thumbnails']['default']['url']
        col4, col5 = st.columns([1, 10])
        with col4:
            st.image(thumbnail_url, width=40)
        with col5:
            st.write(f'#### **{most_liked["channel"][i]}** ')
            st.write(f'##### _with a total of ___{most_liked["count"][i]}___ videos watched_.')
        st.write('')
    #bar graph
    st.write('---')
    st.header('📅Here is a breakdown of number of videos you watched each month')
    st.bar_chart(month_data.set_index('month'))

    #max month
    st.write(f'#### 📈You watched the most videos in the month of {month_data["month"][0]} , _with a total of {month_data["number of videos"][0]} videos watched_.')
    if month_data["month"][0] in ['March', 'April']:
        st.write(f'#### _Academic Comeback?_')
    if month_data["month"][0] in ['May', 'June', 'July', 'August']:
        st.write(f'#### _Looks like you had a lot of free time in Summer!_')
    if month_data["month"][0] in ['September', 'October', 'November']:
        st.write(f'#### _Better content in the fall, huh?_')
    if month_data["month"][0] in ['December', 'January', 'February']:
        st.write(f'#### _Winter is coming, huh?_')
    st.write()
    st.write('---')
    st.header('📺Lets see what you watched the most this year:')
    url_vid1 = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid_data['video_id'][0]}&key={key}'
    response_vid1 = requests.get(url_vid1).json()
    col1, col2 = st.columns([2, 2])
    with col1:
        st.image(response_vid1['items'][0]['snippet']['thumbnails']['standard']['url'],width=450)
    with col2:
        st.write('')
        st.write(f'##### You watched this video the most number of times, _a total of {vid_data["count"][0]} times_.')
        st.write(f'#### "{response_vid1['items'][0]['snippet']['title']}"')
    url_vid2 = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={df_tot['video_id'].iloc[-1]}&key={key}'
    response_vid2 = requests.get(url_vid2).json()
    col1, col2 = st.columns([2, 2])
    with col1:
        st.image(response_vid2['items'][0]['snippet']['thumbnails']['standard']['url'], width=450)
    with col2:
        st.write('')
        st.write(f'##### This is the earliest video you watched this year according to your watch history, on _{df_tot["month"].iloc[-1]} {df_tot['day'].iloc[-1]}_.')
        st.write(f'#### "{response_vid2['items'][0]['snippet']['title']}"')
    st.write('#### ⏬You also watched these the most this year:')
    for i in range(1,10):
        vid_url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid_data['video_id'][i]}&key={key}'
        response_vid = requests.get(vid_url).json()
        thumbnail_url_vid = response_vid['items'][0]['snippet']['thumbnails']['standard']['url']
        col4, col5 = st.columns([1, 2])
        with col4:
            st.image(thumbnail_url_vid, width=250)
        with col5:
            st.write('')
            st.write('')
            st.write('')
            st.write(f'#### **{vid_data["modified_title"][i][:40]}...** _, a total of ___{vid_data["count"][i]}___ times watched_.')
    st.write('---')
    st.write("## Here's a more detailed look at your YouTube activity this year 🤓")
    st.write('### 📅Activity Calendar')
    #calendar heatmap using july
    plost.time_hist(
        data=activity,
        date='date',
        x_unit='week',
        y_unit='day',
        color='count',
        aggregate='sum',
        legend='left')
    st.write(f'#### _Wish your leetcode profile was this consistent huh?_')
    st.divider()
    vid_ids = df_tot['video_id'].sample(n = 1000).tolist()
    list_genres = get_video_details(vid_ids, key)
    df_genres = pd.DataFrame(list_genres)
    temp = df_genres['genre'].value_counts().reset_index()
    temp = temp.head(8)
    temp['Percentage'] = ((temp['count'] / temp['count'].sum()) * 100).round()
    st.header('Now lets do a genre wise analysis📊')
    col1,col2 = st.columns([1,1])
    with col1:
        st.write('#### With Shorts')
        plost.pie_chart(
            data=temp,
            theta='Percentage',
            color='genre')
    df_genres_long = df_genres[df_genres['duration'] > 100]
    temp2 = df_genres_long['genre'].value_counts().reset_index()
    temp2['Percentage'] = ((temp2['count'] / temp2['count'].sum()) * 100).round()
    with col2:
        st.write('#### Without Shorts')
        plost.pie_chart(
            data=temp2,
            theta='Percentage',
            color='genre')
    st.write(f'#### _You watched a lot of {temp['genre'][0]} content overall, and when it comes to long-'
             f'form content, it was mostly {temp2['genre'][0]}_')


