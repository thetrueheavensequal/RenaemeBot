from pyrogram import Client
import os

api_id = input("Enter your API_ID: ")
api_hash = input("Enter your API_HASH: ")

with Client("session", api_id, api_hash) as app:
    print(f"\nYour session string:\n{app.export_session_string()}")
