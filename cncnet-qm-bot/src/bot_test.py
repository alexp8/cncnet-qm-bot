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
        ladders.append(item['abbreviation'])

    maps_json = api_client.fetch_maps("yr")
    maps = []
    for item in maps_json:
        maps.append(item['description'])

    if 'test' not in ladders:
        print('test is not a valid ladder from (' + ', '.join(ladders) + ")")


class MyClient(APIClient):

    def fetch_ladders(self):
        url = "http://localhost:8000/api/v1/ladder"
        return self.get(url)

    def fetch_maps(self, ladder):
        url = "http://localhost:8000/api/v1/qm/ladder/" + ladder + "/maps/public"
        return self.get(url)


if __name__ == "__main__":
    main()
