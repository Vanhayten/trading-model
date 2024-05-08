#!/usr/bin/env python
# coding: utf-8

# In[1]:


from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import time


# In[2]:


mt5.initialize()


# In[3]:


login = 68166696
password = "Developper@1996"
server = "RoboForex-Pro"

mt5.login(login, password, server)


# In[4]:


symbol = "XAUUSD"
timeframe = mt5.TIMEFRAME_M5


# In[5]:


def calculate_date_from():
    today = datetime.now()
    return today - timedelta(days=2)


# In[6]:


def fetch_data_range(start_date, end_date):
    rates = pd.DataFrame(mt5.copy_rates_range(symbol, timeframe, start_date, end_date))
    rates["time"] = pd.to_datetime(rates["time"], unit="s")
    return rates


# In[ ]:


while True:
    # Calculate the start date for the last two days
    date_from = datetime(calculate_date_from().year, calculate_date_from().month, calculate_date_from().day)
    
    # Calculate the end date as the current date and time
    date_to = datetime.now()
    
    # Fetch data for the last two days
    latest_data = fetch_data_range(date_from, date_to)
    
    # Process the data or send it to the model for analysis
    # ...
    
    # Display the latest data in the Jupyter Notebook
    display(latest_data)
    
    # Wait for the next 5-minute interval
    time.sleep(300)  # Wait for 5 minutes (300 seconds)


# In[ ]:




