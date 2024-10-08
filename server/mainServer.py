from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import librosa
import csv
import io
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
uri = os.getenv("mongodburi")

client = MongoClient(uri, server_api=ServerApi("1"))
# Send a ping to confirm a successful connection
db = client["whisper-wave-pennapps"]  # Your database name


def csv_to_list(file_path):
    result = []
    try:
        with open(file_path, "r", newline="") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)
            for row in csv_reader:
                result.append(row[2])
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except csv.Error as e:
        print(f"CSV Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return result


class_names = csv_to_list("yamnet_class_map.csv")


app = FastAPI()


class SignInRequest(BaseModel):
    username: str
    password: str


@app.post("/signInUser")
async def signInUser(loginInfo: SignInRequest):
    print("here")
    collection = db["users"]  # Your collection name

    doc = {"username": f"{loginInfo.username}", "password": f"{loginInfo.password}"}
    print(loginInfo.password)
    try:
        for user in collection.find():
            print("iteration")
            print(f"Password Doc: {user['username']}")
            print(f"{user['password']}")
            if (
                user["username"] == loginInfo.username
                and user["password"] == loginInfo.password
            ):
                print("done")
                return {"message": "user successfully signed in"}
    except AttributeError as e:
        print(f"user has no attribute {e}")
        print("error on username")
        return {"message": "err!"}
    except Exception as e:
        print(e)
        print("line 72")
    print("couldn't find anyone")
    return {"message": "couldn't find user"}


@app.post("/registerUser")
async def registerUser(loginInfo: SignInRequest):
    print("here")
    collection = db["users"]  # Your collection name
    print(loginInfo.username)
    print(loginInfo.password)
    doc = {"username": f"{loginInfo.username}", "password": f"{loginInfo.password}"}
    try:
        for user in collection.find():
            print("iteration")
            print(user["username"])
            print(user["password"])
            if user["username"] == loginInfo.username:
                print("done")
                return {"message": "account already exists"}
        collection.insert_one(
            {"username": loginInfo.username, "password": loginInfo.password}
        )
    except Exception as e:
        print(e)
        print("line 72")
    return {"message": "user successfully registered"}


class soundRequst(BaseModel):
    sound: str
    username: str
    date: str


@app.post("/storeSounds")
async def storeSoundsFromUsers(soundReq: soundRequst):
    print("nothing")
    collection = db["userOutputs"]
    collection.insert_one(
        {"sound": soundReq.sound, "username": soundReq.username, "date": soundReq.date}
    )
    return {"message": "successfully added"}


class storyRequest(BaseModel):
    story: str
    username: str
    tone: str


@app.post("/storeStories")
async def storeSoundsFromUsers(storyReq: storyRequest):
    print("nothing")
    collection = db["userStories"]
    collection.insert_one(
        {"story": storyReq.story, "username": storyReq.username, "tone": storyReq.tone}
    )
    return {"message": "success"}


class addToNotes(BaseModel):
    notesDocument: object
    username: str


@app.post("/storeNotes")
async def storeNotesFromUsers(noteReq: addToNotes):
    try:
        noteString = "\n"
        print(noteReq.notesDocument.splitlines())
        print("line 147")
        for x in noteReq.notesDocument.splitlines()[2:]:
            noteString += "\n" + x
        collection = db["userNotes"]
        print(noteString)
        collection.insert_one(
            {
                "notesDocument": noteString,
                "username": noteReq.username,
                "title": noteReq.notesDocument.splitlines()[0],
            }
        )
        return {"message": "Notes added successfully"}
    except Exception as e:
        print(e)
        return {"message": "Was not successful"}


class queryRequest(BaseModel):
    username: str


@app.post("/querySounds")
async def querySounds(queryReq: queryRequest):
    collection = db["userOutputs"]
    retArry = []
    print(queryReq.username)
    for doc in collection.find():
        if doc["username"] == queryReq.username:
            print("here")
            print(type(doc["sound"]))
            retArry.append(doc["sound"])
            print("appending")
            print(doc)

    if len(retArry) == 0:
        return {"message": "no results found"}
    print("returning everything")
    return {"message": retArry}


@app.post("/queryNotes")
async def queryNotes(queryReq: queryRequest):
    collection = db["userNotes"]
    retArry = []
    print(queryReq.username)
    for doc in collection.find():
        print(doc["username"] == queryReq)
        if doc["username"] == queryReq.username:
            print("here")
            print(type(doc["username"]))
            print(doc)
            retArry.append({"note": doc["notesDocument"], "title": doc["title"][7:]})

    if len(retArry) == 0:
        return {"message": "no results found"}
    return {"message": retArry}


@app.post("/queryStories")
async def queryStories(queryReq: queryRequest):
    collection = db["userStories"]
    retArry = []
    print(queryReq.username)
    for doc in collection.find():
        print(doc["username"] == queryReq)
        if doc["username"] == queryReq.username:
            print("here")
            print(type(doc["username"]))
            print(doc)
            retArry.append({"story": doc["story"], "tone": doc["tone"]})

    if len(retArry) == 0:
        return {"message": "no results found"}
    return {"message": retArry}


@app.post("/clearSoundCache")
async def clearSoundCache(queryReq: queryRequest):
    collection = db["userOutputs"]
    collection.delete_many({"username": queryReq.username})
    return {"message": "Thing Delete Successfully"}


@app.post("/clearStoryCache")
async def clearSoundCache(queryReq: queryRequest):
    collection = db["userStories"]
    collection.delete_many({"username": queryReq.username})
    return {"message": "Thing Delete Successfully"}


@app.post("/clearNoteCache")
async def clearSoundCache(queryReq: queryRequest):
    collection = db["userNotes"]
    collection.delete_many({"username": queryReq.username})
    return {"message": "Thing Delete Successfully"}


@app.get("/test")
async def testApi():
    return {"message": "bottle"}


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load YAMNet model
model = hub.load("https://tfhub.dev/google/yamnet/1")


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read and preprocess the audio file
    contents = await file.read()
    with open("output", "wb") as f:
        f.write(contents)

    audio, sr = librosa.load("output", sr=16000, mono=True)

    # Make prediction
    scores, embeddings, spectrogram = model(audio)
    class_scores = tf.reduce_mean(scores, axis=0)
    top_classes = tf.argsort(class_scores, direction="DESCENDING")[:3]

    # Get class names
    top_class_names = [class_names[i] for i in top_classes.numpy()]

    # Prepare results
    results = [
        {"class": name, "score": float(class_scores[i])}
        for i, name in zip(top_classes, top_class_names)
    ]

    return {"predictions": results}
