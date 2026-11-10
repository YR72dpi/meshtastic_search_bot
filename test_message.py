#!/usr/bin/env python3
import argparse

from bot import answer_question


def parse_position(value: str):
    try:
        lat, lon = value.split(",")
        return float(lat.strip()), float(lon.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--position doit être au format 'latitude,longitude' (ex: 49.4432,1.0993)"
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Teste un message Meshtastic en appelant directement la logique du bot "
            "sans l'envoyer sur le réseau radio."
        )
    )
    parser.add_argument(
        "message",
        help='Message à tester, ex: "/search latest Raspberry Pi 5 model"',
    )
    parser.add_argument(
        "--position",
        type=parse_position,
        help="Optionnel: position de l'expéditeur au format 'latitude,longitude'",
    )
    args = parser.parse_args()

    print(f"Message: {args.message}")
    if args.position is not None:
        print(f"Position: {args.position[0]}, {args.position[1]}")

    answers = answer_question(args.message, args.position)
    print("\nRéponse du bot:\n")

    for index, chunk in enumerate(answers, start=1):
        print(f"--- Partie {index}/{len(answers)} ---")
        print(chunk)
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
