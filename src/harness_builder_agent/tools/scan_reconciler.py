from __future__ import annotations

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.scan import EvidenceBundle, LLMCommandCandidate, LLMScanProposal, ScanMetadata, ScanWarning
from harness_builder_agent.tools.llm_scan_analyzer import SCAN_PROMPT_VERSION


class ScanConflictError(ValueError):
    pass


def reconcile_scan(
    evidence: EvidenceBundle,
    proposal: LLMScanProposal,
    *,
    model: str | None = None,
    base_url: str | None = None,
) -> tuple[ProjectInventory, CommandCatalog, ScanMetadata]:
    _veto_impossible_stack(evidence, proposal)
    warnings: list[ScanWarning] = []
    commands = [_command_from_candidate(candidate, evidence, warnings) for candidate in proposal.command_candidates]
    metadata = ScanMetadata(
        prompt_version=SCAN_PROMPT_VERSION,
        model=model,
        base_url=base_url,
        evidence_file_count=evidence.detected_file_count,
        truncated_files=evidence.truncations,
        warnings=warnings,
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
            "scan_metadata": metadata.model_dump(mode="json"),
            "llm_scan_proposal": proposal.model_dump(mode="json"),
        },
    )
    return inventory, CommandCatalog(commands=commands), metadata


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


def _veto_impossible_stack(evidence: EvidenceBundle, proposal: LLMScanProposal) -> None:
    paths = {item.path.lower() for item in evidence.files + evidence.key_files + evidence.source_samples}
    if proposal.primary_stack == "dotnet-aspnet" and not any(path.endswith((".sln", ".csproj", ".cs")) for path in paths):
        raise ScanConflictError("LLM claimed dotnet-aspnet but no dotnet evidence was found")
    if proposal.primary_stack == "java-spring" and not any(path.endswith((".java", "pom.xml", "build.gradle", "build.gradle.kts")) for path in paths):
        raise ScanConflictError("LLM claimed java-spring but no Java evidence was found")
