import time
from hashlib import md5
from urllib.parse import quote

import requests

from track.utils.fio import write_json

get_md5_data = lambda data: md5(str(data).encode("utf-8")).hexdigest().upper()


class JoyrunAuth:
    def __init__(self, uid=0, sid=""):
        self.params = {}
        self.uid = uid
        self.sid = sid

    def reload(self, params={}, uid=0, sid=""):
        self.params = params
        if uid and sid:
            self.uid = uid
            self.sid = sid
        return self

    @classmethod
    def __get_signature(cls, params, uid, sid, salt):
        if not uid:  # uid == 0 or ''
            uid = sid = ""
        pre_string = "{params_string}{salt}{uid}{sid}".format(
            params_string="".join(
                "".join((k, str(v))) for k, v in sorted(params.items())
            ),
            salt=salt,
            uid=str(uid),
            sid=sid,
        )
        return get_md5_data(pre_string)

    @classmethod
    def get_signature_v1(cls, params, uid=0, sid=""):
        return cls.__get_signature(params, uid, sid, "1fd6e28fd158406995f77727b35bf20a")

    @classmethod
    def get_signature_v2(cls, params, uid=0, sid=""):
        return cls.__get_signature(params, uid, sid, "0C077B1E70F5FDDE6F497C1315687F9C")

    def __call__(self, r):
        params = self.params.copy()
        params["timestamp"] = int(time.time())

        signV1 = self.get_signature_v1(params, self.uid, self.sid)
        signV2 = self.get_signature_v2(params, self.uid, self.sid)

        r.headers["_sign"] = signV2

        if r.method == "GET":
            r.prepare_url(
                r.url, params={"signature": signV1, "timestamp": params["timestamp"]}
            )
        elif r.method == "POST":
            params["signature"] = signV1
            r.prepare_body(data=params, files=None)
        return r


class JoyrunFetcher:
    base_url = "https://api.thejoyrun.com"

    def __init__(self, user_name="", identifying_code="", uid=0, sid=""):
        self.user_name = user_name
        # from sms
        self.identifying_code = identifying_code
        self.uid = uid
        self.sid = sid

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept-Language": "en_US",
                "User-Agent": "okhttp/3.10.0",
                "Host": "api.thejoyrun.com",
                "Connection": "Keep-Alive",
            }
        )
        self.session.headers.update(self.device_info_headers)

        self.auth = JoyrunAuth(self.uid, self.sid)
        if self.uid and self.sid:
            self.__update_loginInfo()

    @classmethod
    def from_uid_sid(cls, uid, sid):
        return cls(uid=uid, sid=sid)

    @property
    def device_info_headers(self):
        return {
            "MODELTYPE": "Xiaomi MI 5",
            "SYSVERSION": "8.0.0",
            "APPVERSION": "4.2.0",
        }

    def __update_loginInfo(self):
        self.auth.reload(uid=self.uid, sid=self.sid)
        loginCookie = "sid=%s&uid=%s" % (self.sid, self.uid)
        self.session.headers.update({"ypcookie": loginCookie})
        self.session.cookies.clear()
        self.session.cookies.set("ypcookie", quote(loginCookie).lower())
        self.session.headers.update(
            self.device_info_headers
        )  # 更新设备信息中的 uid 字段

    def login_by_phone(self):
        params = {
            "phoneNumber": self.user_name,
            "identifyingCode": self.identifying_code,
        }
        r = self.session.get(
            f"{self.base_url}//user/login/phonecode",
            params=params,
            auth=self.auth.reload(params),
        )
        login_data = r.json()
        if login_data["ret"] != "0":
            raise Exception(f'{login_data["ret"]}: {login_data["msg"]}')
        self.sid = login_data["data"]["sid"]
        self.uid = login_data["data"]["user"]["uid"]
        print(f"your uid and sid are {str(self.uid)} {str(self.sid)}")
        self.__update_loginInfo()

    def get_record_info(self, fid):
        print(f"Fetching record {fid}")
        payload = {
            "fid": fid,
            "wgs": 1,
        }
        r = self.session.post(
            f"{self.base_url}/Run/GetInfo.aspx",
            data=payload,
            auth=self.auth.reload(payload),
        )
        data = r.json()
        return data

    def get_records_ids_list(self):
        payload = {"year": 0}
        r = self.session.post(
            f"{self.base_url}/userRunList.aspx",
            data=payload,
            auth=self.auth.reload(payload),
        )
        if not r.ok:
            raise Exception("get runs records error")
        print(r.json())
        return [i["fid"] for i in r.json()["datas"]]

    def save_records_data(self, save_path):
        records_ids = self.get_records_ids_list()
        records = []
        for i in set(records_ids):
            print(f"{i}")
            record_data = self.get_record_info(i)
            write_json(f"{save_path}/{i}.json", record_data)
            records.append(record_data)
        return records
