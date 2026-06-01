"""Registry of federal APIs to monitor."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApiEndpoint:
    slug: str
    name: str
    url: str
    description: str
    agency: str
    category: str
    # JSON pointer path to a stable version or schema field; None = hash full body
    schema_path: str | None = None
    # extra headers needed for the health probe
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 10.0
    expected_status: int = 200


REGISTRY: list[ApiEndpoint] = [
    ApiEndpoint(
        slug="data-gov-catalog",
        name="Data.gov Catalog API",
        url="https://catalog.data.gov/api/3/action/package_search?rows=1",
        description="CKAN catalog of all datasets published at data.gov.",
        agency="GSA",
        category="Open Data",
    ),
    ApiEndpoint(
        slug="federal-register",
        name="Federal Register API",
        url="https://www.federalregister.gov/api/v1/articles?per_page=1&order=newest",
        description="Full-text search and retrieval for Federal Register documents.",
        agency="OFR / GPO",
        category="Regulations",
    ),
    ApiEndpoint(
        slug="ecfr",
        name="eCFR API",
        url="https://www.ecfr.gov/api/versioner/v1/titles.json",
        description="Electronic Code of Federal Regulations — all 50 titles.",
        agency="OFR / GPO",
        category="Regulations",
    ),
    ApiEndpoint(
        slug="grants-gov-search",
        name="Grants.gov Search API",
        url="https://apply07.grants.gov/grantsws/rest/opportunities/search/",
        description="Search open federal grant opportunities.",
        agency="HHS",
        category="Grants",
        headers={"Content-Type": "application/json"},
    ),
    ApiEndpoint(
        slug="usaspending",
        name="USASpending API",
        url="https://api.usaspending.gov/api/v2/references/agency/?page=1&limit=1",
        description="Federal spending data — contracts, grants, loans.",
        agency="Treasury / OMB",
        category="Spending",
    ),
    ApiEndpoint(
        slug="sam-gov-entity",
        name="SAM.gov Entity API",
        url="https://api.sam.gov/entity-information/v3/entities?api_key=DEMO_KEY&legalBusinessName=Test",
        description="System for Award Management — entity registration lookup.",
        agency="GSA",
        category="Procurement",
    ),
    ApiEndpoint(
        slug="fec",
        name="FEC API",
        url="https://api.open.fec.gov/v1/candidates/?api_key=DEMO_KEY&per_page=1",
        description="Federal Election Commission campaign finance data.",
        agency="FEC",
        category="Elections",
    ),
    ApiEndpoint(
        slug="census-acs",
        name="Census Bureau ACS API",
        url="https://api.census.gov/data/2022/acs/acs5?get=NAME&for=state:06&key=",
        description="American Community Survey 5-year estimates.",
        agency="Census Bureau",
        category="Demographics",
    ),
    ApiEndpoint(
        slug="bls",
        name="BLS Public Data API",
        url="https://api.bls.gov/publicAPI/v2/timeseries/data/",
        description="Bureau of Labor Statistics — employment, inflation, wages.",
        agency="DOL / BLS",
        category="Labor",
        expected_status=200,
    ),
    ApiEndpoint(
        slug="fred",
        name="FRED Economic Data API",
        url="https://api.stlouisfed.org/fred/series?series_id=GNPCA&api_key=annualreviews&file_type=json",
        description="Federal Reserve Bank of St. Louis economic time series.",
        agency="Federal Reserve",
        category="Economics",
    ),
    ApiEndpoint(
        slug="nasa-apod",
        name="NASA APOD API",
        url="https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY",
        description="NASA Astronomy Picture of the Day — tests the api.nasa.gov gateway.",
        agency="NASA",
        category="Science",
    ),
    ApiEndpoint(
        slug="noaa-climate",
        name="NOAA Climate Data Online API",
        url="https://www.ncdc.noaa.gov/cdo-web/api/v2/datacategories?limit=1",
        description="NOAA Climate Data Online — historical weather and climate records.",
        agency="NOAA / DOC",
        category="Climate",
        headers={"token": ""},
    ),
    ApiEndpoint(
        slug="regulations-gov",
        name="Regulations.gov API",
        url="https://api.regulations.gov/v4/documents?api_key=DEMO_KEY&filter[postedDate][ge]=2024-01-01&page[size]=1",
        description="Public comment dockets and regulatory documents.",
        agency="EPA / GSA",
        category="Regulations",
    ),
    ApiEndpoint(
        slug="open-fda",
        name="openFDA API",
        url="https://api.fda.gov/drug/label.json?limit=1",
        description="FDA drug labels, adverse events, device recalls.",
        agency="FDA / HHS",
        category="Health",
    ),
    ApiEndpoint(
        slug="cms-open-payments",
        name="CMS Open Payments API",
        url="https://openpaymentsdata.cms.gov/api/1/datastore/query/06dd7a5a-4a48-4abf-bfcc-09b7e7b7dfd7/0?limit=1&offset=0&count=true",
        description="CMS Open Payments — financial relationships between industry and physicians.",
        agency="CMS / HHS",
        category="Health",
    ),
]

REGISTRY_BY_SLUG: dict[str, ApiEndpoint] = {a.slug: a for a in REGISTRY}
