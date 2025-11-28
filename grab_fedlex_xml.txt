# pip install aiohttp tqdm
import asyncio, aiohttp, async_timeout, os, sys
from urllib.parse import urlsplit
import json
 
ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"  # <- verify the endpoint
OUTPUT_DIR = "grabbed_fedlex_xml_landesrecht"
QUERY = r"""
PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT DISTINCT (STR(?srNotation) AS ?rsNr) (STR(?dateApplicabilityNode) AS ?dateApplicability) ?title ?abrev ?fileUrl {
  FILTER(?language = <http://publications.europa.eu/resource/authority/language/DEU>)
  FILTER(!STRSTARTS(STR(?srNotation), "0"))
  ?consolidation a jolux:Consolidation .
  ?consolidation jolux:dateApplicability ?dateApplicabilityNode .
  OPTIONAL { ?consolidation jolux:dateEndApplicability ?dateEndApplicability }
  FILTER(xsd:date(?dateApplicabilityNode) <= xsd:date(now()) && (!BOUND(?dateEndApplicability) || xsd:date(?dateEndApplicability) >= xsd:date(now())))
  ?consolidation jolux:isRealizedBy ?consoExpr .
  ?consoExpr jolux:language ?language .
  ?consoExpr jolux:isEmbodiedBy ?consoManif .
  ?consoManif jolux:userFormat <https://fedlex.data.admin.ch/vocabulary/user-format/xml> .
  ?consoManif jolux:isExemplifiedBy ?fileUrl .
  ?consolidation jolux:isMemberOf ?cc .
  ?cc jolux:classifiedByTaxonomyEntry/skos:notation ?srNotation .
  OPTIONAL { ?cc jolux:dateNoLongerInForce ?ccNoLonger }
  OPTIONAL { ?cc jolux:dateEndApplicability ?ccEnd }
  FILTER(!BOUND(?ccNoLonger) || xsd:date(?ccNoLonger) > xsd:date(now()))
  FILTER(!BOUND(?ccEnd) || xsd:date(?ccEnd) >= xsd:date(now()))
  FILTER(DATATYPE(?srNotation) = <https://fedlex.data.admin.ch/vocabulary/notation-type/id-systematique>)
  OPTIONAL {
    ?cc jolux:isRealizedBy ?ccExpr .
    ?ccExpr jolux:language ?language .
    ?ccExpr jolux:title ?title .
    OPTIONAL { ?ccExpr jolux:titleShort ?abrev }
  }
}
ORDER BY ?srNotation
LIMIT 20
"""
 
async def fetch_urls():
    async with aiohttp.ClientSession() as session:
        params = {"query": QUERY}
        headers = {"Accept": "application/sparql-results+json"}
        async with session.get(ENDPOINT, params=params, headers=headers) as r:
            r.raise_for_status()
            data = await r.json()
    items = []
    seen = set()
    for b in data["results"]["bindings"]:
        if "fileUrl" not in b or "rsNr" not in b or "dateApplicability" not in b:
            continue
        url = b["fileUrl"]["value"]
        rs_nr = b["rsNr"]["value"]
        date_app = b["dateApplicability"]["value"]
        key = (url, rs_nr, date_app)
        if key in seen:
            continue
        seen.add(key)
        items.append(
            {
                "url": url,
                "rsNr": rs_nr,
                "dateApplicability": date_app,
            }
        )
    return items


def output_name(url: str, rs_nr: str, date_app: str) -> str:
    """
    Build filename: SR-<rsnr>-<DDMMYYYY>-DE.xml

    - rs_nr: taken directly from the SPARQL result (STR(?srNotation))
    - date_app: taken from STR(?dateApplicabilityNode), usually 'YYYY-MM-DD' or 'YYYYMMDD'
    """
    # Normalize date to YYYYMMDD (strip dashes if present)
    raw = date_app.strip()
    if "-" in raw:
        raw = raw.replace("-", "")
    if len(raw) != 8 or not raw.isdigit():
        # Fallback: keep original date string if it doesn't match expected pattern
        ddmmyyyy = raw
    else:
        yyyy, mm, dd = raw[0:4], raw[4:6], raw[6:8]
        ddmmyyyy = f"{dd}{mm}{yyyy}"

    filename = f"SR-{rs_nr}-{ddmmyyyy}-DE.xml"
    return os.path.join(OUTPUT_DIR, filename)
 
# async def download_one(session, url, sem, retries=3):
#     name = output_name(url)
#     attempt = 0
#     while True:
#         try:
#             async with sem:
#                 with async_timeout.timeout(300):
#                     async with session.get(url, allow_redirects=True) as r:
#                         r.raise_for_status()
#                         with open(name, "wb") as f:
#                             while True:
#                                 chunk = await r.content.read(1 << 14)
#                                 if not chunk: break
#                                 f.write(chunk)
#             return name
#         except Exception as e:
#             attempt += 1
#             if attempt > retries:
#                 print(f"FAILED: {url} -> {e}", file=sys.stderr)
#                 return None

async def download_one(session, item, sem, retries=3):
    url = item["url"]
    rs_nr = item["rsNr"]
    date_app = item["dateApplicability"]
    name = output_name(url, rs_nr, date_app)
    attempt = 0
    while True:
        try:
            async with sem:
                async with async_timeout.timeout(300):
                    async with session.get(url, allow_redirects=True) as r:
                        r.raise_for_status()
                        with open(name, "wb") as f:
                            while True:
                                chunk = await r.content.read(1 << 14)
                                if not chunk: break
                                f.write(chunk)
            return name
        except Exception as e:
            attempt += 1
            if attempt > retries:
                print(f"FAILED: {url} -> {e}", file=sys.stderr)
                return None
 
async def main():
    # Ensure target directory exists before downloading files
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    items = await fetch_urls()
    print(f"Found {len(items)} files.")
    sem = asyncio.Semaphore(8)  # limit concurrency
    async with aiohttp.ClientSession() as session:
        tasks = [download_one(session, item, sem) for item in items]
        for coro in asyncio.as_completed(tasks):
            name = await coro
            if name:
                print(f"Saved {name}")
 
if __name__ == "__main__":
    asyncio.run(main())