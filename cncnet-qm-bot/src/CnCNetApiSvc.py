from apiclient import APIClient
from apiclient.exceptions import UnexpectedError, ServerError


class CnCNetApiSvc(APIClient):
    host = "https://ladder.cncnet.org"

    def fetch_stats(self, ladder):
        url = f"{self.host}/api/v1/qm/ladder/{ladder}/stats"
        return self.get_call(url)

    def fetch_ladders(self):
        url = f"{self.host}/api/v1/ladder"
        return self.get_call(url)

    def fetch_maps(self, ladder):
        url = f"{self.host}/api/v1/qm/ladder/{ladder}/maps/public"
        return self.get_call(url)

    def fetch_qms(self, ladder):
        url = f"{self.host}/api/v1/qm/ladder/{ladder}/current_matches"
        return self.get_call(url)

    def fetch_rankings(self):
        url = f"{self.host}/api/v1/qm/ladder/rankings"
        return self.get_call(url)

    def get_call(self, url):
        try:
            return self.get(url)
        except UnexpectedError as ue:
            print(ue.message)
            return None
        except ServerError as se:
            print(se)
            return None
