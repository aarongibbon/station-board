"""Resolve missing or non-numeric service platforms from configured calling-point rules."""


def validate_platform_fallback_config(fallback_config, platforms):
    """Validate and normalize optional platform fallback configuration."""
    if fallback_config is None:
        fallback_config = {}
    if not isinstance(fallback_config, dict):
        raise ValueError("platform_fallback must be an object")

    enabled = fallback_config.get("enabled", False)
    if not isinstance(enabled, bool):
        raise ValueError("platform_fallback.enabled must be a boolean")

    rules = fallback_config.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("platform_fallback.rules must be a list")

    normalized_rules = []
    for index, rule in enumerate(rules):
        label = f"platform_fallback.rules[{index}]"
        if not isinstance(rule, dict):
            raise ValueError(f"{label} must be an object")

        calling_points = rule.get("calling_points")
        if calling_points not in {"previous", "subsequent"}:
            raise ValueError(
                f"{label}.calling_points must be 'previous' or 'subsequent'"
            )

        crs = rule.get("contains_crs")
        if not isinstance(crs, str) or not crs.strip():
            raise ValueError(f"{label}.contains_crs must be a non-empty string")

        platform = rule.get("assign_platform")
        if (
            isinstance(platform, bool)
            or not isinstance(platform, int)
            or platform not in platforms
        ):
            raise ValueError(
                f"{label}.assign_platform must be one of the configured platforms"
            )

        normalized_rules.append(
            {
                "calling_points": calling_points,
                "contains_crs": crs.strip().upper(),
                "assign_platform": platform,
            }
        )

    return {"enabled": enabled, "rules": normalized_rules}


def _calling_point_crs_codes(service, list_name):
    """Return CRS codes from the API's wrapped calling-point list shape."""
    codes = set()
    for group in service.get(f"{list_name}CallingPoints", []) or []:
        if not isinstance(group, dict):
            continue
        for point in group.get("callingPoint", []) or []:
            if isinstance(point, dict):
                crs = point.get("crs")
                if isinstance(crs, str):
                    codes.add(crs.strip().upper())
    return codes


def _is_numeric_platform(value):
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, str) and value.strip().isdigit()


def _service_note_identity(service):
    service_id = service.get("serviceID")
    if service_id:
        return ("id", str(service_id))

    def endpoint_identity(key):
        endpoints = service.get(key, []) or []
        return tuple(
            (endpoint.get("crs"), endpoint.get("locationName"))
            for endpoint in endpoints
            if isinstance(endpoint, dict)
        )

    return (
        "schedule",
        service.get("std") or service.get("sta"),
        endpoint_identity("origin"),
        endpoint_identity("destination"),
        service.get("serviceType"),
        service.get("operatorCode"),
    )


def apply_platform_fallback(services, fallback_config, logger, logged_notes):
    """Mutate service platform fields using uniquely matching configured rules.

    Numeric platform values are preserved, including platforms not shown on this
    board. Missing and non-numeric platform values are resolved only when exactly
    one rule matches. Ambiguous or unmatched services retain their original value.
    """
    if not fallback_config.get("enabled", False):
        return

    active_identities = {_service_note_identity(service) for service in services}
    for identity in list(logged_notes):
        if identity not in active_identities:
            del logged_notes[identity]

    for service in services:
        identity = _service_note_identity(service)
        original_platform = service.get("platform")
        if _is_numeric_platform(original_platform):
            logged_notes.pop(identity, None)
            continue

        matched_rules = [
            rule
            for rule in fallback_config["rules"]
            if rule["contains_crs"]
            in _calling_point_crs_codes(service, rule["calling_points"])
        ]
        service_id = service.get("serviceID") or repr(identity)

        if len(matched_rules) == 1:
            service["platform"] = str(matched_rules[0]["assign_platform"])
            logged_notes.pop(identity, None)
            continue

        outcome = "no matching rule" if not matched_rules else "multiple matching rules"
        note_state = (outcome, str(original_platform))
        if logged_notes.get(identity) != note_state:
            logger.info(
                "Platform fallback left %s unchanged for %s (%s)",
                repr(original_platform),
                service_id,
                outcome,
            )
            logged_notes[identity] = note_state
