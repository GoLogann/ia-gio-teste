import asyncio
import time
import logging
from fastapi import FastAPI

from auth.setup import setup_auth_client

logger = logging.getLogger(__name__)

async def refresh_oauth_token(app: FastAPI):
    """Refreshes the OAuth2 token before expiration"""
    while True:
        token_data = app.state.token

        if not token_data:
            logger.warning("No token found, waiting 5 minutes before retrying...")
            await asyncio.sleep(300)
            continue

        expires_at = token_data.get("expires_at", 0)
        time_remaining = expires_at - time.time()
        refresh_threshold = 3600

        if time_remaining > refresh_threshold:
            wait_time = time_remaining - refresh_threshold
            logger.info(f"Token is valid. Next check in {wait_time:.0f} seconds.")
            await asyncio.sleep(wait_time)
            continue

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to refresh token (Attempt {attempt + 1}/{max_retries})...")
                oauth_client, new_token = setup_auth_client()
                app.state.oauth_client = oauth_client
                app.state.token = new_token
                logger.info("New token generated successfully.")

                next_check = new_token.get("expires_at", 0) - time.time() - refresh_threshold
                logger.info(f"Next token refresh scheduled in {next_check:.0f} seconds.")
                await asyncio.sleep(max(60, next_check))
                break
            except Exception as error:
                retry_delay = 2 ** attempt
                logger.error(f"Token refresh failed: {error}. Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
        else:
            logger.critical("Failed to refresh token after multiple attempts.")
            await asyncio.sleep(300)