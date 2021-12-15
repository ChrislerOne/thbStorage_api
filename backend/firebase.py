import firebase_admin
from firebase_admin import credentials, auth
from rest_framework import exceptions

cred = credentials.Certificate("firebaseCredentials.json")
default_app = firebase_admin.initialize_app(cred)
backend = firebase_admin.initialize_app(cred, name='backend')


def get_uid(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return uid
    except:
        pass



def get_user(uid: str):
    try:
        user = auth.get_user(uid=uid)
        return user
    except:
        print(uid)
        raise exceptions.PermissionDenied
