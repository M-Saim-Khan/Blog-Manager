from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from typing import List,Optional
import strawberry
from strawberry.fastapi import GraphQLRouter

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, echo=True)

class Post(SQLModel, table = True):
    id:Optional[int] = Field(default=None , primary_key=True)
    title : str
    content : str
    authorid : int = Field(foreign_key="user.id")
    author : Optional["User"] = Relationship(back_populates="posts")


class User(SQLModel, table = True):
    id : Optional[int] = Field(default=None, primary_key=True)
    name:str
    email:str
    posts:List[Post] = Relationship(back_populates="author")

SQLModel.metadata.create_all(engine)

@strawberry.type
class PostType:
    id: int
    title : str
    content: str

@strawberry.type
class UserType:
    id : int
    name : str
    email : str
    posts:List[PostType]


@strawberry.type
class Query:
    @strawberry.field
    def get_user(self, id:int)->UserType:
        with Session(engine)as session:
            user = session.get(User,id)
            if not user:
                return HTTPException(status_code=404, detail="User not Found")
            return UserType(id = user.id, name = user.name, email = user.email, posts=[PostType(id=p.id, title=p.title, content=p.content) for p in user.posts])
    @strawberry.field
    def get_post(self, id:int)->PostType:
        with Session(engine)as session:
            post = session.get(Post, id)
            if not post:
                return HTTPException(status_code=404, detail="Post Not Found")
            return PostType(id = post.id, title = post.title, content = post.content)
        

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name:str, email:str)->UserType:
        with Session(engine) as session:
            new_user = User(name = name, email = email)
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return UserType(id = new_user.id, name = new_user.name, email = new_user.email, posts = [])
    @strawberry.mutation
    def create_post(self, title: str, content: str, author_id: int)->PostType:
        with Session(engine)as session:
            new_post = Post(title = title, content= content, authorid=author_id)
            session.add(new_post)
            session.commit()
            session.refresh(new_post)
            return PostType(id = new_post.id, title = new_post.title, content = new_post.content)
        
        
    @strawberry.mutation
    def delete_user(self, id:int)->bool:
        with Session(engine)as session:
            user = session.get(User, id)
            if not user:
                raise HTTPException(status_code=404, detail="User not Found")
                for post in user.posts:
                    session.delete(post)
                session.delete(user)
                session.commit()
            return True
        
schema = strawberry.Schema(query=Query, mutation=Mutation)

graphql_app = GraphQLRouter(schema)
app=FastAPI()
app.include_router(graphql_app, prefix='/graphql' )
