from pymongo import MongoClient

# specify the port in this case with mongo uri format
client = MongoClient("mongodb://localhost:27017") #27017 is the default port

# specify the db to be used
db = client.pymongo_test

posts = db.posts
post_data = {
    "title" : "Python and Mongodb",
    "content" : "Pymongo is fun you guys",
    "author" : "Gracia"
}

post_datas = [
    {
    "title" : "Python and Mongodb",
    "content" : "Pymongo is fun you guys",
    "author" : "Esther"
}
{
    "title" : "Python and Mongodb",
    "content" : "Pymongo is fun you guys",
    "author" : "Kui"
}
{
    "title" : "Python and Mongodb",
    "content" : "Pymongo is fun you guys",
    "author" : "Winnie"
}
{
    "title" : "Python and Mongodb",
    "content" : "Pymongo is fun you guys",
    "author" : "Alex"
}
]

result = posts.insert_one(post_data)
gracia = posts.find_one({"author":"Gracia"})
print("One post: {0}".format(result.inserted_id))
print(gracia)
