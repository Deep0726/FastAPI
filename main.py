from fastapi import FastAPI, Depends, HTTPException, Path
from typing import  Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status

import models
from database import SessionLocal
from database import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=500)
    priority: int = Field(gt=0, lt=6)
    complete: bool


def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/",status_code=status.HTTP_200_OK)
def read_all(db: db_dependency):
    return  db.query(models.Todos).all()

@app.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
def get_todo_by_id(db: db_dependency, todo_id: int = Path(gt=0) ):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()
    if todo_model is not  None:
        return  todo_model
    raise HTTPException(status_code=404, detail="Todo not found")

@app.post("/todo", status_code= status.HTTP_201_CREATED)
def create_todo(db:db_dependency , todo_request: TodoRequest):
    todo_model = models.Todos(**todo_request.dict())
    db.add(todo_model)
    db.commit()

@app.put("/todo/{todo_id}", status_code= status.HTTP_204_NO_CONTENT)
def update_todo(db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(db: db_dependency,todo_id: int = Path(gt=0)):
    todo_model = db.query(models.Todos).filter(models.Todos.id  == todo_id).first()

    if todo_model is None:
        raise HTTPException(status_code=404,detail= "Todo not found")
    db.delete(todo_model)
    db.commit()