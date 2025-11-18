# SatNOGS Waterfall Tools

This repository contains two small Python utilities designed to assist with
collecting and inspecting waterfall data from the SatNOGS network.


## `fetch_satnogs_data.py`

A compact helper script for retrieving paginated results from the SatNOGS
network API. Provide a full request URL (including any filters), your API-Token
and ensure that `/api/` is included. The script stores all received data in a
single JSON file, which can then be processed further. For example, to extract
all waterfall image URLs:

```sh
jq -r '.[].waterfall' aggr.json
```

Downloading the referenced files can then be done using your preferred tool by
iterating over the links. These downloaded images are the input for the analysis
script described below.

## `analyse_waterfalls.py`

A proof-of-concept tool that evaluates a waterfall image to determine whether it
is likely to contain a satellite signal. It classifies the waterfalls into
different categories and only vets those as "good", where it is almost sure,
that the signal we are looking for is in it.
