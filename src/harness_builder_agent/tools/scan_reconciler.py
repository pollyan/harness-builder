from __future__ import annotations

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.scan import EvidenceBundle, LLMCommandCandidate, LLMScanProposal, ScanMetadata, ScanWarning
from harness_builder_agent.tools.llm_scan_analyzer import SCAN_PROMPT_VERSION


class ScanConflictError(ValueError):
    pass


STACK_ALIASES = {
    "java-spring": "java-spring",
    "java": "java-spring",
    "spring": "java-spring",
    "spring-boot": "java-spring",
    "maven": "java-spring",
    "gradle": "java-spring",
    "dotnet-aspnet": "dotnet-aspnet",
    "dotnet": "dotnet-aspnet",
    ".net": "dotnet-aspnet",
    "csharp": "dotnet-aspnet",
    "c#": "dotnet-aspnet",
    "aspnet": "dotnet-aspnet",
    "node": "node",
    "nodejs": "node",
    "node.js": "node",
    "javascript": "node",
    "typescript": "node",
    "react": "node",
    "vue": "node",
    "vite": "node",
    "npm": "node",
    "python-flask": "python-flask",
    "python": "python-flask",
    "flask": "python-flask",
    "pyproject": "python-flask",
    "requirements": "python-flask",
}

STACK_LABELS = {
    "java-spring": "Java Spring 后端",
    "dotnet-aspnet": ".NET ASP.NET Core 后端",
    "node": "Node.js / 前端",
    "python-flask": "Python Flask 后端",
    "unknown": "未知技术栈",
}


def reconcile_scan(
    evidence: EvidenceBundle,
    proposal: LLMScanProposal,
    *,
    model: str | None = None,
    base_url: str | None = None,
) -> tuple[ProjectInventory, CommandCatalog, ScanMetadata]:
    _veto_impossible_stack(evidence, proposal)
    warnings: list[ScanWarning] = _coverage_warnings(evidence)
    scan_validation = _validate_stack_claims(evidence, proposal)
    warnings.extend(_stack_validation_warnings(scan_validation))
    commands = [_command_from_candidate(candidate, evidence, warnings) for candidate in proposal.command_candidates]
    metadata = ScanMetadata(
        prompt_version=SCAN_PROMPT_VERSION,
        model=model,
        base_url=base_url,
        evidence_file_count=evidence.detected_file_count,
        truncated_files=evidence.truncations,
        warnings=warnings,
        coverage=evidence.coverage.model_dump(mode="json") if evidence.coverage else None,
        reasoning_summary=proposal.reasoning_summary,
    )
    inventory = ProjectInventory(
        repo_name=evidence.repo_name,
        root_path=evidence.root_path,
        primary_stack=proposal.primary_stack,
        stacks=proposal.stacks,
        modules=proposal.modules,
        evidence=[{"path": item.path, "reason": item.kind} for item in evidence.key_files],
        documents=[{"path": item.path, "kind": item.kind} for item in evidence.documents],
        configs=proposal.configs or [{"path": item.path, "kind": item.kind} for item in evidence.config_files],
        ci_files=proposal.ci_files or [{"path": item.path, "kind": item.kind} for item in evidence.ci_files],
        stack_extensions={
            "architecture_signals": proposal.architecture_signals,
            "risk_areas": proposal.risk_areas,
            "needs_human_confirmation": proposal.needs_human_confirmation,
            "scan_warnings": [warning.model_dump(mode="json") for warning in warnings],
            "scan_validation": scan_validation,
            "stack_profile": _build_stack_profile(proposal, scan_validation),
            "scan_metadata": metadata.model_dump(mode="json"),
            "llm_scan_proposal": proposal.model_dump(mode="json"),
        },
    )
    return inventory, CommandCatalog(commands=commands), metadata


