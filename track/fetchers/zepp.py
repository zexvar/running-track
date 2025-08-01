import json
from urllib.parse import urljoin

import requests


class ZeppFetcher:
    base_url = "https://api-mifit.huami.com"

    def __init__(self, token):
        self.headers = {
            "apptoken": token,
            "appname": "com.xiaomi.hm.health",
            "appPlatform": "web",
        }

    def fetch(self, endpoint: str, params):
        data = requests.get(
            url=urljoin(self.base_url, endpoint),
            headers=self.headers,
            params=params,
        ).json()

        if data["message"] != "success":
            print((data["message"]))
            print((data))

        return data["data"]

    def get_record_detail(self, record_id: int, record_source: str):
        print(f"Fetching record {record_id}")
        return self.fetch(
            endpoint="/v1/sport/run/detail.json",
            params={
                "trackid": record_id,
                "source": record_source,
            },
        )

    def get_records_info_list(self):
        result = []

        def fetch_history(start_id: int = None):
            print(f"Fetching records starting from id {next or 0}")
            return self.fetch(
                endpoint="/v1/sport/run/history.json",
                params={"trackid": start_id} if start_id is not None else {},
            )

        next = None
        while next != -1:
            data = fetch_history()
            result.extend(data["summary"])
            next = data["next"]

        print(f"There are {len(result)} records in total")
        return result

    def save_records_data(self, save_path):
        records_info = self.get_records_info_list()
        records = []
        for i in records_info:
            print(i["trackid"])
            record_id = i["trackid"]
            record_source = i["source"]
            record_detail = self.get_record_detail(record_id, record_source)
            record_data = {**i, **record_detail}
            print(f"Writing json file {record_id}.json")
            with open(f"{save_path}/{record_id}.json", "w", encoding="utf-8") as file:
                file.write(json.dumps(record_data, ensure_ascii=False, indent=2))
            records.append(record_data)
        return records
