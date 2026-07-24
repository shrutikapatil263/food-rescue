#Uses the Haversine formula to compute straight-line distance between two
#lat/long points — good enough for city-scale matching without needing
#PostGIS or any DB geo extensions.

#usage:
 #   from donations.matching import get_available_agents_for_donation

  #  matches = get_available_agents_for_donation(donation)
   # for agent, distance_km in matches:
    #    print(agent.name, distance_km)

import math

from donations.models import Agent


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.asin(math.sqrt(a))


def get_available_agents_for_location(latitude, longitude):
    """
    Returns a list of (agent, distance_km) tuples for agents who are:
      - active, verified, and currently 'available'
      - have a known current location
      - within THEIR OWN service_radius_km of the given point
    Sorted nearest-first.
    """
    candidates = Agent.objects.filter(
        is_active=True,
        availability_status='available',
        verification_status='verified',
        current_latitude__isnull=False,
        current_longitude__isnull=False,
    )

    matches = []
    for agent in candidates:
        distance_km = haversine_km(
            latitude, longitude,
            agent.current_latitude, agent.current_longitude,
        )
        if distance_km <= agent.service_radius_km:
            matches.append((agent, round(distance_km, 2)))

    matches.sort(key=lambda pair: pair[1])
    return matches


def get_available_agents_for_donation(donation):
    """Agents available to pick up from the donation's restaurant."""
    restaurant = donation.restaurant
    return get_available_agents_for_location(restaurant.latitude, restaurant.longitude)


def get_available_agents_for_restaurant(restaurant):
    return get_available_agents_for_location(restaurant.latitude, restaurant.longitude)


def get_available_agents_for_recipient(recipient):
    """Agents available near a delivery/recipient point."""
    return get_available_agents_for_location(recipient.latitude, recipient.longitude)