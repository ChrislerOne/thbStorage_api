import firebase_admin
from firebase_admin import credentials, auth
from rest_framework import exceptions

cred = credentials.Certificate("python-project-90570-firebase-adminsdk-ns0dt-a6553dbe27.json")
default_app = firebase_admin.initialize_app(cred)
backend = firebase_admin.initialize_app(cred, name='backend')


# Creating Tokens for existing user
# from django.contrib.auth.models import User
# from rest_framework.authtoken.models import Token
#
# for user in User.objects.all():
#     Token.objects.get_or_create(user=user)

# TODO not working, connect django auth to firebase
def init(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token=id_token)
        uid = decoded_token['uid']
        return uid
    except:
        print(id_token)
        raise exceptions.PermissionDenied
# config = {
#     "apiKey": "AIzaSyB6l16KDDB_c_7s6mkoDkzikr_HmJUfMxI",
#     "authDomain": "python-project-90570.firebaseapp.com",
#     "storageBucket": "python-project-90570.appspot.com",
# }
#
# firebase = Firebase(config)
#
# auth = firebase.auth()
#
#
# def init():
#     pass
#
#
# def sign_in_email_pw(email, password):
#     try:
#         user = auth.sign_in_with_email_and_password(email, password)
#         return user
#     except:
#         pass
#
#
# def create_user_email_pw(email, password):
#     try:
#         auth.create_user_with_email_and_password(email, password)
#     except:
#         pass
#
#
# # def verify_email(user):
# #     auth.send_email_verification(user['idToken'])
# #
# #
# # def password_reset(email):
# #     auth.send_password_reset_email(email)
# #
#
# def account_info(user):
#     return auth.get_account_info(user['idToken'])
#
#
# def refresh_token(user):
#     auth.refresh(user['idToken'])
#     # TODO Maybe update DB
