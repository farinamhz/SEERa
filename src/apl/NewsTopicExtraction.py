import numpy as np
import pandas as pd
import gensim
import glob
import tagme
from tqdm import tqdm

import Params
from tml import TopicModeling as tm
from cmn import Common as cmn
from dal import DataPreparation as dp

def text2tagme(news_table, threshold=0.05):
    for i in range(len(news_table)):
        text = news_table[Params.apl["textTitle"]][i]
        annotations = tagme.annotate(text)
        result = []
        if annotations is not None:
            for keyword in annotations.get_annotations(threshold):
                result.append([keyword.entity_title, keyword.score, news_table.index[i]])
    d = {
        'Id': list(range(len(result))),
        'Word': result[0],
        'Score': result[1],
        'NewsId': result[2]
    }
    df = pd.DataFrame(d)
    df.to_csv(f'{Params.apl["path2read"]}/NewsTagmeAnnotated.csv')
    return result

def main(news_table):
    t_t = Params.apl["textTitle"]
    news_table = news_table[news_table[t_t].notna()]
    news_ids = news_table['NewsId']
    np.save(f'{Params.apl["path2save"]}/NewsIds_ExpandedURLs.npy', news_ids)
    if Params.dal['tagMe']:
        tagme.GCUBE_TOKEN = "7d516eaf-335b-4676-8878-4624623d67d4-843339462"
        for doc in tqdm(news_table.itertuples(), total=news_table.shape[0]):
            news_table.at[doc.Index, t_t] = dp.tagme_annotator(doc.Text).split()
        processed_docs = news_table[['NewsId', t_t]]
    else:
        processed_docs_ = [dp.preprocess(news).split() for news in news_table[t_t]]
        processed_docs = pd.DataFrame()
        processed_docs['NewsId'] = news_table['NewsId']
        processed_docs[t_t] = np.asarray(processed_docs_)

    # Dictionary and Model Loading
    path_dict = f"{Params.tml['path2save']}/{Params.tml['numTopics']}TopicsDictionary.mm"
    path_mdl = f"{Params.tml['path2save']}/{Params.tml['numTopics']}Topics.model"
    tm_model = pd.read_pickle(path_mdl)
    dictionary = pd.read_pickle(path_dict)
    cmn.logger.info(f'6.2.1. Loading saved topic model of {Params.tml["method"]} from {path_dict} and {path_mdl} ...')

    total_news_topics = {}
    for index, row in processed_docs.iterrows():

        if Params.tml['method'].lower() == 'btm':
            topics = tm.doc2topics(tm_model, row[t_t], threshold=Params.evl['threshold'], just_one=Params.tml['justOne'], binary=Params.tml['binary'], dic=dictionary)
        else:
            news_bow_corpus = dictionary.doc2bow(row[t_t])
            topics = tm.doc2topics(tm_model, news_bow_corpus, threshold=Params.evl['threshold'], just_one=Params.tml['justOne'], binary=Params.tml['binary'])
        total_news_topics[row['NewsId']] = topics.tolist()
    pd.to_pickle(total_news_topics, f'{Params.apl["path2save"]}/NewsTopics.pkl')
    return pd.DataFrame(total_news_topics)


