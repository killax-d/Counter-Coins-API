from firebase_admin import credentials, firestore, initialize_app

FIREBASE_CREDENTIALS = credentials.Certificate('key.json')
FIREBASE_APP = initialize_app(FIREBASE_CREDENTIALS)
FIREBASE_DB = firestore.client()
FIREBASE_USERS = FIREBASE_DB.collection('users')

class UsersService:

    def __init__(self):
        pass

    
    def getUserId(self, request):
        if request.args.get("uid") is not None:
            return request.args.get("uid")
        else:
            return None


    def getReports(self, user_id):
        reports = FIREBASE_USERS.document(user_id).get().to_dict()
        if reports is None:
            reports = {}
        # Reverse order
        return reports.get("reports", [])[::-1]

    def setReports(self, user_id, reports):
        FIREBASE_USERS.document(user_id).set({
            "reports": reports
        })