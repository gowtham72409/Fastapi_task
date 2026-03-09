from fastapi import APIRouter,Depends,HTTPException,status
from database import get_db
from sqlalchemy.orm import Session
import models
import schemas

router=APIRouter(prefix="/products",tags=["products"])

@router.post("/create")
def create_item(item:schemas.ProductCreate,db:Session=Depends(get_db)):
    db_item=models.Product(name=item.name,description=item.description,
                           price=item.price,category=item.category,quantity=item.quantity)
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return {"message":"Product Added"}

@router.get("/")
def get_all_item(db:Session=Depends(get_db)):
    db_item=db.query(models.Product).all()

    return db_item

@router.get("/{id}")
def get_one_item(item_id:int,db:Session=Depends(get_db)):
    db_item=db.query(models.Product).filter(models.Product.id==item_id).first()
    return db_item

@router.put("/update/{id}")
def update_item(id: int, update: schemas.ProductUpdate, db: Session = Depends(get_db)):

    db_item = db.query(models.Product).filter(models.Product.id == id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Product not found")

    db_item.name = update.name
    db_item.description = update.description
    db_item.price = update.price
    db_item.quantity = update.quantity
    db_item.category = update.category

    db.commit()
    db.refresh(db_item)

    return {"message": "Product updated", "data": db_item}

@router.delete("/{id}")
def delete_item(item_id:int,db:Session=Depends(get_db)):
    db_item=db.query(models.Product).filter(models.Product.id==item_id).first()
    db.delete(db_item)
    db.commit()
    return {"message":"Delete successfully"}

