from cryptography.fernet import Fernet
import pymongo
import os

def path():
    #os.chdir('..')
    cwd = os.getcwd()
    return cwd + '\\key.dat'

def gen_key():
    key = Fernet.generate_key()
    f = open(path(),'wb+')
    f.write(key)
    f.close()

def encrypt(msg):
    f = open(path(),'r')
    key = f.read()
    f.close()
    f = Fernet(key)
    e_msg = f.encrypt(msg)  
    return e_msg

def decrypt(msg):
    f = open(path(),'r')
    key = f.read()
    f.close()
    f = Fernet(key)
    print(key)
    d_msg = f.decrypt(msg)
    return d_msg

msg = 'admin123'
msg = encrypt(msg.encode())

print(decrypt(msg).decode())
'''
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["mydatabase"]

x = {"Username": 'admin' , "Password": encrypt(b'admin123'), "Cache": 0}
result = db.admin.insert_one(x)

y = {"Username": 'anchor' , "Password": encrypt(b'anchor123'), "Cache": 0}
result = db.anchor.insert_one(y)'''

#gen_key()