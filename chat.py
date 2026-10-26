#start mr.robot 
print("I,M mr.robot!")
print('I,M master robot')
#===============start=================
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from database import get_db
from auth import decode_token, get_current_user
from decimal import Decimal
from storage import upload_file
from uuid import uuid4
from wallets import send_balance
router = APIRouter()

