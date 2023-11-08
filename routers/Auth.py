from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from classes.schema_dto import User
from firebase_admin import auth
from database.firebase import authShop


router = APIRouter(tags=["Auth"], prefix="/auth")


# create new user
@router.post("/signup", status_code=201)
async def create_an_account(user_body: User):
    try:
        user = auth.create_user(email=user_body.email, password=user_body.password)
        return {"message": f"Nouvel utilisateur créé avec id : {user.uid}"}
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=409, detail=f"Un compte existe déjà pour : {user_body.email}"
        )


@router.post("/login")
async def create_swagger_token(user_credentials: OAuth2PasswordRequestForm = Depends()):
    try:
        print(user_credentials)
        user = authShop.sign_in_with_email_and_password(
            email=user_credentials.username, password=user_credentials.password
        )
        token = user["idToken"]
        print(token)
        return {"access_token": token, "token_type": "bearer"}
    except:
        raise HTTPException(status_code=401, details="Invalid Credentials")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(provided_token: str = Depends(oauth2_scheme)):
    decoded_token = auth.verify_id_token(provided_token)
    decoded_token["idToken"] = provided_token
    return decoded_token


# Protect route to get personal data
@router.get("/me")
def secure_endoint(userData: int = Depends(get_current_user)):
    return userData
