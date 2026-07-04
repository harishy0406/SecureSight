import argparse
import asyncio
import datetime
import hashlib
import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from securesight.api.core.config import get_settings
from securesight.api.models.alert import Alert, AlertSeverity, AlertStatus
from securesight.api.models.event import Event, EventType
from securesight.api.models.host import Host, HostOS, HostStatus
from securesight.api.models.rule import Rule, RuleAction, RuleSeverity, RuleStatus
from securesight.api.models.user import User

logger = logging.getLogger(__name__)


def _rand(start: int, end: int) -> int:
    return random.randint(start, end)


def _pick[T](items: list[T]) -> T:
    return random.choice(items)


async def seed_demo_data(count: int = 50) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user = User(
            email="demo@securesight.local",
            username="demo",
            hashed_password=hashlib.sha256(b"demosecuresight").hexdigest(),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()
        logger.info("Created demo user (id=%s)", user.id)

        os_list = [HostOS.LINUX, HostOS.WINDOWS, HostOS.MACOS, HostOS.FREEBSD]
        status_list = [HostStatus.ACTIVE, HostStatus.INACTIVE, HostStatus.COMPROMISED]
        hosts = []
        for i in range(10):
            host = Host(
                hostname=f"node-{i + 1:03d}.securesight.local",
                ip_address=f"10.0.{_rand(0, 255)}.{_rand(1, 254)}",
                os=_pick(os_list),
                status=_pick(status_list),
                labels={"env": _pick(["prod", "staging", "dev"]), "region": _pick(["us-east", "eu-west", "ap-south"])},
                owner_id=user.id,
            )
            session.add(host)
            hosts.append(host)
        await session.flush()
        logger.info("Created %d hosts", len(hosts))

        sev_list = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.CRITICAL, AlertSeverity.ERROR]
        rule_action_list = [RuleAction.BLOCK, RuleAction.LOG, RuleAction.ALERT, RuleAction.QUARANTINE]
        rule_sev_list = [RuleSeverity.LOW, RuleSeverity.MEDIUM, RuleSeverity.HIGH, RuleSeverity.CRITICAL]
        rule_status_list = [RuleStatus.ACTIVE, RuleStatus.INACTIVE, RuleStatus.DRAFT, RuleStatus.DEPRECATED]
        for i in range(20):
            rule = Rule(
                name=f"Rule-{i + 1:03d}",
                description=f"Demo rule {i + 1} for testing",
                severity=_pick(rule_sev_list),
                action=_pick(rule_action_list),
                status=_pick(rule_status_list),
                expression=f"cpu_usage > {_rand(80, 95)}",
                enabled=_pick([True, False]),
                owner_id=user.id,
            )
            session.add(rule)
        await session.flush()
        logger.info("Created 20 rules")

        status_map = [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED, AlertStatus.DISMISSED]
        hosts_for_alerts = await session.run_sync(lambda s: s.query(Host).all())
        rules_for_alerts = await session.run_sync(lambda s: s.query(Rule).all())
        for i in range(count):
            alert = Alert(
                title=f"Alert-{i + 1:04d}",
                description=f"Demo alert {i + 1} generated for testing",
                severity=_pick(sev_list),
                status=_pick(status_map),
                source_ip=f"192.168.{_rand(0, 255)}.{_rand(1, 254)}",
                host_id=_pick(hosts_for_alerts).id if hosts_for_alerts else None,
                rule_id=_pick(rules_for_alerts).id if rules_for_alerts else None,
                assigned_to=user.id,
                owner_id=user.id,
                metadata={"demo": True, "seed_iteration": i + 1},
            )
            session.add(alert)
        await session.flush()
        logger.info("Created %d alerts", count)

        event_types = [EventType.LOGIN, EventType.LOGOUT, EventType.ALERT_TRIGGERED, EventType.RULE_CHANGED]
        for i in range(count):
            event = Event(
                event_type=_pick(event_types),
                source=f"source-{_rand(1, 5):03d}",
                description=f"Demo event {i + 1}",
                details={"event_id": i + 1, "simulated": True},
                severity=_pick(sev_list).value,
                owner_id=user.id,
                timestamp=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=_rand(0, 1440)),
            )
            session.add(event)
        await session.flush()
        logger.info("Created %d events", count)

        await session.commit()
        logger.info("Demo data seeding complete!")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data")
    parser.add_argument("--count", type=int, default=50, help="Number of alerts/events to create")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(seed_demo_data(count=args.count))
