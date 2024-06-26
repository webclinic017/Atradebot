# util and helper functions for atradebot

import pandas as pd
from datetime import datetime, timedelta
import yaml
import yfinance as yf
import re
import random
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter

TextEmbeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

DATE_FORMAT = "%Y-%m-%d"

def is_business_day(date):
    """check if date is a business day

    :param date: date to check
    :type date: datetime.date
    :return: if date is a business day
    :rtype: bool
    """    
    return bool(len(pd.bdate_range(date, date)))

def find_business_day(start_date, num_days):
    """add or subtract days from start_date and find the next business day

    :param start_date: date to start from
    :type start_date: datetime.date
    :param num_days: number of days to add/subtract
    :type num_days: int
    :return: output date
    :rtype: datetime.date
    """ 
    out_date = start_date + timedelta(days=num_days)
    while not is_business_day(out_date):
        if num_days < 0:
            out_date -= timedelta(days=1)
        else:
            out_date += timedelta(days=1)
        
    return out_date

#add/subtract business days
def business_days(start_date, num_days):
    """add or subtract business days from start_date

    :param start_date: date to start from
    :type start_date: datetime.date
    :param num_days: number of days to add/subtract
    :type num_days: int
    :return: output date
    :rtype: datetime.date
    """    
    current_date = start_date
    business_days_added = 0
    while business_days_added < abs(num_days):
        if num_days < 0:
            current_date -= timedelta(days=1)
        else:
            current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday to Friday
            business_days_added += 1
    return current_date


def pd_append(df, dict_d):
    """append dictionary to dataframe

    :param df: pandas dataframe
    :type df: pandas.DataFrame
    :param dict_d: dictionary to append
    :type dict_d: dict
    :return: pandas dataframe with appended dictionary
    :rtype: pandas.DataFrame
    """ 
    return pd.concat([df, pd.DataFrame.from_records([dict_d])])


def get_price(stock):
    """get current price of stock

    :param stock: stock id
    :type stock: str
    :return: current price
    :rtype: float
    """    
    ticker = yf.Ticker(stock).info
    return ticker['regularMarketOpen']

def get_config(cfg_file):
    with open(cfg_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    return cfg


def get_price_date(date, end_date, stock):
    """get price of stock at date and end_date

    :param date: start date to get price 
    :type date: datetime.date
    :param end_date: end date to get price
    :type end_date: datetime.date
    :param stock: stock id
    :type stock: str
    :return: dataframe of stock data from date to end_date
    :rtype: pandas.DataFrame
    """    
    data = yf.Ticker(stock)
    hdata = data.history(start=date.strftime(DATE_FORMAT),  end=end_date.strftime(DATE_FORMAT))
    return hdata

def find_peaks_valleys(array):
    """find peaks and valleys

    :param array: list of numbers
    :type array: List[int]
    :return: reduced list of peaks and valleys. list of ids of the array
    :rtype: List[int]
    """    
    peaks = []
    valleys = []
    off = 5
    for i in range(off, len(array) - off, off):
        if array[i - off] < array[i] > array[i + off]:
            peaks.append(i)
        elif array[i - off] > array[i] < array[i + off]:
            valleys.append(i)
    return peaks, valleys


def filter_points(data, peak_idx, valley_idx):
    """ignore peaks and valleys that are too close to each other

    :param data: data from yfinance.download
    :type data: pandas
    :param peak_idx: list of ids for peaks
    :type peak_idx: List[int]
    :param valley_idx: list of ids for valleys
    :type valley_idx: List[int]
    :return: reduced list of peaks and valleys
    :rtype: List[int]
    """       
    len_min = min(len(peak_idx), len(valley_idx))
    idx = 0
    coef_var = np.std(data)/np.mean(data)
    peak_idx_n, valley_idx_n = [], []
    while idx < len_min:
        abs_diff = abs(data[peak_idx[idx]]-data[valley_idx[idx]])
        min_diff = min(data[peak_idx[idx]], data[valley_idx[idx]])
        percent = abs_diff/min_diff
        if percent > coef_var*0.2: 
            peak_idx_n.append(peak_idx[idx])
            valley_idx_n.append(valley_idx[idx])
        idx += 1
    return peak_idx_n, valley_idx_n
    
# run financial sentiment analysis model
def get_forecast(stock, date, add_days=[21, 5*21, 12*21]):
    """get forecast for stock on date

    :param stock: stock id
    :type stock: str
    :param date: date in datetime format 
    :type date: datetime
    :param add_days: number of days to add for forecasting in a list, defaults to [21, 5*21, 12*21]
    :type add_days: list, optional
    :return: forecast list based on add_days eg.: add_days=[21, 5*21, 12*21] return is stock gain/loss in [1mon, 5mon, 1 yr]. higher than 1. percent increase, lower than 1. percent decrease
    :rtype: List[int]
    """
    s = date
    e = business_days(s, +3)
    data = yf.Ticker(stock)
    hdata = data.history(start=s.strftime("%Y-%m-%d"),  end=e.strftime("%Y-%m-%d"))
    price = hdata['Close'].mean()

    forecast = [0, 0, 0]
    for idx, adays in enumerate(add_days): #add business days
        s = business_days(s, adays)#look into future
        e = business_days(s, +3)
        hdata = data.history(start=s.strftime("%Y-%m-%d"),  end=e.strftime("%Y-%m-%d"))
        forecast[idx] = hdata['Close'].mean()/price
    
    return forecast


def get_mentionedtext(keyword, text, context_length=512):
    """get text around keyword given the number of characters to extract before and after the keyword

    :param keyword: keyword to search for in text
    :type keyword: str
    :param text: text to search for keyword
    :type text: str
    :param context_length: number of words before and after the keyword, defaults to 512
    :type context_length: int, optional
    :return: collected text around keyword
    :rtype: str
    """    
    delimiter = '.'
    # Create a regex pattern to match the keyword with surrounding text
    # pattern = r"(.{0,%d})(%s)(.{0,%d})" % (context_length, re.escape(keyword), context_length)
    pattern = r"([^%s]+%s[^%s]+)%s" % (delimiter, re.escape(keyword), delimiter, delimiter)

    # Find all matches in the text
    matches = re.findall(pattern, text)
    f_text = ''
    for match in matches:
        match = match.replace("\n", "")
        f_text += match
        if len(f_text) > context_length:
            break
    return f_text

def get_doc2vectext(query, intexts):
    """get relevant text from intexts based on query using vector search

    :param query: input to search for
    :type query: str
    :param intexts: context to search in
    :type intexts: str
    :return: relevant text from intexts
    :rtype: str
    """    
    text_splitter = CharacterTextSplitter(separator=' ', chunk_size=128, chunk_overlap=16)
    texts = text_splitter.split_text(intexts)
    vector_store = FAISS.from_texts(texts, TextEmbeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    doc = retriever.get_relevant_documents(query)
    dstr = ' '.join([d.page_content for d in doc])
    return dstr

def gen_rand_alloc(n_stock=5):
# Generate random percentages that sum up to 100
    percentages = [random.randint(1, 100) for _ in range(n_stock - 1)]
    remaining_percentage = 100 - sum(percentages)
    percentages.append(remaining_percentage)
    return percentages

