"""Five weeks of feedback for a fictional SaaS product.

Exists because trend detection needs history. On a fresh clone every theme
reports ``insufficient_history``, which hides the one capability that
separates this from a stateless demo. Replaying this corpus produces genuine
trends — computed by the real pipeline, not fabricated rows.

The corpus tells a deliberate story so all four trend directions appear:

* **billing** dominates weeks 1-3, then a fix lands  -> ``declining``
* **signup** is background noise until a week-5 regression -> ``spiking``
* **dashboard** slowness grumbles along at a constant rate -> ``steady``
* **mobile** crashes appear for the first time in week 5 -> ``emerging``

Each entry deliberately contains exactly one topic keyword. That is a
constraint of the offline embedder used by ``--offline`` (it maps keywords to
orthogonal dimensions); real embeddings have no such requirement.
"""

from __future__ import annotations

WEEK_1 = [
    {"text": "Billing charged my card twice this month", "user_type": "paid", "source": "support"},
    {"text": "Got a double billing charge again, second time now", "user_type": "paid", "source": "support"},
    {"text": "The billing page shows an amount I never agreed to", "user_type": "enterprise", "source": "support"},
    {"text": "Why is my billing total different from the quote?", "user_type": "paid", "source": "nps"},
    {"text": "Billing invoice does not match what I was quoted", "user_type": "enterprise", "source": "sales_call"},
    {"text": "Please fix billing, I was overcharged", "user_type": "paid", "source": "review"},
    {"text": "The dashboard takes forever to load", "user_type": "free", "source": "support"},
    {"text": "Dashboard is unusably slow with a year of data", "user_type": "paid", "source": "support"},
    {"text": "Loading the dashboard spins for thirty seconds", "user_type": "paid", "source": "review"},
    {"text": "Signup flow errored once but worked on retry", "user_type": "free", "source": "support"},
    {"text": "Would love an export to CSV option", "user_type": "paid", "source": "nps"},
    {"text": "Can you add export for the raw numbers?", "user_type": "free", "source": "review"},
    {"text": "Search never finds anything I know exists", "user_type": "paid", "source": "support"},
    {"text": "The search box ignores partial words", "user_type": "free", "source": "support"},
    {"text": "Slack integration keeps disconnecting", "user_type": "paid", "source": "slack"},
    # Noise, to show triage working.
    {"text": "ok", "user_type": "free", "source": "nps"},
    {"text": "https://unrelated-spam.example.com", "user_type": "free", "source": "review"},
]

WEEK_2 = [
    {"text": "Billing took payment twice, need a refund", "user_type": "paid", "source": "support"},
    {"text": "Charged for two seats but billing shows one", "user_type": "enterprise", "source": "support"},
    {"text": "My billing history has a duplicate entry", "user_type": "paid", "source": "support"},
    {"text": "Billing keeps overcharging, considering cancelling", "user_type": "paid", "source": "nps"},
    {"text": "Third billing error this quarter, not acceptable", "user_type": "enterprise", "source": "sales_call"},
    {"text": "The billing receipt total is simply wrong", "user_type": "paid", "source": "review"},
    {"text": "Dashboard load time is still painful", "user_type": "paid", "source": "support"},
    {"text": "It takes ages before the dashboard renders", "user_type": "free", "source": "review"},
    {"text": "Dashboard freezes the tab on large accounts", "user_type": "enterprise", "source": "support"},
    {"text": "Minor hiccup during signup, resolved itself", "user_type": "free", "source": "support"},
    {"text": "An export button would save me hours", "user_type": "paid", "source": "nps"},
    {"text": "Still waiting on export to spreadsheet", "user_type": "paid", "source": "review"},
    {"text": "Search results are in a baffling order", "user_type": "free", "source": "support"},
    {"text": "Cannot get search to match exact phrases", "user_type": "paid", "source": "support"},
    {"text": "The integration with Slack dropped overnight", "user_type": "paid", "source": "slack"},
    {"text": "?????", "user_type": "free", "source": "nps"},
]

