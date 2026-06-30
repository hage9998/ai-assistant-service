from fastapi import FastAPI


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Gamification of Life - AI-Assistant Service",
        description=(
            "API for the AI-Assistant Service. "
            "See the [documentation](/docs) for more information."
        ),
        version="1.0.0",
    )

    return app


app = create_app()
