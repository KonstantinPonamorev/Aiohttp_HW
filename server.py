import json
import typing
import bcrypt
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.exc import IntegrityError
from aiohttp_pydantic import PydanticView
from pydantic import BaseModel


router = web.RouteTableDef()
app = web.Application()


PG_DSN = 'postgresql+asyncpg://app:secret@127.0.0.1:5431/app'
engine = create_async_engine(PG_DSN, echo=True)
Base = declarative_base()


async def hash_password(password: str, salt_rounds=12):
    password_bin = await password.encode('utf-8')
    hashed = await bcrypt.hshpw(password_bin, bcrypt.gensalt(salt_rounds))
    return await hashed.decode()


class HTTPError(web.HTTPException):

    def __init__(
            self,
            *,
            headers=None,
            reason=None,
            body=None,
            message=None
    ):
        json_response = json.dumps({'error': message})
        super().__init__(headers=headers, reason=reason, body=body,
                         text=json_response, content_type='application/json')


class BadRequest(HTTPError):
    status_code = 400


class NotFound(HTTPError):
    status_code = 400


class CreateUser(BaseModel):
    username: str
    password: str


class PatchUser(BaseModel):
    name: typing.Optional[str]
    password: typing.Optional[str]


class CreateAdvertisement(BaseModel):
    header: str
    description: str
    owner_id: int


class PatchAdvertisement(BaseModel):
    header: typing.Optional[str]
    description: typing.Optional[str]


class User(Base):

    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String, nullable=False)
    registration_time = Column(DateTime, server_default=func.now())


async def get_user(user_id: int, session) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise NotFound(message='User not found')
    return user


class UserView(web.View, PydanticView):

    async def get(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            return web.json_response({'username': user.username,
                                      'registration_time': int(user.registration_time.timestamp())})

    async def post(self, new_user: CreateUser):
        user_data = await self.request.json()
        new_user = User(username=user_data['username'],
                        password=await hash_password(user_data['password']))
        async with app.async_session_maker() as session:
            try:
                session.add(new_user)
                await session.commit()
                return web.json_response({'id': new_user.id,
                                          'username': new_user.username})
            except IntegrityError as er:
                raise BadRequest(message='user already exist')


    async def patch(self, user: PatchUser):
        user_id = int(self.request.match_info['user_id'])
        user_data = await self.request.json()
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            for column, value in user_data.items():
                setattr(user, column, value)
            session.add(user)
            await session.commit()
            return web.json_response({'status': 'success'})


    async def delete(self):
        user_id = int(self.request.match_info['user_id'])
        async with app.async_session_maker() as session:
            user = await get_user(user_id, session)
            await session.delete(user)
            await session.commit()
            return web.json_response({'status': 'success'})


app.add_routes([web.post('/users/', UserView)])
app.add_routes([web.get('/users/{user_id:\d+}', UserView)])
app.add_routes([web.patch('/users/{user_id:\d+}', UserView)])
app.add_routes([web.delete('/users/{user_id:\d+}', UserView)])


class Advertisement(Base):

    __tablename__ = 'advertisements'
    id = Column(Integer, primary_key=True)
    header = Column(String, index=True, unique=True, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    owner_id = Column(Integer, ForeignKey("user.id"))


async def get_advertisement(advertisement_id:int, session) -> Advertisement:
    advertisement = await session.get(Advertisement, advertisement_id)
    if not advertisement:
        raise NotFound(message='Advertisement not found')
    return advertisement


class AdvertisementView(web.View, PydanticView):

    async def get(self):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            return web.json_response({'header': advertisement.header,
                                      'owner_id': advertisement.owner_id})

    async def post(self, new_advertisement: CreateAdvertisement):
        advertisement_data = await self.request.json()
        new_advertisement = Advertisement(**advertisement_data)
        async with app.async_session_maker() as session:
            try:
                session.add(new_advertisement)
                await session.commit()
                return web.json_response({'id': new_advertisement.id,
                                          'header': new_advertisement.header})
            except IntegrityError as er:
                raise BadRequest(message='advertisement already exist')

    async def patch(self, advertisement: PatchAdvertisement):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        advertisement_data = await self.request.json()
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            for column, value in advertisement_data.items():
                setattr(advertisement, column, value)
            session.add(advertisement)
            await session.commit()
            return web.json_response({'status': 'success'})

    async def delete(self):
        advertisement_id = int(self.request.match_info['advertisement_id'])
        async with app.async_session_maker() as session:
            advertisement = await get_advertisement(advertisement_id, session)
            await session.delete(advertisement)
            await session.commit()
            return web.json_response({'status': 'success'})


app.add_routes([web.post('/advertisements/', AdvertisementView)])
app.add_routes([web.get('/advertisements/{advertisement_id:\d+}', AdvertisementView)])
app.add_routes([web.patch('/advertisements/{advertisement_id:\d+}', AdvertisementView)])
app.add_routes([web.delete('/advertisements/{advertisement_id:\d+}', AdvertisementView)])


async def init_orm(app: web.Application):
    print('Start app')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async_session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        app.async_session_maker = async_session_maker
        yield
    print('End app')


app.cleanup_ctx.append(init_orm)
web.run_app(app)
