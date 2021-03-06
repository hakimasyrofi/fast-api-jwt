from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

json_filename="menu.json"
with open(json_filename,"r") as read_file:
	jsonData = json.load(read_file)

SECRET_KEY = "4b97e40df461128071d1abd62f3714eb09bac4e06c01b89e0aeef1ff46b17fc8" #openssl rand -hex 32
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20

admin = {
    "asdf": {
        "username": "asdf",
        "hashed_password": "$2a$10$kkTZ4TL0tTlayVG6w5eSWOkPmDKf0AeiHhtgYZ0vF90DcBQP4uK/W", #asdf encrypt with bcrypt hash
        "disabled": False,
    }
}

class Item(BaseModel):
	id: int
	name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(admin_db, username: str, password: str):
    user = get_user(admin_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(admin, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(admin, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/menu')
async def read_all_menu(current_user: User = Depends(get_current_active_user)):
	return jsonData['menu']

@app.get('/menu/{item_id}')
async def read_menu(item_id: int, current_user: User = Depends(get_current_active_user)):
	for menu_item in jsonData['menu']:
		if menu_item['id'] == item_id:
			return menu_item
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.post('/menu')
async def add_menu(item: Item, current_user: User = Depends(get_current_active_user)):
	item_dict = item.dict()
	item_found = False
	for menu_item in jsonData['menu']:
		if menu_item['id'] == item_dict['id']:
			item_found = True
			return "Menu ID "+str(item_dict['id'])+" exists."

	if not item_found:
		jsonData['menu'].append(item_dict)
		with open(json_filename,"w") as write_file:
			json.dump(jsonData, write_file)
		return item_dict

	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.patch('/menu')
async def update_menu(item: Item, current_user: User = Depends(get_current_active_user)):
	item_dict = item.dict()
	item_found = False
	for menu_idx, menu_item in enumerate(jsonData['menu']):
		if menu_item['id'] == item_dict['id']:
			item_found = True
			jsonData['menu'][menu_idx]=item_dict
			
			with open(json_filename,"w") as write_file:
				json.dump(jsonData, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.delete('/menu/{item_id}')
async def delete_menu(item_id: int, current_user: User = Depends(get_current_active_user)):

	item_found = False
	for menu_idx, menu_item in enumerate(jsonData['menu']):
		if menu_item['id'] == item_id:
			item_found = True
			jsonData['menu'].pop(menu_idx)
			
			with open(json_filename,"w") as write_file:
				json.dump(jsonData, write_file)
			return "updated"
	
	if not item_found:
		return "Menu ID not found."
	raise HTTPException(
		status_code=404, detail=f'item not found'
	)