# -*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, request, render_template
import string 
from string import digits
import json
from datetime import datetime
from random import randint
from urlparse import urlparse
from collections import OrderedDict, deque
import os
from PIL import Image
import requests
import redis
from bs4 import BeautifulSoup
import MySQLdb

app = Flask(__name__)

recent_uploads = deque(3*[0], 3)
json_img_uploads = "no upload"

@app.route('/')
def index():
   return 'Hello World'

@app.route('/submit_article',methods = ['POST', 'GET'])
def submit_article():
   if request.method == 'POST':
      submission = request.form['article']
   
	  #form.get for optional choices
      isIgnore = request.form.get('ignore_numbers')
      min_length = request.form.get('min_length')

   elif request.method == 'GET':
      submission = request.args.get('article')
      isIgnore = request.args.get('ignore_numbers')
      min_length = request.args.get('min_length')
   else:
      raise ValueError('Use POST and GET method instead')

   #Handle None input
   if (submission == None or submission == ''):
      submission = ''
   if (min_length == None or min_length == ''):
      min_length = 0
   if (isIgnore == None or isIgnore == ''):
      isIgnore = 0
	  
   wordcount={}

   #Covert to ascii and ignore those which cannot e.g £;
   submission = submission.encode('ascii',errors='ignore')
   
   #Replace punctuation with space; Convert to lower case
   submission = submission.translate(string.maketrans(string.punctuation, ' '*len(string.punctuation))).lower()

   #Remove words in dict which shorter than min_length
   submission = ' '.join([w for w in submission.split() if len(w)>=int(min_length)])
   
   #If isIgnore is set to 1, remove all digits
   if(isIgnore == '1'):
       submission = submission.translate(None, digits)
 
   #Word count
   for word in submission.split():
       if word not in wordcount:
          wordcount[word] = 1
       else: 
          wordcount[word] += 1
		  
   #Perform secondary sort which sorted according to value first, then key
   wordcount =  sorted(wordcount.items(), key=lambda x: (-x[1], x[0]))

   #Output result in JSON format
   
   return json.dumps(OrderedDict([('status', 'success'), ('port', urlparse(request.url).port), ('unique_words',len(wordcount)), ('words',wordcount)]))

@app.route('/submit_image',methods = ['POST'])
def submit_image():   
   global recent_uploads
   global json_img_uploads

   if request.method == 'POST':
      submission = request.form['image']
	  
   if (submission == None or submission == ''):
      submission = ''
   submission = submission.decode('base64')
   
   utc_now = datetime.utcnow()

   filename =  "{:%Y%m%d-%H%M%S}".format(utc_now) + '-' + ''.join(["%s" % randint(0, 9) for num in range(0, 5)])
   temp = filename + '.jpeg'
   
   fh = open(os.path.join('/home/ubuntu/static/images',temp), "wb")
   fh.write(submission)
   fh.close()
   
   img = Image.open(os.path.join('/home/ubuntu/static/images',temp))

   if(img.size[0] < img.size[1]):
      ratio = img.size[0]/64.0
      s0 = 64
      s1 = int(round(img.size[1] / ratio, 0))

      img = img.resize((s0,s1))
      img = img.crop((0, int(round((s1 - 64.0) / 2.0,0)),64,int(round((s1 + 64.0) / 2.0,0))))

      temp = filename + '.tn'
	  
      img.save(temp,"JPEG")
   else:
      ratio =img.size[1]/64.0
      s0 = int(round(img.size[0] / ratio, 0))
      s1 = 64

      img = img.resize((s0,s1))
      img = img.crop((int(round((s0 - 64.0) / 2.0,0)),0,int(round((s0 + 64.0) / 2.0,0)),64))
      temp = filename + '.tn'
      img.save(temp,"JPEG")

	  
   img_url = 'http://' + str(urlparse(request.url).hostname) + '/images/' + filename + '.jpeg';
   img_tn_url = 'http://' + str(urlparse(request.url).hostname) + '/images/' + filename + '.tn.jpeg';

   recent_uploads.appendleft(json_img_uploads)
   json_img_uploads = {'image_url':img_url, 'image_thumbnail_url':img_tn_url}
   
   #Output result in JSON format 
   recent_uploads_list = [recent_uploads[0],recent_uploads[1],recent_uploads[2]]

   json_list = [('status','success'),('port', urlparse(request.url).port), ('image_url',img_url), ('image_thumbnail_url',img_tn_url), ('recent_uploads', recent_uploads_list)]

   return json.dumps(OrderedDict(json_list))


@app.route('/submit_url',methods = ['POST'])
def submit_url():   
   submission = request.form['url']
   r = requests.get(submission)
   html_doc = r.text

   soup = BeautifulSoup(html_doc, 'html.parser')

   url = r.url
   re = redis.StrictRedis(host='localhost', port=6379, db=0)

   if re.get(url):
      return re.get(url)
   else:
      title =  soup.title.text

      description = ""

      submited_at = "{:%Y-%m-%d %H:%M:%S}".format(datetime.utcnow())

      if soup.find("meta",  property="og:description"):
            description = soup.find("meta",  property="og:description")["content"]
      elif soup.find("meta",  property="description"):
            description = soup.find("meta",  property="description")["content"]
      else:
            description = ""


      conn = MySQLdb.connect(host= "localhost",user="root",passwd="1234",db="ierg4080")
      x = conn.cursor()

      try:
            x.execute("""INSERT INTO urls (url, title, description, submited_at ) VALUES (%s,%s, %s,%s)""",(url,title,description,submited_at))
            conn.commit()

      except Exception as e:
            conn.rollback()

      conn.close()

      result_list =  OrderedDict([('url',url), ('title',title), ('description' , description),('submited_at' , submited_at) ])

      json_list = [('status','success'), ('result', result_list) , ('from_cache',0)]

      json_response = json.dumps(OrderedDict(json_list))
      json_response_cache = json.dumps(OrderedDict([('status','success'), ('result', result_list) , ('from_cache',1)]))
  
      re.set(url, json_response_cache)

      return json_response
	  
   return 0
	
@app.route('/list_urls')
def list_urls():

   conn = MySQLdb.connect(host= "localhost",user="root",passwd="1234",db="ierg4080")
   x = conn.cursor()

   try:
      x.execute("""SELECT * FROM urls ORDER BY submited_at ASC LIMIT 5""")
      result = x.fetchall()
      conn.commit()
   except Exception as e:
      conn.rollback()

   conn.close()


   urls_list = []

   for row in result:
      url =  str(row[1])
      title = str(row[2])
      description = str(row[3])
      submited_at = str(row[4])
      urls =  OrderedDict([('url',url), ('title',title), ('description' , description),('submited_at' , submited_at) ])
      urls_list.append(urls)
	  
   urls_list.reverse()
   return json.dumps(OrderedDict([('status','success'), ('urls', urls_list)]))
   

if __name__ == '__main__':
   app.run()