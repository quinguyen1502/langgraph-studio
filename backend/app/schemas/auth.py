from pydantic import BaseModel


class Credentials(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str


class TokenOut(BaseModel):
    token: str
    user: UserOut