def _coverage_warnings(evidence: EvidenceBundle) -> list[ScanWarning]:
    if not evidence.coverage:
        return []
    warnings: list[ScanWarning] = []
    for item in evidence.coverage.warnings:
        warnings.append(
            ScanWarning(
                code=str(item.get("code", "evidence_coverage_warning")),
                message=str(item.get("message", "Evidence coverage warning.")),
                severity="warning",
                evidence=[str(item.get("bucket"))] if item.get("bucket") else [],
            )
        )
    if not evidence.test_files:
        warnings.append(
            ScanWarning(
                code="test_evidence_not_found",
                message="No dedicated test evidence bucket was found; test strategy needs human confirmation.",
                severity="warning",
            )
        )
    return warnings


def _command_from_candidate(
    candidate: LLMCommandCandidate, evidence: EvidenceBundle, warnings: list[ScanWarning]
) -> CommandDefinition:
    gate = candidate.gate
    confidence = candidate.confidence
    if candidate.gate == "hard" and not _command_has_evidence(candidate, evidence):
        gate = "soft"
        confidence = "low"
        warnings.append(
            ScanWarning(
                code="command_without_evidence",
                message=f"Command `{candidate.command}` was downgraded because `{candidate.source}` is without evidence.",
                evidence=[candidate.source],
            )
        )
    return CommandDefinition(
        id=candidate.id,
        command=candidate.command,
        type=candidate.type,
        gate=gate,
        source=candidate.source,
        confidence=confidence,
    )


def _command_has_evidence(candidate: LLMCommandCandidate, evidence: EvidenceBundle) -> bool:
    evidence_paths = {item.path for item in evidence.files + evidence.key_files + evidence.config_files + evidence.ci_files}
    if candidate.source in evidence_paths:
        return True
    command = candidate.command.lower()
    if "mvn" in command and any(path.endswith("pom.xml") for path in evidence_paths):
        return True
    if "dotnet" in command and any(path.endswith((".sln", ".csproj")) for path in evidence_paths):
        return True
    if "npm" in command and any(path.endswith("package.json") for path in evidence_paths):
        return True
    return False


def _validate_stack_claims(evidence: EvidenceBundle, proposal: LLMScanProposal) -> dict[str, object]:
    paths = _all_evidence_paths(evidence)
    values = _all_evidence_values(evidence)
    checked_claims: list[str] = []
    supported_claims: list[str] = []
    unsupported_claims: list[dict[str, str]] = []
    for stack in _normalized_stack_claims(proposal):
        checked_claims.append(stack)
        if _stack_has_evidence(stack, paths, values):
            supported_claims.append(stack)
        else:
            unsupported_claims.append({"stack": stack, "reason": _unsupported_stack_reason(stack)})
    return {
        "checked_claims": checked_claims,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
    }


def _stack_validation_warnings(scan_validation: dict[str, object]) -> list[ScanWarning]:
    warnings: list[ScanWarning] = []
    for item in scan_validation["unsupported_claims"]:
        if not isinstance(item, dict):
            continue
        stack = str(item.get("stack", "unknown"))
        reason = str(item.get("reason", "LLM stack claim is without supporting evidence"))
        warnings.append(
            ScanWarning(
                code="llm_stack_claim_without_evidence",
                message=reason,
                severity="warning",
                evidence=[stack],
            )
        )
    return warnings


def _normalized_stack_claims(proposal: LLMScanProposal) -> list[str]:
    claims: list[str] = []
    for raw_stack in [proposal.primary_stack, *proposal.stacks]:
        stack = STACK_ALIASES.get(raw_stack.strip().lower())
        if stack and stack not in claims:
            claims.append(stack)
    return claims


def _all_evidence_paths(evidence: EvidenceBundle) -> set[str]:
    files = (
        evidence.files
        + evidence.key_files
        + evidence.config_files
        + evidence.ci_files
        + evidence.documents
        + evidence.source_samples
        + evidence.priority_files
        + evidence.test_files
        + evidence.api_entrypoints
        + evidence.risk_files
    )
    return {item.path.lower() for item in files}


def _all_evidence_values(evidence: EvidenceBundle) -> set[str]:
    files = (
        evidence.files
        + evidence.key_files
        + evidence.config_files
        + evidence.ci_files
        + evidence.documents
        + evidence.source_samples
        + evidence.priority_files
        + evidence.test_files
        + evidence.api_entrypoints
        + evidence.risk_files
    )
    values: set[str] = set()
    for item in files:
        values.add(item.path.lower())
        if item.summary:
            values.add(item.summary.lower())
        if item.reason:
            values.add(item.reason.lower())
        if item.bucket:
            values.add(item.bucket.lower())
    return values


