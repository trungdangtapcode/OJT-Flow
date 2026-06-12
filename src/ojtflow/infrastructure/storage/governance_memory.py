"""In-memory tenant/workspace governance repository."""

from __future__ import annotations

from copy import deepcopy
from threading import RLock

from ojtflow.core.contracts.governance import (
    OrganizationGroupMembershipRecord,
    OrganizationGroupRecord,
    OrganizationMembershipRecord,
    OrganizationRecord,
    WorkspaceDetail,
    WorkspaceSettingsRecord,
)
from ojtflow.core.errors import NotFoundError, OJTFlowError
from ojtflow.core.time import utc_now


class InMemoryGovernanceRepository:
    """Stores organization workspace primitives in process memory."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._organizations: dict[str, OrganizationRecord] = {}
        self._memberships: dict[str, OrganizationMembershipRecord] = {}
        self._groups: dict[str, OrganizationGroupRecord] = {}
        self._group_memberships: dict[tuple[str, str], OrganizationGroupMembershipRecord] = {}
        self._settings: dict[str, WorkspaceSettingsRecord] = {}

    def get_current_workspace(self, *, user_id: str) -> WorkspaceDetail | None:
        with self._lock:
            memberships = self._active_memberships(user_id)
            if not memberships:
                return None
            return self._workspace_for_membership(memberships[0])

    def list_workspaces(self, *, user_id: str) -> list[WorkspaceDetail]:
        with self._lock:
            return [
                self._workspace_for_membership(membership)
                for membership in self._active_memberships(user_id)
            ]

    def create_default_workspace(
        self,
        *,
        organization: OrganizationRecord,
        membership: OrganizationMembershipRecord,
        group: OrganizationGroupRecord,
        group_membership: OrganizationGroupMembershipRecord,
        settings: WorkspaceSettingsRecord,
    ) -> WorkspaceDetail:
        with self._lock:
            existing = self.get_current_workspace(user_id=membership.user_id)
            if existing:
                return existing
            self._organizations[organization.organization_id] = organization
            self._memberships[membership.membership_id] = membership
            self._groups[group.group_id] = group
            self._group_memberships[
                (group_membership.group_id, group_membership.user_id)
            ] = group_membership
            self._settings[settings.organization_id] = settings
            return self._workspace_for_membership(membership)

    def update_workspace_settings(
        self,
        *,
        organization_id: str,
        user_id: str,
        settings: dict,
        updated_by_user_id: str,
    ) -> WorkspaceDetail:
        with self._lock:
            membership = self._membership_for_user_org(
                user_id=user_id,
                organization_id=organization_id,
            )
            current = self._settings.get(organization_id)
            if not current:
                raise NotFoundError("Workspace settings were not found.")
            self._settings[organization_id] = current.model_copy(
                update={
                    "settings": deepcopy(settings),
                    "version": current.version + 1,
                    "updated_by_user_id": updated_by_user_id,
                    "updated_at": utc_now().isoformat(),
                }
            )
            return self._workspace_for_membership(membership)

    def create_group(
        self,
        *,
        organization_id: str,
        user_id: str,
        group: OrganizationGroupRecord,
    ) -> WorkspaceDetail:
        with self._lock:
            membership = self._membership_for_user_org(
                user_id=user_id,
                organization_id=organization_id,
            )
            if any(
                existing.organization_id == organization_id and existing.slug == group.slug
                for existing in self._groups.values()
            ):
                raise OJTFlowError(
                    "Organization group slug already exists.",
                    details={"organization_id": organization_id, "slug": group.slug},
                )
            self._groups[group.group_id] = group
            return self._workspace_for_membership(membership)

    def add_membership(
        self,
        *,
        organization_id: str,
        actor_user_id: str,
        membership: OrganizationMembershipRecord,
    ) -> WorkspaceDetail:
        with self._lock:
            actor_membership = self._membership_for_user_org(
                user_id=actor_user_id,
                organization_id=organization_id,
            )
            if any(
                existing.organization_id == organization_id
                and existing.user_id == membership.user_id
                for existing in self._memberships.values()
            ):
                raise OJTFlowError(
                    "Organization membership already exists.",
                    details={
                        "organization_id": organization_id,
                        "user_id": membership.user_id,
                    },
                )
            self._memberships[membership.membership_id] = membership
            return self._workspace_for_membership(actor_membership)

    def _active_memberships(self, user_id: str) -> list[OrganizationMembershipRecord]:
        return sorted(
            [
                membership
                for membership in self._memberships.values()
                if membership.user_id == user_id and membership.status == "active"
            ],
            key=lambda membership: membership.created_at,
        )

    def _membership_for_user_org(
        self,
        *,
        user_id: str,
        organization_id: str,
    ) -> OrganizationMembershipRecord:
        for membership in self._memberships.values():
            if (
                membership.user_id == user_id
                and membership.organization_id == organization_id
                and membership.status == "active"
            ):
                return membership
        raise NotFoundError(
            "Organization workspace was not found for the current user.",
            details={"organization_id": organization_id},
        )

    def _workspace_for_membership(
        self,
        membership: OrganizationMembershipRecord,
    ) -> WorkspaceDetail:
        organization = self._organizations.get(membership.organization_id)
        settings = self._settings.get(membership.organization_id)
        if not organization or not settings:
            raise NotFoundError("Workspace record is incomplete.")
        groups = sorted(
            [
                group
                for group in self._groups.values()
                if group.organization_id == organization.organization_id
            ],
            key=lambda group: (group.slug, group.group_id),
        )
        group_memberships = sorted(
            [
                group_membership
                for group_membership in self._group_memberships.values()
                if group_membership.organization_id == organization.organization_id
            ],
            key=lambda group_membership: (
                group_membership.group_id,
                group_membership.user_id,
            ),
        )
        return WorkspaceDetail(
            organization=organization,
            membership=membership,
            groups=groups,
            group_memberships=group_memberships,
            settings=settings,
        )
