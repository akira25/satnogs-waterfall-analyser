import requests as r
from time import sleep
import json

#
# Get a satnogs-network API-Request and roll through paginated API.
#
# This is a pretty quick, rough script for traversing through the paginated
# SatNOGS-API. For using it, paste the URL with the filters you want to apply
# from your browser here and add the '/api/' into it, for addressing the API
# directly.
#
# After retrieving the json-data, you might get the waterfall-image-urls from
# that e.g. with 'jq':
#
#     jq -r '.[].waterfall' aggr.json
#
# Downloading the files with a for-loop is left for you as an exercise. :)
# Afterwards, you can analyse the waterfalls with the `analyse-waterfalls.py`
# script.
#
# © by Martin Hübner, 2025
#


url = "https://network.satnogs.org/api/observations/?id=&status=good&ground_station=1860&start=&end=&transmitter_uuid=&transmitter_mode=&transmitter_type=&waterfall_status=&vetted_status=&vetted_user=&observer=360&sat_id=&start__lt=&end__gt=&observation_id=&norad_cat_id="

SATNOGS_API_TOKEN="PASTE_YOUR_TOKEN_HERE"
headers = {'Authorization': 'Token {0}'.format(SATNOGS_API_TOKEN)}

def flatten(xss):
    return [x for xs in xss for x in xs]


if __name__ == "__main__":
    aggregated_data = []

    next_page = url
    out_name_idx = 0
    while next_page:
        print(f"Loading Page {out_name_idx}")
        resp = r.get(next_page, headers=headers)

        if resp.status_code != 200:
            print(resp.text)

        data = resp.json()
        aggregated_data.append(data)

        try:
            next_page = resp.links.get("next", None).get("url", None)
        except AttributeError:
            next_page = None
        # prev_page = resp.links.get("prev", None).get("url", None)

        with open("tmp.json", "w") as f:
            json.dump(
                flatten(aggregated_data),
                f
            )

        out_name_idx += 1
        sleep(2)


    with open("aggr.json", "w") as f:
        json.dump(
            flatten(aggregated_data),
            f
        )
