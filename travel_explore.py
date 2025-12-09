#!/usr/bin/env python3
"""
Travel Explore Script - Fetches travel destinations from SearchAPI and lists by cheapest price.
Uses the Google Travel Explore API via SearchAPI.
"""

import os
import sys
import requests
from typing import Optional


def get_travel_destinations(
    departure_id: str = "ZRH",
    adults: int = 1,
    time_period: str = "one_week_trip_in_the_next_six_months",
    interests: str = "popular",
    currency: str = "CHF",
    gl: str = "CH",
    hl: str = "en-US",
    max_price: Optional[int] = None,
    travel_class: str = "economy",
    stops: str = "any",
) -> dict:
    """
    Fetch travel destinations from SearchAPI Google Travel Explore.

    Args:
        departure_id: IATA airport code (e.g., 'ZRH' for Zurich)
        adults: Number of adults (1-9)
        time_period: Travel period (e.g., 'one_week_trip_in_the_next_six_months' or 'YYYY-MM-DD..YYYY-MM-DD')
        interests: Type of destinations ('popular', 'outdoors', 'beaches', 'museums', 'history', 'skiing')
        currency: Currency code (e.g., 'CHF', 'EUR', 'USD')
        gl: Country code for localization (e.g., 'CH' for Switzerland)
        hl: Language code (e.g., 'en-US', 'de')
        max_price: Maximum flight price filter
        travel_class: Flight class ('economy', 'premium_economy', 'business', 'first_class')
        stops: Stop preference ('any', 'nonstop', 'one_stop_or_fewer', 'two_stops_or_fewer')

    Returns:
        API response as dictionary
    """
    api_key = os.environ.get("SEARCHAPI_API_KEY")
    if not api_key:
        raise ValueError(
            "SEARCHAPI_API_KEY environment variable is not set. "
            "Please set it with: export SEARCHAPI_API_KEY='your_api_key'"
        )

    base_url = "https://www.searchapi.io/api/v1/search"

    params = {
        "engine": "google_travel_explore",
        "departure_id": departure_id,
        "adults": adults,
        "time_period": time_period,
        "interests": interests,
        "currency": currency,
        "gl": gl,
        "hl": hl,
        "travel_class": travel_class,
        "stops": stops,
    }

    if max_price is not None:
        params["max_price"] = max_price

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.get(base_url, params=params, headers=headers)
    response.raise_for_status()

    return response.json()


def sort_by_cheapest(destinations: list) -> list:
    """
    Sort destinations by flight price (cheapest first).

    Args:
        destinations: List of destination objects from the API response

    Returns:
        Sorted list of destinations
    """
    def get_price(dest):
        flight = dest.get("flight", {})
        price = flight.get("price")
        if price is None:
            return float("inf")
        return price

    return sorted(destinations, key=get_price)


def build_flight_link(
    departure_id: str,
    dest_airport: str,
    outbound_date: str,
    return_date: str,
    adults: int = 1,
    currency: str = "CHF"
) -> str:
    """
    Build a Google Flights search URL.

    Args:
        departure_id: Departure airport IATA code
        dest_airport: Destination airport IATA code
        outbound_date: Outbound date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD)
        adults: Number of adults
        currency: Currency code

    Returns:
        Google Flights URL
    """
    from urllib.parse import quote
    base_url = "https://www.google.com/travel/flights"
    query = f"flights from {departure_id} to {dest_airport} on {outbound_date} returning {return_date}"
    return f"{base_url}?q={quote(query)}&curr={currency}&px={adults}"


