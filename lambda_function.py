import boto3
import cloudscraper
import os
import re
import requests

HUNDREDTH_REGRESSOR_CHAPTERS_URL = "https://translatinotaku.net/novel/the-100th-regression-of-the-max-level-player/ajax/chapters/"
TABLE_NAME = "lotm-update-notifier"
HUNDREDTH_REGRESSOR_STATE_KEY = {"id": {"S": "hundredth-regressor-state"}}
NEXT_CHAPTER_KEY = "next_chapter"

BOT_KEY = os.environ["BOT_KEY"]

dynamo = boto3.client("dynamodb")
scrapper = cloudscraper.create_scraper()


class Handler:
    def __init__(self, name: str, state_key) -> None:
        self.name = name
        self.state_key = state_key

        self.log("Retrieving state")
        self.state = dynamo.get_item(TableName=TABLE_NAME, Key=state_key).get("Item")
        self.log("State:", self.state)

    def log(self, *msg):
        print(f"{self.name}:", *msg)

    def get_int(self, key: str) -> int:
        return int(self.state.get(key).get("N"))

    def set_int(self, key: str, value: int) -> None:
        self.log("Updating state", key, "=", value)
        dynamo.update_item(
            TableName=TABLE_NAME,
            Key=self.state_key,
            UpdateExpression=f"SET {key} = :{key}",
            ExpressionAttributeValues={f":{key}": {"N": str(value)}},
        )

    def send_to_all(self, count, url) -> None:
        for chat_id in self.state.get("chat_ids").get("SS"):
            self.log(f"Sending message to chat {chat_id}")
            resp = requests.get(
                f"https://api.telegram.org/bot{BOT_KEY}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": f"{self.name}: {count} new {'chapter was' if count == 1 else 'chapters were'} released: {url}",
                    "link_preview_options": {
                        "is_disabled": True,
                    },
                },
            )
            if resp.status_code != 200:
                self.log(f"Error: {resp.status_code} {resp.text}")


class HundredthRegressorHandler(Handler):
    def __init__(self):
        super().__init__("100th", HUNDREDTH_REGRESSOR_STATE_KEY)

    def check(self):
        next_chapter = self.get_int(NEXT_CHAPTER_KEY)
        self.log(f"Checking whether chapter {next_chapter} was released")
        resp = scrapper.post(HUNDREDTH_REGRESSOR_CHAPTERS_URL)

        if resp.status_code != 200:
            self.log(f"Unexpected status code: {resp.status_code}. Body: {resp.text}")
            return

        chapter_urls = re.findall(r'href="(http[^"]+)"', resp.text)

        if len(chapter_urls) < next_chapter - 1:
            self.log("Fewer chapters than expected:", len(chapter_urls))
            self.log(chapter_urls)
            return
        elif len(chapter_urls) < next_chapter:
            self.log("No new chapters")
            return

        count = len(chapter_urls) - next_chapter + 1
        print(f"{count} new chapters")

        self.set_int(NEXT_CHAPTER_KEY, len(chapter_urls) + 1)

        url = chapter_urls[-next_chapter]

        self.send_to_all(count, url)


def lambda_handler(event, context):
    HundredthRegressorHandler().check()
