import requests
from bs4 import BeautifulSoup
import MySQLdb
from datetime import datetime
from collections import OrderedDict, deque
import json
import redis

r = requests.get('http://www.bbc.com/news/technology-37713938')
html_doc = r.text

soup = BeautifulSoup(html_doc, 'html.parser')

url = r.url

title =  soup.title.text

description = ""

submited_at = "{:%Y-%m-%d %H:%M:%S}".format(datetime.utcnow())


if soup.find("meta",  property="og:description"):
        description = soup.find("meta",  property="og:description")["content"]
elif soup.find("meta",  property="description"):
        description = soup.find("meta",  property="description")["content"]
else:
        description = ""


conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd="1234",
                  db="ierg4080")
x = conn.cursor()

try:
   x.execute("""INSERT INTO urls (url, title, description, submited_at ) VALUES (%s,%s,%s,%s)""",(url,title,description,submited_at))
   conn.commit()

except Exception as e:
   conn.rollback()

conn.close()

result_list =  OrderedDict([('url',url), ('title',title), ('description' , description) ])

json_list = [('status','success'), ('result', result_list) , ('from_cache',0)]

re = redis.StrictRedis(host='localhost', port=6379, db=0)

re.set(url, OrderedDict(json_list))

print re.get(url)

print OrderedDict(json_list)
#return json.dumps(OrderedDict(json_list))