WEEK_3 = [
    {"text": "Another duplicate billing charge appeared", "user_type": "paid", "source": "support"},
    {"text": "Billing is wrong again, I want this escalated", "user_type": "enterprise", "source": "support"},
    {"text": "Please audit my billing, the totals drift", "user_type": "paid", "source": "support"},
    {"text": "Billing discrepancy for the third month running", "user_type": "enterprise", "source": "sales_call"},
    {"text": "Refund me, the billing amount is incorrect", "user_type": "paid", "source": "review"},
    {"text": "Dashboard speed has not improved at all", "user_type": "paid", "source": "support"},
    {"text": "Waiting on the dashboard is part of my routine now", "user_type": "free", "source": "review"},
    {"text": "Dashboard rendering blocks everything else", "user_type": "enterprise", "source": "support"},
    {"text": "Signup was fine for me this time", "user_type": "free", "source": "nps"},
    {"text": "Any progress on the export feature?", "user_type": "paid", "source": "support"},
    {"text": "Export to CSV is the one thing missing", "user_type": "enterprise", "source": "nps"},
    {"text": "Search quality is poor for long queries", "user_type": "paid", "source": "support"},
    {"text": "The search index seems stale most days", "user_type": "free", "source": "support"},
    {"text": "Our integration token expires without warning", "user_type": "enterprise", "source": "slack"},
]

# The billing fix ships. Notification complaints appear for the first time.
WEEK_4 = [
    {"text": "Billing looks correct this month, thank you", "user_type": "paid", "source": "nps"},
    {"text": "Dashboard is still the slowest part of the product", "user_type": "paid", "source": "support"},
    {"text": "Dashboard needs to load under two seconds", "user_type": "enterprise", "source": "sales_call"},
    {"text": "Every dashboard visit means a coffee break", "user_type": "free", "source": "review"},
    {"text": "Signup failed twice for a colleague today", "user_type": "paid", "source": "support"},
    {"text": "New teammate could not complete signup", "user_type": "enterprise", "source": "support"},
    {"text": "Export still not available, this is blocking us", "user_type": "enterprise", "source": "support"},
    {"text": "We need export before renewal, honestly", "user_type": "enterprise", "source": "sales_call"},
    {"text": "Search misses records that definitely exist", "user_type": "paid", "source": "support"},
    {"text": "Fuzzy search would help a lot here", "user_type": "free", "source": "nps"},
    {"text": "Our integration silently stopped syncing", "user_type": "paid", "source": "slack"},
    {"text": "I get no notification when a report finishes", "user_type": "paid", "source": "support"},
    {"text": "Notification emails arrive hours late", "user_type": "free", "source": "support"},
    {"text": "Can I turn the notification spam off entirely?", "user_type": "paid", "source": "review"},
]

# A release regresses signup. Mobile crashes surface for the first time.
WEEK_5 = [
    {"text": "Signup is completely broken after the update", "user_type": "paid", "source": "support"},
    {"text": "Cannot complete signup, OAuth fails every attempt", "user_type": "enterprise", "source": "support"},
    {"text": "Signup errors out at the email confirmation step", "user_type": "free", "source": "support"},
    {"text": "New users cannot signup at all right now", "user_type": "enterprise", "source": "sales_call"},
    {"text": "Signup page throws a server error on submit", "user_type": "paid", "source": "support"},
    {"text": "Blocked onboarding ten people, signup is down", "user_type": "enterprise", "source": "support"},
    {"text": "Tried to signup for a trial and it just fails", "user_type": "free", "source": "review"},
    {"text": "Billing has been accurate since the fix, appreciated", "user_type": "paid", "source": "nps"},
    {"text": "Dashboard load times remain a daily annoyance", "user_type": "paid", "source": "support"},
    {"text": "The dashboard is slow but I have learned to wait", "user_type": "free", "source": "review"},
    {"text": "Dashboard still lags on our larger workspace", "user_type": "enterprise", "source": "support"},
    {"text": "Export to CSV please, we ask every month", "user_type": "enterprise", "source": "nps"},
    {"text": "Without export we may switch to a competitor", "user_type": "enterprise", "source": "sales_call"},
    {"text": "The mobile app crashes on launch every time", "user_type": "paid", "source": "app_store"},
    {"text": "Mobile version closes itself when I open a report", "user_type": "free", "source": "app_store"},
    {"text": "Mobile keeps crashing since yesterday", "user_type": "paid", "source": "app_store"},
]

WEEKS: list[tuple[str, list[dict]]] = [
    ("Week 1", WEEK_1),
    ("Week 2", WEEK_2),
    ("Week 3", WEEK_3),
    ("Week 4", WEEK_4),
    ("Week 5 (signup regression ships)", WEEK_5),
]


def weeks_with_ids() -> list[tuple[str, list[dict]]]:
    """The corpus with stable per-item ids assigned."""
    out = []
    for index, (label, items) in enumerate(WEEKS, start=1):
        out.append(
            (
                label,
                [
                    {**item, "id": f"w{index}-{position}"}
                    for position, item in enumerate(items, start=1)
                ],
            )
        )
    return out
