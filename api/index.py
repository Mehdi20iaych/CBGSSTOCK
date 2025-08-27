import os

# Vercel Python entrypoint for FastAPI app using ASGI

from backend.server import app as fastapi_app


def handler(event, context):
	# For compatibility with Vercel's legacy handler interface; not used.
	return {"statusCode": 200, "body": "OK"}


# Expose module-level variable named `app` for Vercel's Python runtime (ASGI)
app = fastapi_app

