from fastapi.middleware.cors import CORSMiddleware


def get_cors_middleware(app):
    origins = [
        "http://localhost:8000",
        "http://localhost",
        "https://localhost:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=[
            "*",
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Requested-With",
        ],
    )
