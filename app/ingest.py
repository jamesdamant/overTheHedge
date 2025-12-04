import re
import requests
import pandas as pd
import xml.etree.ElementTree as ET

from config import get_config

class DataLoader():

    def __init__(self):
        self.comp_ticker_url = get_config("sec-url","comp_ticker.url")
        self.comp_sub_base_url = get_config("sec-url","comp_sub.base_url")
        self.fund_infotable_base_url = get_config("sec-url","fund_infotable.base_url")


    def _escape_fn(self, xml_data: str) -> str:
        escape_map = {
            # '<': '&lt;',
            # '>': '&gt;',
            # '"': '&quot;',
            # "'": '&apos;',
            '&': '&amp;',
        }
        return ''.join(escape_map.get(char, char) for char in xml_data)


    def get_latest_sub(self, cik):
        cik = str(cik).zfill(10)

        url = self.comp_sub_base_url + cik + ".json"
        headers = {
            "User-Agent": "james@damant.com",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)
        try:
            name = resp.json().get("name")
            recent_filings = resp.json()['filings']['recent']
            forms = recent_filings['form']
            acc_numbers = recent_filings['accessionNumber']
            filing_dates = recent_filings['filingDate']
            report_dates = recent_filings['reportDate']
            

            for i in range(len(forms)):
                if forms[i] == "13F-HR":
                    
                    return {
                        "name": name,
                        "form": forms[i],
                        "accessionNumber": acc_numbers[i],
                        "filingDate": filing_dates[i],
                        "reportDate": report_dates[i]
                    }


            return None

        except KeyError as e:
            print(f"Error: Required key not found in the JSON structure: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None 
        
# TODO FIX The lookup on filename
    def get_infotable(self, cik, acc_num, metadata):
        url = self.fund_infotable_base_url + cik + "/" + acc_num.replace("-","") + "/infotable.xml"
        print(url)
        headers = {
            "User-Agent": "james@damant.com",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        resp = requests.get(url, headers=headers)

        if resp.status_code == 404:
            url = self.fund_infotable_base_url + cik + "/" + acc_num.replace("-","") + "/informationtable.xml"
            headers = {
                "User-Agent": "james@damant.com",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            resp = requests.get(url, headers=headers)
    
        if resp.status_code == 404:
            url = self.fund_infotable_base_url + cik + "/" + acc_num.replace("-","") + "/MLP_Filing_20250930.xml"
            headers = {
                "User-Agent": "james@damant.com",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            resp = requests.get(url, headers=headers)

        infotable = self._escape_fn(resp.text)
        
        # Remove xmlns declarations
        xml_data = re.sub(r'xmlns="[^"]+"', '', infotable)
        # Remove ALL namespace prefixes like <ns1:tag> → <tag>
        xml_clean = re.sub(r'<(/?)(\w+):', r'<\1', xml_data)
        # Same for closing tags: </ns1:tag>
        xml_clean = re.sub(r'</\w+:', '</', xml_clean)

        with open("./data/out.xml","a+") as f:
            f.write(xml_clean)

        root = ET.fromstring(xml_clean)

        records = []
        for info in root.findall("infoTable"):
            record = {
                "nameOfIssuer": info.findtext("nameOfIssuer"),
                "titleOfClass": info.findtext("titleOfClass"),
                "cusip": info.findtext("cusip"),
                "value": int(info.findtext("value")),
                "sshPrnamt": int(info.find("shrsOrPrnAmt/sshPrnamt").text),
                "sshPrnamtType": info.find("shrsOrPrnAmt/sshPrnamtType").text,
                "investmentDiscretion": info.findtext("investmentDiscretion"),
                "voting_Sole": int(info.find("votingAuthority/Sole").text),
                "voting_Shared": int(info.find("votingAuthority/Shared").text),
                "voting_None": int(info.find("votingAuthority/None").text),
            }
            records.append(record)

        df = pd.DataFrame(records)
        df["fundName"] = metadata.get("name")
        df["form"] = metadata.get("form")
        df["accessionNumber"] = metadata.get("accessionNumber")
        df["filingDate"] = metadata.get("filingDate")
        df["reportDate"] = metadata.get("reportDate")
        print(df.columns)

        return df