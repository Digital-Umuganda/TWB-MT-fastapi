from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.helpers.config import Config


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #origins when origins is set
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    from app.views.v1.translate import translate_v1
    from app.views.v1.translate_html import translate_html
    from app.views.v1.translate_markdown import translate_markdown


    app.include_router(translate_v1)
    app.include_router(translate_html)
    app.include_router(translate_markdown)


    @app.on_event('startup')
    async def startup_event() -> None:
        config = Config(load_all_models=True)

    return app
