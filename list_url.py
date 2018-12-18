import MySQLdb
from collections import OrderedDict

conn = MySQLdb.connect(host= "localhost",user="root",passwd="1234",db="ierg4080")
x = conn.cursor()

try:
   x.execute("""SELECT * FROM urls ORDER BY submited_at ASC, id DESC LIMIT 5""")
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

print urls_list