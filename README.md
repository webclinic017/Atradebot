## Bot to invest

Bot to help you choose what to invest using AI 

### Install

Install using pip
```
pip install -e .
```

### Run 
Go to folder `src/atradebot`

start by setting your plan using .yaml file like in  `default.yaml`: 


Then run `python3 main.py -c default.yaml -m run`
This will get news and suggest what stocks to buy during that time and update the profile `.xlsx` files

### Test strategies
Go to folder `src/atradebot`

Use this to test different strategies using past historical data
```
python backtest.py
```

### Set to run everyday
Go to folder `src/atradebot`

run: `crontab -e`

And add this line to run everyday 8am: 
`0 8 * * * python main.py -c default.yaml -m run`


### Run App

Use the following command to run this bot as an app

```
streamlit run app.py
```

### Train model to predict news 
Go to folder `src/atradebot`

Use this to create a hugginface dataset to train a model
```
python fin_data.py
```
Then run this to train a model
```
python fin_train.py
```

