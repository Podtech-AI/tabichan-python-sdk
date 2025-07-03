#!/usr/bin/env python3

from tabichan.client import TabichanClient

client = TabichanClient()

task_id = client.start_chat(
    user_query="Plan a 2-day trip to Tokyo for this weekend",
    user_id="user123",
    country="japan",
)

print(task_id)

result = client.wait_for_chat(task_id)

print(result)
