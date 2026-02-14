"""Entity and relationship extraction operations extracted from operate.py."""

from collections import defaultdict
from typing import Any

import yaml

from lightrag.base import BaseKVStorage
from lightrag.chunking import truncate_entity_identifier
from lightrag.utils import (
    fix_tuple_delimiter_corruption,
    is_float_regex,
    logger,
    sanitize_and_normalize_extracted_text,
    split_string_by_multi_markers,
)


async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
    timestamp: int,
    file_path: str = "unknown_source",
):
    if len(record_attributes) != 4 or "entity" not in record_attributes[0]:
        if len(record_attributes) > 1 and "entity" in record_attributes[0]:
            logger.warning(
                f"{chunk_key}: LLM output format error; found {len(record_attributes)}/4 feilds on ENTITY `{record_attributes[1]}` @ `{record_attributes[2] if len(record_attributes) > 2 else 'N/A'}`"
            )
            logger.debug(record_attributes)
        return None

    try:
        entity_name = sanitize_and_normalize_extracted_text(
            record_attributes[1], remove_inner_quotes=True
        )

        if not entity_name or not entity_name.strip():
            logger.info(
                f"Empty entity name found after sanitization. Original: '{record_attributes[1]}'"
            )
            return None

        entity_type = sanitize_and_normalize_extracted_text(
            record_attributes[2], remove_inner_quotes=True
        )

        if not entity_type.strip() or any(
            char in entity_type for char in ["'", "(", ")", "<", ">", "|", "/", "\\"]
        ):
            logger.warning(
                f"Entity extraction error: invalid entity type in: {record_attributes}"
            )
            return None

        entity_type = entity_type.replace(" ", "").lower()

        entity_description = sanitize_and_normalize_extracted_text(record_attributes[3])

        if not entity_description.strip():
            logger.warning(
                f"Entity extraction error: empty description for entity '{entity_name}' of type '{entity_type}'"
            )
            return None

        return dict(
            entity_name=entity_name,
            entity_type=entity_type,
            description=entity_description,
            source_id=chunk_key,
            file_path=file_path,
            timestamp=timestamp,
        )

    except ValueError as e:
        logger.error(
            f"Entity extraction failed due to encoding issues in chunk {chunk_key}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Entity extraction failed with unexpected error in chunk {chunk_key}: {e}"
        )
        return None


async def _handle_single_relationship_extraction(
    record_attributes: list[str],
    chunk_key: str,
    timestamp: int,
    file_path: str = "unknown_source",
):
    if len(record_attributes) != 5 or "relation" not in record_attributes[0]:
        if len(record_attributes) > 1 and "relation" in record_attributes[0]:
            logger.warning(
                f"{chunk_key}: LLM output format error; found {len(record_attributes)}/5 fields on RELATION `{record_attributes[1]}`~`{record_attributes[2] if len(record_attributes) > 2 else 'N/A'}`"
            )
            logger.debug(record_attributes)
        return None

    try:
        source = sanitize_and_normalize_extracted_text(
            record_attributes[1], remove_inner_quotes=True
        )
        target = sanitize_and_normalize_extracted_text(
            record_attributes[2], remove_inner_quotes=True
        )

        if not source:
            logger.info(
                f"Empty source entity found after sanitization. Original: '{record_attributes[1]}'"
            )
            return None

        if not target:
            logger.info(
                f"Empty target entity found after sanitization. Original: '{record_attributes[2]}'"
            )
            return None

        if source == target:
            logger.debug(
                f"Relationship source and target are the same in: {record_attributes}"
            )
            return None

        edge_keywords = sanitize_and_normalize_extracted_text(
            record_attributes[3], remove_inner_quotes=True
        )
        edge_keywords = edge_keywords.replace("，", ",")

        edge_description = sanitize_and_normalize_extracted_text(record_attributes[4])

        edge_source_id = chunk_key
        weight = (
            float(record_attributes[-1].strip('"').strip("'"))
            if is_float_regex(record_attributes[-1].strip('"').strip("'"))
            else 1.0
        )

        return dict(
            src_id=source,
            tgt_id=target,
            weight=weight,
            description=edge_description,
            keywords=edge_keywords,
            source_id=edge_source_id,
            file_path=file_path,
            timestamp=timestamp,
        )

    except ValueError as e:
        logger.warning(
            f"Relationship extraction failed due to encoding issues in chunk {chunk_key}: {e}"
        )
        return None
    except Exception as e:
        logger.warning(
            f"Relationship extraction failed with unexpected error in chunk {chunk_key}: {e}"
        )
        return None


