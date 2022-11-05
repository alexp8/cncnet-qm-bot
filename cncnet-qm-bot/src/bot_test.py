# bot.py
from apiclient import APIClient, JsonResponseHandler

global api_client
global ladders


def main():
    global api_client
    api_client = MyClient(
        response_handler=JsonResponseHandler
    )

    global ladders
    ladders = []
    ladders_json = api_client.fetch_ladders()
    for item in ladders_json:
        if item["private"] == 0:
            ladders.append(item['abbreviation'])

    maps_json = api_client.fetch_maps("blitz")
    maps = []
    for item in maps_json:
        maps.append(item['description'])

    print("```\n" + '\n'.join(maps) + "\n```")


class MyClient(APIClient):
    global host
    host = "https://ladder.cncnet.org"
    # host = "http://localhost:8000"

    def fetch_ladders(self):
        url = host + "/api/v1/ladder"
        return self.get(url)

    def fetch_maps(self, ladder):
        url = host + "/api/v1/qm/ladder/" + ladder + "/maps/public"
        return self.get(url)


if __name__ == "__main__":
    main()
