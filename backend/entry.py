import os
import uvicorn


def main() -> None:
	host = os.environ.get("BACKEND_HOST", "127.0.0.1")
	port = int(os.environ.get("BACKEND_PORT", "8001"))
	uvicorn.run("backend.server:app", host=host, port=port, workers=1, reload=False)


if __name__ == "__main__":
	main()

