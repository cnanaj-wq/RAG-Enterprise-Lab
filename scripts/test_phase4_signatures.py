from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CONTRACTS = ROOT / "data" / "seed" / "expected_contracts.json"
SHORTCUTS_CONFIG = ROOT / "config" / "shortcuts.yml"
RESTRICTED_MESSAGE = (
    "🔒 Cette information appartient à une catégorie documentaire restreinte "
    "à laquelle votre profil n'a pas accès."
)


def load_contracts() -> list[dict]:
    return json.loads(
        EXPECTED_CONTRACTS.read_text(encoding="utf-8")
    )


def month_key(value: str) -> str:
    """
    Accepts YYYY-MM and normalizes to YYYY-MM.
    """
    datetime.strptime(value, "%Y-%m")
    return value


def load_allowed_groups() -> set[str]:
    config = yaml.safe_load(
        SHORTCUTS_CONFIG.read_text(encoding="utf-8")
    )
    return set(
        config["shortcuts"]["/signatures"]["allowed_groups"]
    )


def authorize(groups: list[str]) -> bool:
    return bool(set(groups) & load_allowed_groups())


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--month",
        default="2026-09",
        help="Mois au format YYYY-MM",
    )
    parser.add_argument(
        "--group",
        action="append",
        default=None,
        help="Groupe utilisateur. Répétable.",
    )

    args = parser.parse_args()
    groups = args.group or []

    if not authorize(groups):
        print(RESTRICTED_MESSAGE)
        return

    target_month = month_key(args.month)

    contracts = [
        contract
        for contract in load_contracts()
        if contract["expected_close_date"].startswith(target_month)
    ]

    counts = Counter(
        contract["signature_status"]
        for contract in contracts
    )

    total = len(contracts)

    signed = counts["SIGNED"]

    in_progress = (
        counts["SENT"]
        + counts["VIEWED"]
        + counts["PARTIALLY_SIGNED"]
    )

    to_process = counts["NOT_SENT"]

    failed = (
        counts["DECLINED"]
        + counts["BLOCKED"]
    )

    signed_rate = (
        (signed / total) * 100
        if total
        else 0.0
    )

    print("🧭 Shortcut : /signatures mois")
    print()
    print(f"📅 Mois                 {target_month}")
    print()
    print(f"📄 Contrats attendus    {total}")
    print(f"✅ Signés               {signed}")
    print(f"⏳ En cours             {in_progress}")
    print(f"🆕 À traiter            {to_process}")
    print(f"🚫 Échecs               {failed}")
    print()
    print(f"📊 Taux signé           {signed_rate:.1f} %")
    print()

    print("🔎 Détail des statuts")
    print(f"   ✅ SIGNED             {counts['SIGNED']}")
    print(f"   🆕 NOT_SENT           {counts['NOT_SENT']}")
    print(f"   📤 SENT               {counts['SENT']}")
    print(f"   👀 VIEWED             {counts['VIEWED']}")
    print(
        f"   ✍️ PARTIALLY_SIGNED   "
        f"{counts['PARTIALLY_SIGNED']}"
    )
    print(f"   ❌ DECLINED           {counts['DECLINED']}")
    print(f"   🚫 BLOCKED            {counts['BLOCKED']}")

    print()

    if total == 0:
        print("⚠️ Aucun contrat attendu pour ce mois.")
    elif failed > 0:
        print(
            "⚠️ Des contrats nécessitent une attention immédiate."
        )
    elif signed == total:
        print("✅ Tous les contrats du mois sont signés.")
    else:
        print(
            "⏳ La campagne de signature est encore en cours."
        )


if __name__ == "__main__":
    main()