async def _process_extraction_result(
    result: str,
    chunk_key: str,
    timestamp: int,
    file_path: str = "unknown_source",
    tuple_delimiter: str = "<|#|>",
    completion_delimiter: str = "<|COMPLETE|>",
) -> tuple[dict, dict]:
    maybe_nodes = defaultdict(list)
    maybe_edges = defaultdict(list)

    if completion_delimiter not in result:
        logger.warning(
            f"{chunk_key}: Complete delimiter can not be found in extraction result"
        )

    records = split_string_by_multi_markers(
        result,
        ["\n", completion_delimiter, completion_delimiter.lower()],
    )

    fixed_records = []
    for record in records:
        record = record.strip()
        if record is None:
            continue
        entity_records = split_string_by_multi_markers(
            record, [f"{tuple_delimiter}entity{tuple_delimiter}"]
        )
        for entity_record in entity_records:
            fixed_records.append(entity_record.strip())
        relationship_records = split_string_by_multi_markers(
            record, [f"{tuple_delimiter}relation{tuple_delimiter}"]
        )
        for relationship_record in relationship_records:
            fixed_records.append(relationship_record.strip())

    for record in fixed_records:
        if record is None:
            continue
        if tuple_delimiter not in record:
            continue
        record = fix_tuple_delimiter_corruption(record, tuple_delimiter)
        record_attributes = [
            it.strip()
            for it in record.split(tuple_delimiter)
            if it is not None and it.strip() != ""
        ]

        entity_data = await _handle_single_entity_extraction(
            record_attributes, chunk_key, timestamp, file_path
        )
        if entity_data:
            entity_name = entity_data["entity_name"]
            truncated_entity_name = truncate_entity_identifier(entity_name)
            entity_data["entity_name"] = truncated_entity_name
            maybe_nodes[truncated_entity_name].append(entity_data)

        relationship_data = await _handle_single_relationship_extraction(
            record_attributes, chunk_key, timestamp, file_path
        )
        if relationship_data:
            source = relationship_data["src_id"]
            target = relationship_data["tgt_id"]
            truncated_source = truncate_entity_identifier(source)
            truncated_target = truncate_entity_identifier(target)
            relationship_data["src_id"] = truncated_source
            relationship_data["tgt_id"] = truncated_target
            maybe_edges[(truncated_source, truncated_target)].append(relationship_data)

    return dict(maybe_nodes), dict(maybe_edges)


async def _parse_yaml_extraction(
    content: str, chunk_key: str, timestamp: int, file_path: str = "unknown_source"
) -> tuple[dict, dict]:
    maybe_nodes = defaultdict(list)
    maybe_edges = defaultdict(list)

    try:
        clean_content = content.strip()
        if "```" in clean_content:
            first_fence = clean_content.find("```")
            last_fence = clean_content.rfind("```")
            if last_fence > first_fence:
                newline_idx = clean_content.find("\n", first_fence)
                if newline_idx != -1 and newline_idx < last_fence:
                    clean_content = clean_content[newline_idx + 1 : last_fence].strip()
                else:
                    clean_content = clean_content[first_fence + 3 : last_fence].strip()

        try:
            data = yaml.safe_load(clean_content)
        except Exception:
            clean_content = clean_content.strip("()[] \n\t`\"'#")
            data = yaml.safe_load(clean_content)

        if not data:
            return {}, {}

        entities = data.get("entities") or []
        if isinstance(entities, dict):
            temp_entities = []
            for name, details in entities.items():
                if isinstance(details, dict):
                    details["name"] = name
                    temp_entities.append(details)
                else:
                    temp_entities.append({"name": name, "description": str(details)})
            entities = temp_entities

        for ent in entities:
            if not isinstance(ent, dict):
                continue
            name = ent.get("name")
            if not name:
                continue
            ent_type = ent.get("type", "UNKNOWN")
            description = ent.get("description", "")

            maybe_nodes[name].append(
                {
                    "entity_name": name,
                    "entity_type": ent_type,
                    "description": description,
                    "source_id": chunk_key,
                    "file_path": file_path,
                    "timestamp": timestamp,
                }
            )

        relationships = data.get("relationships") or []
        if isinstance(relationships, dict):
            temp_relationships = []
            for key, details in relationships.items():
                if isinstance(details, dict):
                    details["key"] = key
                    temp_relationships.append(details)
            relationships = temp_relationships

        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            source = rel.get("source")
            target = rel.get("target")
            if not source or not target:
                continue

            rel_type = rel.get("type", "RELATED")
            description = rel.get("description", "")
            keywords = rel.get("keywords", "")

            maybe_edges[(source, target)].append(
                {
                    "src_id": source,
                    "tgt_id": target,
                    "description": description,
                    "keywords": keywords,
                    "weight": 1.0,
                    "source_id": chunk_key,
                    "file_path": file_path,
                    "timestamp": timestamp,
                }
            )

    except Exception as e:
        logger.error(f"Failed to parse YAML extraction result: {e}")
        logger.debug(f"Content: {content}")

    return dict(maybe_nodes), dict(maybe_edges)


async def _rebuild_from_extraction_result(
    text_chunks_storage: BaseKVStorage,
    extraction_result: str,
    chunk_id: str,
    timestamp: int,
    extraction_format: str = "standard",
) -> tuple[dict, dict]:
    chunk_data = await text_chunks_storage.get_by_id(chunk_id)
    file_path = (
        chunk_data.get("file_path", "unknown_source")
        if chunk_data
        else "unknown_source"
    )

    if extraction_format == "yaml":
        return await _parse_yaml_extraction(
            extraction_result, chunk_id, timestamp, file_path
        )

    return await _process_extraction_result(
        extraction_result, chunk_id, timestamp, file_path
    )
