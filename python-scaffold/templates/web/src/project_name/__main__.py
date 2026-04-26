import uvicorn

from {{project_name_snake}}.config import settings


def main() -> None:
    uvicorn.run(
        "{{project_name_snake}}.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
    )


if __name__ == "__main__":
    main()
