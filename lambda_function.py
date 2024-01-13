import boto3
import cloudscraper
import os
import requests

URL = "https://www.lightnovelpub.com/novel/circle-of-inevitability-1513/chapter-{}"
TABLE_NAME = "lotm-update-notifier"
STATE_KEY = {"id": {"S": "state"}}
NEXT_CHAPTER_KEY = "next_chapter"

BOT_KEY = os.environ["BOT_KEY"]

dynamo = boto3.client("dynamodb")
scrapper = cloudscraper.create_scraper()


def lambda_handler(event, context):
    print("Retrieving state")
    state = dynamo.get_item(TableName=TABLE_NAME, Key=STATE_KEY).get("Item")
    print("State:", state)

    next_chapter = int(state.get(NEXT_CHAPTER_KEY).get("N"))
    print(f"Checking whether chapter {next_chapter} was released")
    resp = scrapper.get(URL.format(next_chapter))

    if resp.status_code == 404:
        print(f"Chapter {next_chapter} wasn't released yet")
        return

    if resp.status_code != 200:
        print(f"Unexpected status code: {resp.status_code}. Body: {resp.text}")
        return

    print(f"Chapter {next_chapter} was released")

    released_chapter = next_chapter
    next_chapter += 1
    for next_chapter in range(next_chapter, next_chapter + 10):
        print(f"Follow up: Checking whether chapter {next_chapter} was released")
        resp = scrapper.get(URL.format(next_chapter))
        if resp.status_code == 404:
            print(f"Chapter {next_chapter} wasn't released yet")
            break
        if resp.status_code != 200:
            print(f"Unexpected status code: {resp.status_code}. Body: {resp.text}")
            break
    else:
        # All 10 next chapters were released
        next_chapter += 1

    print("Updating state")
    dynamo.update_item(
        TableName=TABLE_NAME,
        Key=STATE_KEY,
        UpdateExpression=f"SET {NEXT_CHAPTER_KEY} = :{NEXT_CHAPTER_KEY}",
        ExpressionAttributeValues={f":{NEXT_CHAPTER_KEY}": {"N": str(next_chapter)}},
    )

    url = URL.format(released_chapter)
    count = next_chapter - released_chapter

    for chat_id in state.get("chat_ids").get("SS"):
        print(f"Sending message to chat {chat_id}")
        resp = requests.get(
            f"https://api.telegram.org/bot{BOT_KEY}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": f"{count} new {'chapter was' if count == 1 else 'chapters were'} released: {url}",
            },
        )
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} {resp.text}")
