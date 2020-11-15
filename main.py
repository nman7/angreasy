from flask import Flask,render_template,request
app = Flask(__name__)

@app.route('/',methods=["GET","POST"])

def hello():
    global dispan,video_embedded,v_id
    video_embedded=''
    dispan={}
    v_id=''

    if request.method=="POST":
        mydic = request.form
        URL = mydic['url']

        # Getting ID from YT video URL
        def get_yt_video_id(url):
            import re
            reg_expression = r"^.*(youtu\.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
            matches = re.findall(reg_expression, url)
            if matches and len(matches[0][1]) == 11:
                return matches[0][1]
            raise Exception("Invalid URL, Please enter again!")


        try:
            # getting Subtitle
            v_id = get_yt_video_id(URL)
            VIDEOID=v_id
            from youtube_transcript_api import YouTubeTranscriptApi
            subs = YouTubeTranscriptApi.get_transcript(v_id)
        except Exception as error:
            e = error
            return render_template('index.html', e=e)



        
        import nltk
        nltk.download('punkt','stopwords','wordnet')
        from nltk.corpus import stopwords
        from nltk.corpus import wordnet
        stop = stopwords.words('english')
        # pip install PyDictionary
        from PyDictionary import PyDictionary
        dictionary = PyDictionary()
        import pandas as pd
        difficult_words = pd.read_csv('IeltsandGRE_words.csv')
        all_words = pd.read_csv('All_dictionary_words.csv')

        Subtitle_Dataframe = []
        for i in subs:
            Subtitle_Dataframe.append([i['text'], i['start']])

        # Create the pandas DataFrame
        Subtitle_Dataframe = pd.DataFrame(Subtitle_Dataframe, columns=['subtitle', 'time'])

        #Tokenization
        Subtitle_Dataframe['tokenized_sents'] = Subtitle_Dataframe.apply(
            lambda row: nltk.word_tokenize(row['subtitle']), axis=1)

        #removing stop words
        Subtitle_Dataframe['words_without_stopwords'] = Subtitle_Dataframe['tokenized_sents'].apply(
            lambda x: [word for word in x if word not in (stop)])



        #cleaning-----------------------------------------------------------------------
        def clean_text(text):
            import re
            text = [re.sub(pattern, ' ', j) for j in text]
            text = [re.sub(r'\b\w{1,3}\b', '', j) for j in text]
            text = [re.sub(r'[^\w\s]', '', j) for j in text]
            text = [j.strip() for j in text]
            text = [j.strip(' ') for j in text]
            return text


        pattern = '[0-9]'
        Subtitle_Dataframe['words_without_stopwords'] = Subtitle_Dataframe['words_without_stopwords'].apply(
            clean_text)

        Final = []
        all_words = all_words[['Word', 'Meaning']]

        for i, j in Subtitle_Dataframe.iterrows():
            for x in j['words_without_stopwords']:
                try:
                    if x in difficult_words:
                        ans = dictionary.meaning(x)['Noun']
                        Final.append([x, ans, j['time']])
                except:
                    pass
                try:
                    d = all_words.index[all_words.Word == x].tolist()
                    ans = all_words.iloc[d[0]]
                    Final.append([ans['Word'], ans['Meaning'], j['time']])
                    # print("A")
                except:
                    pass


        FINAL_dataframe = pd.DataFrame(Final, columns=['word', 'meaning', 'time'])
        FINAL_dataframe = FINAL_dataframe.drop_duplicates(subset='word', keep="first")
        FINAL_dataframe['time'] = FINAL_dataframe['time'].astype(int)

        def convert(seconds):
            seconds = seconds % (24 * 3600)
            hour = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60

            seconds= "%d:%02d:%02d" % (hour, minutes, seconds)
            return seconds


        FINAL_dataframe['time']=FINAL_dataframe['time'].apply(convert)

        vid_url = []
        for i in FINAL_dataframe['time']:
            bvm = "https://www.youtube.com/embed/{id}?start={first}".format(
                id=v_id, first=i)
            vid_url.append(bvm)
        FINAL_dataframe['video_url_with_time'] = vid_url



        shp = FINAL_dataframe.shape
        shape = shp[0]

        for i in range(shape):
            x = list(FINAL_dataframe.iloc[i])
            dispan[x[0]] = [x[1], x[2], x[3]]


        video_embedded = "https://www.youtube.com/embed/{id}?start={first}".format(
            id=v_id, first=0)
    return render_template('index.html',dispan=dispan,url = video_embedded,VIDEOID=v_id)







app.run(debug=True)