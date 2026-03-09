from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from database import get_db
from router.auth import get_current_user
import models

router=APIRouter(prefix="/orders",tags=["orders"])

@router.post("/place")
def order_item(current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    cart_item=db.query(models.Cart).filter(models.Cart.user_id==current_user.id).all()
    total=0
    order=models.Order(
        user_id=current_user.id,
        total_price=0
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item in cart_item:
        product=db.query(models.Product).filter(models.Product.id==item.product_id).first()
        total+=product.price * item.quantity

        order_item=models.OrderItem(
            order_id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product.price
        )

        db.add(order_item)
        
        product.quantity-=item.quantity
    
    order.total_price=total

    db.query(models.Cart).filter(models.Cart.id==current_user.id).delete()
    db.commit

    return {"message":"oreder place","total":total}