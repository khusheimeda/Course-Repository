from pymongo import MongoClient
import pandas as pd
from pprint import pprint

def csv_from_excel(nameoffile):
    data_xls = pd.read_excel(nameoffile + '.xlsx', 'Sheet1', index_col=1)
    data_xls.to_csv(nameoffile + '.csv', encoding='utf-8')


def convert(nameoffile):
    client = MongoClient()
    db = client.mydatabase
    if 'student' in nameoffile:
        data = db.student
    elif 'teacher' in nameoffile:
        data = db.teacher
    df = pd.read_csv(nameoffile) #csv file which you want to import
    records_ = df.to_dict(orient = 'records') #list of dictionaries in csv
    cursor = data.find({})
    temp = []
    for i in cursor:
        temp.append(i)
    print(temp) #list of dictionaries in mongodb

    flag = 0

    for x in records_: #dictionary from csv
        for y in temp: #dictionary from mongodb
            if x["Username"] == y["Username"]:
                flag=1
                break
        if flag == 0 and 'student' in nameoffile:
            result = db.student.insert_one(x)
        elif flag==0 and 'teacher' in nameoffile:
            result = db.teacher.insert_one(x)
        flag = 0

    cursor = data.find({})
    for document in cursor:
        pprint(document)
