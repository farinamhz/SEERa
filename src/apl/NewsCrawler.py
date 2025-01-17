import pandas as pd
import os
from newspaper import Article
from tqdm import tqdm
import glob

import Params

def crawl_request(url):
    article = Article(url)
    article.download()
    article.parse()
    return article


def news_crawler(tweet_path, tweet_entities_path):
    tweets = pd.read_csv(tweet_path)
    tweet_entities = pd.read_csv(tweet_entities_path)
    tweet_entities.dropna(inplace=True, subset=['ExpandedUrl'])
    urls = tweet_entities['ExpandedUrl']
    short_urls = tweet_entities['Url']
    display_urls = tweet_entities['DisplayUrl']
    tweet_ids = tweet_entities['TweetId']
    entity_type_codes = tweet_entities['EntityTypeCode']
    accepted_news_ids = []
    accepted_tweet_ids = []
    accepted_user_ids = []
    news_articles = []
    news_titles = []
    publish_date = []
    accepted_urls = []
    accepted_short_urls = []
    accepted_display_urls = []
    description = []
    source_urls = []
    chunk = True
    if chunk and not os.path.isdir(f'../data/toy/News'): os.makedirs(f'../data/toy/News')
    chunk_size = 20000
    indices = urls.index
    url_values = urls.values
    for i in tqdm(range(len(url_values))):
        if entity_type_codes[i] != 2:
            continue
        url = url_values[i]
        ind = indices[i]
        if chunk and i % chunk_size == 0 and i > 0:
            news = {'NewsId': accepted_news_ids, "UserId": accepted_user_ids, 'TweetId': accepted_tweet_ids,
                    'ExpandedUrl': accepted_urls, 'ShortUrl': accepted_short_urls, 'DisplayUrl': accepted_display_urls,
                    'SourceUrl': source_urls, 'Text': news_articles, 'Title': news_titles, 'Description': description,
                    'PublicationTime': publish_date}
            news = pd.DataFrame.from_dict(news)
            news.to_csv(f'../data/toy/News/News_Chunk{i//chunk_size}.csv', index=False)
            accepted_news_ids = []
            accepted_tweet_ids = []
            accepted_user_ids = []
            accepted_urls = []
            accepted_short_urls = []
            accepted_display_urls = []
            description = []
            source_urls = []
            news_articles = []
            news_titles = []
            publish_date = []
        try:
            if url in accepted_urls:
                continue
            article = crawl_request(url)
            accepted_news_ids.append(ind)
            accepted_tweet_ids.append(tweet_ids[ind])
            uid = tweets[tweets.Id == tweet_ids[ind]]['UserId']
            accepted_user_ids.append(uid)
            accepted_short_urls.append(short_urls[ind])
            accepted_display_urls.append(display_urls[ind])
            accepted_urls.append(url)
            source_urls.append(article.source_url)
            text = article.text
            title = article.title
            publish_date.append(article.publish_date)
            news_articles.append(text)
            news_titles.append(title)
            description.append(article.meta_description)
        except:
            pass
    if not chunk:
        news = {'NewsId': accepted_news_ids, "UserId": accepted_user_ids, 'TweetId': accepted_tweet_ids,
                'ExpandedUrl': accepted_urls, 'ShortUrl': accepted_short_urls, 'DisplayUrl': accepted_display_urls,
                'SourceUrl': source_urls, 'Text': news_articles, 'Title': news_titles, 'Description': description,
                'PublicationTime': publish_date}
        news = pd.DataFrame.from_dict(news)
        news.insert(0, "NewsId", list(range(len(news))), True)
        news.to_csv(f'{Params.dal["path"]}/News.csv', index=False)
    else:
        frame_path = sorted(glob.glob(f'{Params.dal["path"]}/News/*_Chunk*.csv'))
        frames = []
        for f in frame_path:
            frames.append(pd.read_csv(f))
        news = pd.concat(frames, ignore_index=True)
        news.insert(0, "NewsId", list(range(len(news))), True)
        news.to_csv(f'{Params.dal["path"]}/News.csv', index=False)

