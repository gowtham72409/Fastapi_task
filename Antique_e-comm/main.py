from fastapi import FastAPI,Depends
from sqlalchemy.orm import Session
from database import Base,engine,get_db
import models
import schemas

app=FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/create",)
def create_antique(antique:schemas.AntiqueCreate,db:Session=Depends(get_db)):
    item=models.Product(name=antique.name,description=antique.description,
                              price=antique.price,category=antique.category)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"message":"Create successfully"}

@app.get("/antique")
def get_all_antique(db:Session=Depends(get_db)):
    item=db.query(models.Product).all()
    return item

@app.get("/antique/{id}")
def get_one_antique(antique_id:int,db:Session=Depends(get_db)):
    item=db.query(models.Product).filter(models.Product.id==antique_id).first()
    return item

@app.put("/antique/{id}")
def update_antique(antique_id: int, antique: schemas.AntiqueCreate,db: Session=Depends(get_db)):
    item=db.query(models.Product).filter(models.Product.id==antique_id).first()
    if not item:
        return {"message":"Invalid Item"}
    item.name=antique.name,
    item.description=antique.description,
    item.price=antique.price,
    item.category=antique.category

    db.commit()
    db.refresh(item)
    return item

@app.delete("/antique/{id}")
def delete_antique(antique_id: int,db: Session=Depends(get_db)):
    item=db.query(models.Product).filter(models.Product.id==antique_id).first()
    if not item:
        return {"message":"Invalid Item"}
    
    db.delete(item)
    db.commit()
    return {"message":"Remove the Item"}

