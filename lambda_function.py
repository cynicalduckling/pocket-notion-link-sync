import requests, json, time, os
from dotenv import load_dotenv

load_dotenv()


class Pocket:
    def __init__(self, consumer_key, access_token, base_url):
        self.access_token = access_token
        self.consumer_key = consumer_key
        self.headers = {"Content-Type": "application/json"}
        self.base_url = base_url

    def get_items(self):
        url = self.base_url + "/get"

        params = {
            "consumer_key": self.consumer_key,
            "access_token": self.access_token,
        }

        response = requests.post(url=url, headers=self.headers, data=json.dumps(params))

        response_dict = response.json()["list"]

        blocks = [
            {
                "type": "bookmark",
                "bookmark": {
                    "url": item["resolved_url"],
                    "caption": [
                        {
                            "type": "text",
                            "text": {
                                "content": item["excerpt"][0:279].replace("\n", " "),
                                "link": None,
                            },
                            "annotations": {
                                "bold": True,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "",
                            "href": None,
                        }
                    ],
                },
            }
            for item in [response_dict[key] for key in response_dict.keys()]
        ]

        id_content = {
            x: {
                "title": response_dict[x]["excerpt"][0:279].replace("\n", " "),
                "url": response_dict[x]["resolved_url"],
            }
            for x in response_dict
        }
        print(f"Get blocks: ", response)

        return blocks, id_content


class Notion:
    def __init__(self, auth_token, base_url):
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "accept": "application/json",
            "Notion-Version": "2022-06-28",
            "content-type": "application/json",
        }
        self.base_url = base_url

    def delete_blocks(self, page_size=None):
        blocks_url = f"{self.base_url}/blocks/009e563a87e648d090ac4d300351230c/children?page_size=100"

        response = requests.get(url=blocks_url, headers=self.headers)
        responses = [
            (
                time.sleep(0.1),
                requests.delete(
                    url=f"https://api.notion.com/v1/blocks/{block_id}",
                    headers=self.headers,
                ),
            )
            for block_id in [x["id"] for x in response.json()["results"]]
        ]

        print("Delete blocks: <Response [200]>")

        return self

    def append_blocks(self, blocks):

        blocks_url = f"{self.base_url}/blocks/009e563a87e648d090ac4d300351230c/children"

        body = {"children": blocks}

        response = requests.patch(
            url=blocks_url, headers=self.headers, data=json.dumps(body)
        )

        print("Append blocks: ", response)

        return True


class Discord:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.headers = {"Content-Type": "application/json"}

    def send_request(self, content):
        url = self.webhook_url

        data = {
            "content": content,
            "username": "pocket",
            "avatar_url": "https://cdn.discordapp.com/attachments/431354432987594763/1073869298151464960/Pocket_service-Icon-White-Dark-Background-Logo.png",
        }

        requests.post(url=url, data=json.dumps(data), headers=self.headers)

    def discord_check(self, id_content):
        with open("discord_check.json", "r") as f:
            flags = json.load(f)

        for key in id_content:
            if key not in flags.keys():
                flags[key] = 0
            else:
                pass

        for key in id_content:
            title = id_content[key]["title"]
            url = id_content[key]["url"]
            if flags[key] == 0:
                self.send_request(
                    "**-----------------------------------------------------------------------------------------------------------------**\n\n>>> **"
                    + title
                    + "**\n\n"
                    + url
                )
                flags[key] = 1
            else:
                continue

        with open("discord_check.json", "w") as f:
            json.dump(flags, f, indent=4)

        print(f"Discord check: ", True)


def lambda_handler(event=None, context=None):
    blocks, id_content = Pocket(
        consumer_key=os.getenv("POCKET_CONSUMER_KEY"),
        access_token=os.getenv("POCKET_ACCESS_TOKEN"),
        base_url="https://getpocket.com/v3",
    ).get_items()

    flag = (
        Notion(
            auth_token=os.getenv("NOTION_AUTH_TOKEN"),
            base_url="https://api.notion.com/v1",
        )
        .delete_blocks()
        .append_blocks(blocks)
    )

    print(flag)

    Discord(webhook_url=os.getenv("WEBHOOK_URL")).discord_check(id_content)


lambda_handler()