def format_destination(
    dest: dict,
    rank: int,
    currency: str = "CHF",
    departure_id: str = "ZRH",
    adults: int = 1
) -> str:
    """
    Format a destination for display.

    Args:
        dest: Destination object from API
        rank: Rank number for display
        currency: Currency symbol to display
        departure_id: Departure airport IATA code
        adults: Number of adults

    Returns:
        Formatted string representation
    """
    name = dest.get("name", "Unknown")
    country = dest.get("country", "Unknown")
    flight = dest.get("flight", {})

    price = flight.get("price", "N/A")
    airline = flight.get("airline_name", "Unknown")
    stops = flight.get("stops", "N/A")
    duration = flight.get("flight_duration", "N/A")
    airport_code = flight.get("airport_code", "")

    outbound = dest.get("outbound_date", "N/A")
    return_date = dest.get("return_date", "N/A")

    avg_cost_night = dest.get("avg_cost_per_night")
    cost_str = f"{avg_cost_night} {currency}/night" if avg_cost_night else "N/A"

    stop_text = "direct" if stops == 0 else f"{stops} stop(s)"

    # Build flight link
    flight_link = ""
    if airport_code and outbound != "N/A" and return_date != "N/A":
        flight_link = build_flight_link(departure_id, airport_code, outbound, return_date, adults, currency)

    return f"""
{rank}. {name}, {country}
   Flight: {price} {currency} ({airline}, {stop_text}, {duration})
   Dates: {outbound} -> {return_date}
   Avg accommodation: {cost_str}
   Book: {flight_link}
"""


def main():
    """Main function to fetch and display travel destinations."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch travel destinations from SearchAPI and list by cheapest price"
    )
    parser.add_argument(
        "--departure", "-d",
        default="ZRH",
        help="Departure airport IATA code (default: ZRH for Zurich)"
    )
    parser.add_argument(
        "--adults", "-a",
        type=int,
        default=1,
        help="Number of adults (default: 1)"
    )
    parser.add_argument(
        "--period", "-p",
        default="one_week_trip_in_the_next_six_months",
        help="Time period (default: one_week_trip_in_the_next_six_months)"
    )
    parser.add_argument(
        "--interests", "-i",
        choices=["popular", "outdoors", "beaches", "museums", "history", "skiing"],
        default="popular",
        help="Type of destinations (default: popular)"
    )
    parser.add_argument(
        "--currency", "-c",
        default="CHF",
        help="Currency code (default: CHF)"
    )
    parser.add_argument(
        "--max-price", "-m",
        type=int,
        help="Maximum flight price filter"
    )
    parser.add_argument(
        "--travel-class", "-t",
        choices=["economy", "premium_economy", "business", "first_class"],
        default="economy",
        help="Travel class (default: economy)"
    )
    parser.add_argument(
        "--stops", "-s",
        choices=["any", "nonstop", "one_stop_or_fewer", "two_stops_or_fewer"],
        default="any",
        help="Stop preference (default: any)"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=20,
        help="Number of destinations to display (default: 20)"
    )

    args = parser.parse_args()

    print(f"🌍 Fetching travel destinations from {args.departure}...")
    print(f"   Interests: {args.interests} | Period: {args.period}")
    print(f"   Class: {args.travel_class} | Stops: {args.stops}")
    print()

    try:
        response = get_travel_destinations(
            departure_id=args.departure,
            adults=args.adults,
            time_period=args.period,
            interests=args.interests,
            currency=args.currency,
            max_price=args.max_price,
            travel_class=args.travel_class,
            stops=args.stops,
        )

        destinations = response.get("destinations", [])

        if not destinations:
            print("No destinations found. Try different search parameters.")
            sys.exit(0)

        sorted_destinations = sort_by_cheapest(destinations)

        # Limit results
        display_destinations = sorted_destinations[:args.limit]

        print(f"📋 Found {len(destinations)} destinations. Showing top {len(display_destinations)} by cheapest price:\n")
        print("=" * 60)

        for rank, dest in enumerate(display_destinations, 1):
            print(format_destination(dest, rank, args.currency, args.departure, args.adults))

        print("=" * 60)
        print(f"\n💡 Tip: Use --help to see all available options")

    except ValueError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ API error: {e}", file=sys.stderr)
        if e.response.status_code == 401:
            print("   Check your SEARCHAPI_API_KEY is valid", file=sys.stderr)
        elif e.response.status_code == 429:
            print("   Rate limit exceeded. Please wait and try again.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
