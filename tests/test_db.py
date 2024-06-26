# cron job for getting news to db

import json
import sqlalchemy as db
from atradebot.db import create_db
from atradebot.utils_news import get_google_news

# setup db:
engine, connection, stocks, dates, news, sentiments = create_db()

# get some news for 1 stock:
stock = 'AAPL'
stock_news, _, _ = get_google_news(stock, num_results=10, time_period=['2022-06-28', '2022-06-31'])
print('Articles #:', len(stock_news))
print(stock_news)

# # save to json so we do not have to get news again:
# with open("stock_news.json", "w") as text_file:
#     jsonString = json.dumps(stock_news)
#     text_file.write(jsonString)
#     text_file.close()

# read json
# jsonString = open("stock_news.json", "r").read()

# add articles to database:
# for article in json.loads(jsonString):
for article in stock_news:
    print(article)
    entry = [{'symbol':article['stock'], 
              'title':article['title'], 
              'date':article['date'], 
              'url':article['link'], 
              'source':article['source'], 
              'text':article['text'], 
              'sentiment':'0', 
              'embedding':'[0,0,0]'},
            ]
    query = db.insert(news)
    ResultProxy = connection.execute(query,entry)

# query news:
query = news.select()
ResultProxy = connection.execute(query)
ResultSet = ResultProxy.fetchall()
print(ResultSet)