from fastapi import FastAPI

# Import de la Documentation
from documentation.description import api_description
from documentation.tags import tags_metadata

# Import du router
import routers.ShopSmart
import routers.Auth
import routers.Stripe

# Initialisation de l'API
app = FastAPI(
    title="ShopSmart",
    description=api_description,
    openapi_tags=tags_metadata,
    docs_url="/",
)


# Inclusion des routes
app.include_router(routers.ShopSmart.router)
app.include_router(routers.Auth.router)
app.include_router(routers.Stripe.router)
