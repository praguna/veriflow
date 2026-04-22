import argparse
import sys
from veriflow.pipeline import quick_verify, deep_verify


def main():
    parser = argparse.ArgumentParser(description="Veriflow — Multi-modal content verification")
    parser.add_argument("--text", "-t", type=str, help="Text to verify")
    parser.add_argument("--image", "-i", type=str, help="Path to image file")
    parser.add_argument("--pdf", "-p", type=str, help="Path to PDF file")
    parser.add_argument("--url", "-u", type=str, help="URL to verify")
    parser.add_argument("--deep", "-d", action="store_true", help="Deep verification (includes reverse image search)")
    parser.add_argument("--json", "-j", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not any([args.text, args.image, args.pdf, args.url]):
        parser.print_help()
        sys.exit(1)

    image_bytes = None
    if args.image:
        with open(args.image, "rb") as f:
            image_bytes = f.read()

    verify = deep_verify if args.deep else quick_verify
    profile = verify(text=args.text, image_bytes=image_bytes, file_path=args.pdf, url=args.url)

    if args.json:
        print(profile.model_dump_json(indent=2))
    else:
        _print_report(profile)


def _print_report(profile):
    print(f"\n{'='*60}")
    print(f"VERIFLOW TRUST PROFILE ({profile.depth.upper()})")
    print(f"{'='*60}")
    print(f"\nVerdict:    {profile.verdict.upper()}")
    print(f"Confidence: {profile.overall_confidence:.0%}")

    print(f"\nClaims ({len(profile.claims)}):")
    status_icon = {"supported": "+", "refuted": "x", "uncertain": "?"}
    for cv in profile.per_claim:
        icon = status_icon.get(cv.status, "?")
        matching_claim = next((c for c in profile.claims if c.id == cv.claim_id), None)
        claim_text = matching_claim.text if matching_claim else cv.claim_id
        print(f"  [{icon}] {claim_text}")
        print(f"      {cv.status} ({cv.confidence:.0%}) — {cv.reasoning}")

    if profile.red_flags:
        print(f"\nRed Flags:")
        for flag in profile.red_flags:
            print(f"  ! {flag}")

    print(f"\nSummary: {profile.evidence_summary}\n")


if __name__ == "__main__":
    main()
