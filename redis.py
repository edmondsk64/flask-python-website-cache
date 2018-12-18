import redis

re = redis.StrictRedis(host='localhost', port=6379, db=0)

re.set('foo', 'bar')

print re.get('ds')