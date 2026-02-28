"""FastAPI application entry point for the Slack App."""

from fastapi import FastAPI

from slack_app.routers import users, messages, groups

app = FastAPI(
    title="Slack-Style Messaging API",
    description="A Slack-inspired messaging service with DMs and group chats.",
    version="1.0.0",
)

app.include_router(users.router)
app.include_router(messages.router)
app.include_router(groups.router)
