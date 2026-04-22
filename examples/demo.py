"""Quick CLI demo of veriflow."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from veriflow.pipeline import quick_verify, deep_verify


def demo_text():
    print("=" * 60)
    print("VERIFLOW — Text Verification Demo")
    print("=" * 60)

    with open(os.path.join(os.path.dirname(__file__), "fake_news.txt")) as f:
        text = f.read()

    print(f"\nInput:\n{text}")
    print("Verifying claims...\n")

    profiles = quick_verify(text=text)
    _print_profile(profiles)


def demo_url(url: str):
    print("=" * 60)
    print(f"VERIFLOW — URL Verification: {url}")
    print("=" * 60)

    profile = quick_verify(url=url)
    _print_profile(profile)


def _print_profile(profile):
    print(f"Verdict:    {profile.verdict.upper()}")
    print(f"Confidence: {profile.overall_confidence:.0%}")

    for cv in profile.per_claim:
        matching = next((c for c in profile.claims if c.id == cv.claim_id), None)
        text = matching.text if matching else cv.claim_id
        print(f"  [{cv.status[0]}] {text}")
        print(f"      {cv.reasoning}")

    if profile.red_flags:
        print("\nRed Flags:")
        for flag in profile.red_flags:
            print(f"  ! {flag}")

    print(f"\nSummary: {profile.evidence_summary}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        demo_url(sys.argv[1])
    else:
        demo_text()
