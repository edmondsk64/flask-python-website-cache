import MySQLdb
conn = MySQLdb.connect(host= "localhost",
                  user="root",
                  passwd="1234",
                  db="ierg4080")
x = conn.cursor()

try:
   x.execute("""INSERT INTO urls (url, title, description ) VALUES (%s,%s, %s)""",("http://google.com","title is ", "discodsadsa"))
   conn.commit()
except Exception as e:
   conn.rollback()

conn.close()

