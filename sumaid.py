from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Set up the templates directory
templates = Jinja2Templates(directory="templates")

class Product(BaseModel):
    name:str
    description:str
    price:int
    quantity:int

products = [
    {
        "product_id": 1,
        "name": "Smartphone",
        "description": "A smartphone with 128GB storage and a high-quality camera.",
        "price": 700,
        "quantity": 15
    },
    {
        "product_id": 2,
        "name": "Laptop",
        "description": "A laptop with 16GB RAM and 512GB SSD storage.",
        "price": 1200,
        "quantity": 10
    },
    {
        "product_id": 3,
        "name": "Pen",
        "description": "A smooth-writing blue ink ballpoint pen.",
        "price": 2,
        "quantity": 100
    },
    {
        "product_id": 4,
        "name": "Table",
        "description": "A wooden study table suitable for home or office use.",
        "price": 150,
        "quantity": 8
    }
]

@app.get("/products")
def get_all_prod():
    return products


@app.get("/product/{ID}")
def get_prod_by_id(ID:int):

    for product in products:
        if product["product_id"] == ID:
            return product
        
    return "product not found"

@app.post("/product")
def add_prod(prod: dict = Body(...)):
    products.append(prod)
    return prod

@app.put ("/product/{id}")
def update_cart(id:int,product:Product):
    for p in products:
        if p["product_id"] == id:
            p.update(product.model_dump())
            return{
                "message": "product update successfully",
                "product": p
            }

    return {"message": "product not found"}     


@app.delete("/product/{id}")
def delete_product(id:int):
    for p in products:
        if p["product_id"] == id:
            products.remove(p)
            return {
                "message": "product deleted successfully",
                "product": p
            }
    return {"message": "product not found"}