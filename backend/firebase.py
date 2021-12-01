import firebase_admin
from firebase_admin import credentials, auth
from rest_framework import exceptions

cred = credentials.Certificate("firebaseCredentials.json")
default_app = firebase_admin.initialize_app(cred)
backend = firebase_admin.initialize_app(cred, name='backend')


def get_uid(id_token: str):
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token['uid']
    return uid


def get_user(uid: str):
    try:
        user = auth.get_user(uid=uid)
        return user
    except:
        print(uid)
        raise exceptions.PermissionDenied

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
