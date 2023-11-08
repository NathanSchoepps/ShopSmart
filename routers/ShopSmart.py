from fastapi import APIRouter, Depends, HTTPException
from typing import List
import uuid
from classes.schema_dto import Item, ShoppingList
from database.firebase import db
from routers.Auth import get_current_user

router = APIRouter(tags=["Lists"])


shopping_lists = [
    ShoppingList(category="Fruits", items=[Item(name="Pomme", quantity=4)]),
    ShoppingList(category="Legumes", items=[Item(name="Artichaut", quantity=2)]),
]


@router.get("/lists/", response_model=List[ShoppingList])
async def get_all_shopping_lists(userData: int = Depends(get_current_user)):
    stripe_sub = db.child("users").child(userData["uid"]).child("stripe").get().val()
    if not stripe_sub:
        raise HTTPException(status_code=401, detail="no subscription")
    status = (
        db.child("users")
        .child(userData["uid"])
        .child("stripe")
        .child("status")
        .get()
        .val()
    )
    if status != "active":
        raise HTTPException(status_code=401, detail="no active subscription")
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    return shopping_lists


@router.get("/lists/{category}", response_model=List[ShoppingList])
async def get_shopping_lists_by_category(
    category: str, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    lists = [s for s in shopping_lists if s["category"] == category]
    return lists


@router.post("/lists/", response_model=ShoppingList)
async def create_shopping_list(
    shopping_list: ShoppingList, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    if fireBaseobject is None:
        fireBaseobject = {}
    shopping_list_id = str(uuid.uuid4())
    fireBaseobject[shopping_list_id] = shopping_list.dict()
    # increment_stripe(userData["uid"])
    db.child("users").child(userData["uid"]).child("Shop").set(
        fireBaseobject, userData["idToken"]
    )
    return shopping_list


@router.post("/lists/{category}", response_model=ShoppingList)
async def add_item_to_shopping_list(
    category: str, item: Item, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    for shopping_list in shopping_lists:
        if shopping_list["category"] == category:
            shopping_list["items"].append(item.dict())
            # increment_stripe(userData["uid"])
            db.child("users").child(userData["uid"]).child("Shop").set(
                fireBaseobject, userData["idToken"]
            )
            return shopping_list
    raise HTTPException(status_code=404, detail="Shopping list not found")


@router.patch("/lists/{category}", response_model=ShoppingList)
async def patch_shopping_list(
    category: str, updated_name: str, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    for shopping_list in shopping_lists:
        if shopping_list["category"] == category:
            shopping_list["category"] = updated_name
            db.child("users").child(userData["uid"]).child("Shop").set(
                fireBaseobject, userData["idToken"]
            )
            return shopping_list
    raise HTTPException(status_code=404, detail="Shopping list not found")


@router.delete("/lists/{category}", response_model=ShoppingList)
async def delete_shopping_list_by_category(
    category: str, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    if fireBaseobject:
        for key, shopping_list in fireBaseobject.items():
            if shopping_list.get("category") == category:
                db.child("users").child(userData["uid"]).child("Shop").child(
                    key
                ).remove(userData["idToken"])
                return shopping_list
    raise HTTPException(status_code=404, detail="Shopping list not found")


@router.patch("/lists/{category}/items/{item_name}", response_model=ShoppingList)
async def patch_item_from_shopping_list(
    category: str,
    item_name: str,
    updated_name: str,
    userData: int = Depends(get_current_user),
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    for shopping_list in shopping_lists:
        if shopping_list["category"] == category:
            for item in shopping_list["items"]:
                if item["name"] == item_name:
                    item["name"] = updated_name
                    db.child("users").child(userData["uid"]).child("Shop").set(
                        fireBaseobject, userData["idToken"]
                    )
                    return shopping_list
    raise HTTPException(status_code=404, detail="Item not found in the shopping list")


@router.delete("/lists/{category}/items/{item_name}", response_model=ShoppingList)
async def delete_item_from_shopping_list(
    category: str, item_name: str, userData: int = Depends(get_current_user)
):
    fireBaseobject = (
        db.child("users")
        .child(userData["uid"])
        .child("Shop")
        .get(userData["idToken"])
        .val()
    )
    shopping_lists = [value for value in fireBaseobject.values()]
    for shopping_list in shopping_lists:
        if shopping_list["category"] == category:
            for item in shopping_list["items"]:
                if item["name"] == item_name:
                    shopping_list["items"].remove(item)
                    db.child("users").child(userData["uid"]).child("Shop").set(
                        fireBaseobject, userData["idToken"]
                    )
                    return shopping_list
    raise HTTPException(status_code=404, detail="Item not found in the shopping list")
