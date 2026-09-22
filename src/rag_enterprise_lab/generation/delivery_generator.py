"""Génération déterministe d'un projet de delivery par client actif, avec une
petite équipe (lead + membres) piochée dans Consulting / Data & AI / Engineering."""

import random
from datetime import date, timedelta

from rag_enterprise_lab.domain.commercial import Client
from rag_enterprise_lab.domain.delivery import Project, ProjectStatus
from rag_enterprise_lab.domain.organization import Employee
from rag_enterprise_lab.generation.namebank import PROJECT_THEMES

STATUS_WEIGHTS: list[tuple[ProjectStatus, int]] = [
    (ProjectStatus.ACTIVE, 65),
    (ProjectStatus.DELIVERED, 20),
    (ProjectStatus.ON_HOLD, 10),
    (ProjectStatus.CANCELLED, 5),
]


def _weighted_choice[T](rng: random.Random, weighted: list[tuple[T, int]]) -> T:
    population = [item for item, _ in weighted]
    weights = [w for _, w in weighted]
    return rng.choices(population, weights=weights, k=1)[0]


def generate_projects(
    rng: random.Random,
    *,
    clients: list[Client],
    leads: list[Employee],
    members: list[Employee],
    reference_date: date,
) -> list[Project]:
    projects: list[Project] = []
    for i, client in enumerate(clients, start=1):
        lead = leads[(i - 1) % len(leads)]
        team_size = 2 + (i % 3)  # 2 à 4 membres, déterministe
        start = (i - 1) % len(members)
        team_member_ids = sorted(
            {members[(start + j) % len(members)].employee_id for j in range(team_size)}
        )
        projects.append(
            Project(
                project_id=f"PRJ-{i:04d}",
                project_code=f"PJ{i:03d}",
                name=f"{client.name.split(' ')[0]} {rng.choice(PROJECT_THEMES)}",
                client_id=client.customer_id,
                status=_weighted_choice(rng, STATUS_WEIGHTS),
                delivery_lead_id=lead.employee_id,
                team_member_ids=team_member_ids,
                start_date=reference_date - timedelta(days=rng.randint(30, 720)),
            )
        )
    return projects
