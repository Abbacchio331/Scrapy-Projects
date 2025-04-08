from json import loads
from ast import literal_eval
from regex import sub

with open("output.json", "r") as f:
    data = literal_eval(loads(f.read())[0]['data'])

responseurl = 'https://3m.wd1.myworkdayjobs.com/wday/cxs/3m/Search/jobs'

print(data['total'])
print([sub(r"/jobs\s*\Z", data['jobPostings'][i]['externalPath'], responseurl) for i in range(len(data['jobPostings']))])
