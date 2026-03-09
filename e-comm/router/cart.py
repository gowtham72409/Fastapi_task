from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from database import get_db
from router.auth import get_current_user
import models
import schemas

router=APIRouter(prefix="/cart",tags=["cart"])

@router.post("/")
def create_cart(item:schemas.CartAdd,current_user=Depends(get_current_user),
                db:Session=Depends(get_db)):
    cart=models.Cart(user_id=current_user.id,product_id=item.product_id,
                     quantity=item.quantity)
    
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return {"messade":"Item added in cart"}

@router.get("/")
def get_cart(current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    cart=db.query(models.Cart).filter(models.Cart.user_id==current_user.id).all()
    return cart