import pytest
from backend.app.services.ship30_skill import Ship30Skill


def test_ship30_skill_principles_prompt():
    prompt = Ship30Skill.get_system_prompt()
    assert "Ship 30 for 30" in prompt
    assert "1-3-1" in prompt
    assert "1,250 words" in prompt
    assert "SKIMMABILITY" in prompt


def test_ship30_essay_analyzer():
    sample_essay = """
# Why Your Retention Curve Is Lying To You

Most founders look at retention backwards.
They celebrate a 5% bump in month one.
They ignore the slow bleed in month six.
They wonder why growth suddenly flatlines.
Here is the uncomfortable truth Elena Verna shared on Lenny's Podcast.

## 1. The Asymmetry of Acquisition vs Retention

When you pour money into top-of-funnel ads, you get dopamine hits.
**The leaky bucket reality:** Every lost customer raises your blended CAC.

- **Metric A:** Natural retention frequency.
- **Metric B:** Product-led expansion loops.
- **Metric C:** Payback period velocity.

## 2. The 3-Step Execution Plan

- **Step 1:** Calculate cohort survival rates after 90 days.
- **Step 2:** Isolate the high-conviction persona.
- **Step 3:** Instrument notification loops tied to core value.

## 3. The Takeaway

Fix the engine before you buy more fuel.
"""
    analysis = Ship30Skill.analyze_essay(sample_essay)
    assert analysis["heading_count"] >= 3
    assert analysis["bullet_point_count"] >= 6
    assert analysis["bold_emphasis_count"] >= 5
    assert analysis["is_skimmable"] is True