def _stack_has_evidence(stack: str, paths: set[str], values: set[str]) -> bool:
    if stack == "java-spring":
        return any(path.endswith((".java", "pom.xml", "build.gradle", "build.gradle.kts")) for path in paths) or any(
            "spring" in value for value in values
        )
    if stack == "dotnet-aspnet":
        return any(path.endswith((".sln", ".csproj", ".cs")) for path in paths)
    if stack == "node":
        return any(path.endswith(("package.json", ".js", ".ts", ".tsx", ".vue")) for path in paths)
    if stack == "python-flask":
        return any(
            path.endswith((".py", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "pipfile", "poetry.lock"))
            for path in paths
        ) or any("flask" in value for value in values)
    return False


def _unsupported_stack_reason(stack: str) -> str:
    if stack == "java-spring":
        return "LLM claimed java-spring but no .java, pom.xml, build.gradle, or Spring evidence was found"
    if stack == "dotnet-aspnet":
        return "LLM claimed dotnet-aspnet but no .sln, .csproj, or .cs evidence was found"
    if stack == "node":
        return "LLM claimed node but no package.json or JS/TS/Vue evidence was found"
    if stack == "python-flask":
        return "LLM claimed python-flask but no Python, pyproject, requirements, or Flask evidence was found"
    return f"LLM claimed {stack} but no supporting evidence was found"


def _veto_impossible_stack(evidence: EvidenceBundle, proposal: LLMScanProposal) -> None:
    paths = {item.path.lower() for item in evidence.files + evidence.key_files + evidence.source_samples}
    values = _all_evidence_values(evidence)
    if proposal.primary_stack == "dotnet-aspnet" and not any(path.endswith((".sln", ".csproj", ".cs")) for path in paths):
        raise ScanConflictError("LLM claimed dotnet-aspnet but no dotnet evidence was found")
    if proposal.primary_stack == "java-spring" and not any(path.endswith((".java", "pom.xml", "build.gradle", "build.gradle.kts")) for path in paths):
        raise ScanConflictError("LLM claimed java-spring but no Java evidence was found")
    if proposal.primary_stack == "python-flask" and not (
        any(path.endswith((".py", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "pipfile", "poetry.lock")) for path in paths)
        or any("flask" in value for value in values)
    ):
        raise ScanConflictError("LLM claimed python-flask but no Python or Flask evidence was found")


def _build_stack_profile(proposal: LLMScanProposal, scan_validation: dict[str, object]) -> dict[str, object]:
    supported = [str(item) for item in scan_validation.get("supported_claims", [])]
    primary_label = STACK_LABELS.get(proposal.primary_stack, proposal.primary_stack)
    composition_label = _composition_label(proposal, supported)
    module_roles = [
        {
            "path": str(module.get("path", ".")),
            "kind": str(module.get("kind", "module")),
            "name": str(module.get("name", "未命名模块")),
        }
        for module in proposal.modules
        if isinstance(module, dict)
    ]
    return {
        "primary_label": primary_label,
        "composition_label": composition_label,
        "supported_stacks": supported,
        "module_roles": module_roles,
    }


def _composition_label(proposal: LLMScanProposal, supported: list[str]) -> str:
    stack_set = {proposal.primary_stack, *supported, *proposal.stacks}
    if proposal.primary_stack == "python-flask" and (
        "node" in supported or stack_set.intersection({"react", "typescript", "vite"})
    ):
        frontend_parts = []
        if "react" in stack_set:
            frontend_parts.append("React")
        if "typescript" in stack_set:
            frontend_parts.append("TypeScript")
        frontend = " / ".join(frontend_parts) if frontend_parts else "前端"
        return f"Python Flask 后端 + {frontend} 前端"
    labels = [STACK_LABELS.get(stack, stack) for stack in supported if stack != "unknown"]
    if labels:
        return " + ".join(dict.fromkeys(labels))
    return STACK_LABELS.get(proposal.primary_stack, proposal.primary_stack)
