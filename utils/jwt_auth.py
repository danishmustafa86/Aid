from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from jwt import PyJWTError
import jwt
from fastapi.responses import JSONResponse

security = HTTPBearer()
def jwt_authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    SECRET_KEY = "5037ef22-57f6-417e-84a5-50070b064c87"
    ALGORITHM = "HS256"
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except PyJWTError:
        return JSONResponse(status_code=401, content={"error": "Invalid Token"})