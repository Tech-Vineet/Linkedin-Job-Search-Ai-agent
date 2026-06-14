import os
from typing import Any, List

import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")


def fetch_dataset_items(dataset_id: str) -> List[dict]:
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    params: dict[str, str] = {
        "clean": "true",
        "format": "json",
    }

    if APIFY_TOKEN:
        params["token"] = APIFY_TOKEN

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]

    raise ValueError("Apify dataset response did not contain a list of items.")


def fetch_run_dataset_items(run_id: str) -> List[dict]:
    url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"
    params: dict[str, str] = {
        "clean": "true",
        "format": "json",
    }

    if APIFY_TOKEN:
        params["token"] = APIFY_TOKEN

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    if isinstance(data, list):
        return data

    raise ValueError("Apify run dataset response did not contain a list of items.")


def extract_posts(payload: Any) -> List[dict]:
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a JSON object or array.")

    nested_payload = payload.get("payload")
    if isinstance(nested_payload, dict):
        try:
            return extract_posts(nested_payload)
        except ValueError:
            pass

    if str(payload.get("eventType", "")).lower() == "test":
        return []

    if isinstance(payload.get("items"), list):
        return payload["items"]

    if "content" in payload or "linkedinUrl" in payload:
        return [payload]

    resource = payload.get("resource") or {}
    event_data = payload.get("eventData") or {}
    dataset_id = (
        payload.get("datasetId")
        or payload.get("defaultDatasetId")
        or resource.get("defaultDatasetId")
        or event_data.get("defaultDatasetId")
    )

    if dataset_id:
        return fetch_dataset_items(dataset_id)

    run_id = (
        payload.get("actorRunId")
        or payload.get("resourceId")
        or resource.get("id")
        or event_data.get("actorRunId")
        or event_data.get("resourceId")
    )

    if run_id:
        return fetch_run_dataset_items(run_id)

    keys = ", ".join(sorted(payload.keys()))
    raise ValueError(
        "Could not find posts, defaultDatasetId, or actorRunId in payload. "
        f"Top-level keys: {keys}"
    )
