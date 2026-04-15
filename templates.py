"""
src/whatsapp/templates.py
WhatsApp-ready message strings for Axension AI Agent 1.
All messages are under 400 characters. Human tone — not robotic.
"""


def supplier_nudge(name: str, po_num: str, item: str, days: int) -> str:
    """
    1–2 days overdue. Friendly reminder — no pressure yet.

    Example:
        supplier_nudge("Ravi", "PO-1042", "Steel rods", 1)
        → "Hi Ravi, just checking in on PO-1042 (Steel rods) — it's 1 day
           past the delivery date. Could you share an ETA? Helps us keep
           production on track. Thanks! — Axension AI"
    """
    return (
        f"Hi {name}, just checking in on {po_num} ({item}) — it's {days} "
        f"day{'s' if days > 1 else ''} past the delivery date. Could you share "
        f"an ETA? Helps us keep production on track. Thanks! — Axension AI"
    )


def supplier_chase(name: str, po_num: str, item: str, days: int) -> str:
    """
    3–5 days overdue. Firm tone — mentions production impact.

    Example:
        supplier_chase("Ravi", "PO-1042", "Steel rods", 4)
        → "Hi Ravi, PO-1042 (Steel rods) is now 4 days overdue. This is
           starting to affect our production schedule. Please confirm dispatch
           status today. If there's a problem, let us know so we can
           plan. — Axension AI"
    """
    return (
        f"Hi {name}, {po_num} ({item}) is now {days} days overdue. This is "
        f"starting to affect our production schedule. Please confirm dispatch "
        f"status today. If there's a problem, let us know so we can "
        f"plan. — Axension AI"
    )


def supplier_escalate(name: str, po_num: str, item: str, days: int) -> str:
    """
    5+ days overdue. Urgent — requests callback.

    Example:
        supplier_escalate("Ravi", "PO-1042", "Steel rods", 7)
        → "Ravi, PO-1042 (Steel rods) is 7 days overdue — this is now urgent.
           Production is being held up. Please call us back immediately or
           confirm a hard delivery date today. — Axension AI"
    """
    return (
        f"Ravi, {po_num} ({item}) is {days} days overdue — this is now urgent. "
        f"Production is being held up. Please call us back immediately or confirm "
        f"a hard delivery date today. — Axension AI"
    )


def owner_morning_brief(
    factory: str,
    open_pos: int,
    overdue: int,
    deliveries_today: int,
    stock_alerts: int
) -> str:
    """
    7:45 AM daily summary for factory owner.

    Args:
        factory: Factory name/identifier
        open_pos: Number of open purchase orders
        overdue: Number of overdue POs
        deliveries_today: Expected deliveries today
        stock_alerts: Number of low-stock alerts

    Example:
        owner_morning_brief("Factory A", 12, 3, 2, 1)
        → "📋 Morning Brief — Factory A
           Open POs: 12 | Overdue: 3 🔴
           Deliveries today: 2 | Stock alerts: 1 ⚠️
           Agent 1 is following up on overdue orders now. — Axension AI"
    """
    overdue_flag = " 🔴" if overdue > 0 else " ✅"
    stock_flag = " ⚠️" if stock_alerts > 0 else " ✅"

    return (
        f"📋 Morning Brief — {factory}\n"
        f"Open POs: {open_pos} | Overdue: {overdue}{overdue_flag}\n"
        f"Deliveries today: {deliveries_today} | Stock alerts: {stock_alerts}{stock_flag}\n"
        f"Agent 1 is following up on overdue orders now. — Axension AI"
    )


if __name__ == "__main__":
    # Preview all templates
    print(supplier_nudge("Ravi", "PO-1042", "Steel rods", 1))
    print()
    print(supplier_chase("Ravi", "PO-1042", "Steel rods", 4))
    print()
    print(supplier_escalate("Ravi", "PO-1042", "Steel rods", 7))
    print()
    print(owner_morning_brief("Factory A", 12, 3, 2, 1))
