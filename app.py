import os
from flask import Flask
from lxml import html
import requests
import json
from collections import OrderedDict
from time import sleep
import random
import pymongo
from urllib.request import Request, urlopen
from fake_useragent import UserAgent
import random
from bs4 import BeautifulSoup
from IPython.core.display import clear_output
from apscheduler.schedulers.background import BackgroundScheduler

#a very sophisticated stock data scraper

user_agent_list = (
   #Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
)
DBUrl = 'Insert Your MONGO DB string here'

# Here I provide some proxies for not getting caught while scraping
ua = UserAgent() # From here we generate a random user agent
proxies = [] # Will contain proxies [ip, port]

# Main function
def loadProxies():
  # Retrieve latest proxies
  proxies_req = Request('https://www.sslproxies.org/')
  proxies_req.add_header('User-Agent', ua.random)
  proxies_doc = urlopen(proxies_req).read().decode('utf8')

  soup = BeautifulSoup(proxies_doc, 'html.parser')
  proxies_table = soup.find(id='proxylisttable')

  # Save proxies in the array
  for row in proxies_table.tbody.find_all('tr'):
    proxies.append({
      'ip':   row.find_all('td')[0].string,
      'port': row.find_all('td')[1].string
    })

  # Choose a random proxy
  proxy_index = random_proxy()
  proxy = proxies[proxy_index]

  for n in range(1, 20):
    req = Request('http://icanhazip.com')
    req.set_proxy(proxy['ip'] + ':' + proxy['port'], 'http')

    # Every 10 requests, generate a new proxy
    if n % 10 == 0:
      proxy_index = random_proxy()
      proxy = proxies[proxy_index]

    # Make the call
    try:
      my_ip = urlopen(req).read().decode('utf8')
      print('#' + str(n) + ': ' + my_ip)
      clear_output(wait = True)
    except: # If error, delete this proxy and find another one
      del proxies[proxy_index]
      print('Proxy ' + proxy['ip'] + ':' + proxy['port'] + ' deleted.')
      proxy_index = random_proxy()
      proxy = proxies[proxy_index]

# Retrieve a random index proxy (we need the index to delete it if not working)
def random_proxy():
  return random.randint(0, len(proxies) - 1)



def parse(ticker):
    url = "http://finance.yahoo.com/quote/%s?p=%s" % (ticker, ticker)
    user_agent = random.choice(user_agent_list)
    headers = {'User-Agent': user_agent, "Accept-Language": "en-US, en;q=0.5"}
    if len(proxies)>0:
             proxy = random.choice(proxies)
             response = requests.get(url, headers=headers, proxies=proxy, verify=False)
    else:
        response = requests.get(url, headers=headers, verify=False)

    print("Parsing %s" % (url))
    sleep(4)
    parser = html.fromstring(response.text)
    summary_table = parser.xpath('//div[contains(@data-test,"summary-table")]//tr')
    summary_data = OrderedDict()
    other_details_json_link = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{0}?formatted=true&lang=en-US&region=US&modules=summaryProfile%2CfinancialData%2CrecommendationTrend%2CupgradeDowngradeHistory%2Cearnings%2CdefaultKeyStatistics%2CcalendarEvents&corsDomain=finance.yahoo.com".format(
        ticker)
    summary_json_response = requests.get(other_details_json_link)
    try:
        json_loaded_summary = json.loads(summary_json_response.text)
        y_Target_Est = json_loaded_summary["quoteSummary"]["result"][0]["financialData"]["targetMeanPrice"]['raw']
        earnings_list = json_loaded_summary["quoteSummary"]["result"][0]["calendarEvents"]['earnings']
        eps = json_loaded_summary["quoteSummary"]["result"][0]["defaultKeyStatistics"]["trailingEps"]['raw']
        datelist = []
        for i in earnings_list['earningsDate']:
            datelist.append(i['fmt'])
        earnings_date = ' to '.join(datelist)
        for table_data in summary_table:
            raw_table_key = table_data.xpath('.//td[contains(@class,"C($primaryColor)")]//text()')
            raw_table_value = table_data.xpath('.//td[contains(@class,"Ta(end)")]//text()')
            table_key = ''.join(raw_table_key).strip().replace(".","")
            table_value = ''.join(raw_table_value).strip()
            summary_data.update({table_key: table_value})
        summary_data.update(
            {'1y Target Est': y_Target_Est, 'EPS (TTM)': eps, 'Earnings Date': earnings_date, 'ticker': ticker,
             'url': url})
        return {ticker:summary_data}
    except:
        print("Failed to parse json response")
        return {"error": "Failed to parse json response"}


app = Flask(__name__, static_url_path='')


@app.route('/')
def server():
    f = open('stocks.txt', 'r')
    stocks = f.readlines()
    print(stocks)
    f.close()
    scraped_data = parse(stocks[random.randrange(1, 99)].strip())
    print(scraped_data)
    return os.environ.get("MESSAGE", scraped_data)


def cron():
    myclient = pymongo.MongoClient(DBUrl)
    f = open('stocks.txt', 'r')
    stocks = f.readlines()
    f.close()
    try:
        scraped_data = parse(stocks[random.randrange(1, 99)].strip())
        mydb = myclient["data"]
        mycol = mydb["stocks"]
        mycol.insert_one(scraped_data)
        print("data saved",scraped_data)
    except:
        print("Failed to scrape data")


sched = BackgroundScheduler(daemon=True)
sched.add_job(cron,'interval',minutes=2)
sched.add_job(loadProxies,'interval',minutes=15)
sched.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host='localhost', port=port, debug=True)
