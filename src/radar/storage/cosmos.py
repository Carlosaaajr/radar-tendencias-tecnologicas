"""CosmosReportRepository — Azure Cosmos DB serverless (production)."""

from __future__ import annotations

import logging

from azure.cosmos import CosmosClient, PartitionKey, exceptions

from radar.models import Report, ReportSummary, SupportLevel

logger = logging.getLogger(__name__)

DATABASE_NAME = "radar"
CONTAINER_NAME = "reports"


class CosmosReportRepository:
    def __init__(self, endpoint: str, key: str) -> None:
        client = CosmosClient(endpoint, credential=key)
        database = client.create_database_if_not_exists(DATABASE_NAME)
        self._container = database.create_container_if_not_exists(
            id=CONTAINER_NAME,
            partition_key=PartitionKey(path="/theme_slug"),
        )

    def save(self, report: Report) -> None:
        item = report.model_dump(mode="json")
        try:
            self._container.upsert_item(item)
        except exceptions.CosmosHttpResponseError:
            logger.warning("Cosmos write failed, retrying once for report %s", report.id)
            self._container.upsert_item(item)

    def get(self, report_id: str, theme_slug: str) -> Report | None:
        try:
            item = self._container.read_item(item=report_id, partition_key=theme_slug)
        except exceptions.CosmosResourceNotFoundError:
            return None
        return Report.model_validate(item)

    def list_summaries(self) -> list[ReportSummary]:
        query = (
            "SELECT c.id, c.theme, c.theme_slug, c.created_at, c.status, c.sections "
            "FROM c ORDER BY c.created_at DESC"
        )
        items = self._container.query_items(query=query, enable_cross_partition_query=True)
        return [_to_summary(item) for item in items]

    def find_by_slug(self, theme_slug: str) -> list[ReportSummary]:
        query = (
            "SELECT c.id, c.theme, c.theme_slug, c.created_at, c.status, c.sections "
            "FROM c WHERE c.theme_slug = @slug ORDER BY c.created_at DESC"
        )
        params = [{"name": "@slug", "value": theme_slug}]
        items = self._container.query_items(
            query=query, parameters=params, partition_key=theme_slug
        )
        return [_to_summary(item) for item in items]


def _to_summary(item: dict) -> ReportSummary:
    overview: dict[SupportLevel, int] = {}
    for section in item.get("sections", []):
        support = section.get("support")
        if not support:
            continue
        level = SupportLevel(support["level"])
        overview[level] = overview.get(level, 0) + 1
    return ReportSummary(
        id=item["id"],
        theme=item["theme"],
        theme_slug=item["theme_slug"],
        created_at=item["created_at"],
        status=item["status"],
        support_overview=overview,
    )
