"""Sweden-wide municipality coordinates and regional discovery queries."""

MUNICIPALITY_COORDS: dict[str, tuple[float, float]] = {
    "Stockholm": (59.3293, 18.0686),
    "Göteborg": (57.7089, 11.9746),
    "Malmö": (55.605, 13.0038),
    "Uppsala": (59.8586, 17.6389),
    "Linköping": (58.4108, 15.6214),
    "Lund": (55.705, 13.193),
    "Västerås": (59.6099, 16.5448),
    "Örebro": (59.2753, 15.2134),
    "Helsingborg": (56.0465, 12.6945),
    "Jönköping": (57.7826, 14.1618),
    "Norrköping": (58.5877, 16.1924),
    "Umeå": (63.8258, 20.2630),
    "Luleå": (65.5848, 22.1547),
    "Sundsvall": (62.3908, 17.3069),
    "Gävle": (60.6749, 17.1413),
    "Karlstad": (59.3793, 13.5036),
    "Växjö": (56.8777, 14.8091),
    "Halmstad": (56.6745, 12.8578),
    "Borås": (57.721, 12.9401),
    "Täby": (59.4439, 18.0687),
    "Botkyrka": (59.2373, 17.8173),
    "Sollentuna": (59.4281, 17.9509),
    "Nacka": (59.3105, 18.1638),
    "Huddinge": (59.2376, 17.9819),
    "Kalmar": (56.6634, 16.3568),
    "Kristianstad": (56.0294, 14.1567),
    "Visby": (57.6348, 18.2948),
    "Kiruna": (67.8558, 20.2253),
    "Östersund": (63.1792, 14.6357),
    "Falun": (60.6066, 15.6355),
    "Skövde": (58.3908, 13.8454),
    "Trollhättan": (58.2837, 12.2886),
    "Lidköping": (58.5039, 13.1579),
    "Piteå": (65.3172, 21.4794),
    "Varberg": (57.1056, 12.2508),
    "Motala": (58.5371, 15.0369),
    "Karlskrona": (56.1612, 15.5869),
    "Karlskoga": (59.3267, 14.5239),
    "Södertälje": (59.1955, 17.6253),
    "Eskilstuna": (59.3667, 16.5077),
}

# Domain/name fragment → (municipality, lat, lng)
SITE_LOCATION_HINTS: dict[str, tuple[str, float, float]] = {
    "botkyrka": ("Botkyrka", 59.2373, 17.8173),
    "taby": ("Täby", 59.4439, 18.0687),
    "tabyloppis": ("Täby", 59.4439, 18.0687),
    "solvalla": ("Stockholm", 59.3650, 17.9800),
    "roslag": ("Täby", 59.4439, 18.0687),
    "stockholm": ("Stockholm", 59.3293, 18.0686),
    "goteborg": ("Göteborg", 57.7089, 11.9746),
    "göteborg": ("Göteborg", 57.7089, 11.9746),
    "malmo": ("Malmö", 55.605, 13.0038),
    "malmö": ("Malmö", 55.605, 13.0038),
    "uppsala": ("Uppsala", 59.8586, 17.6389),
    "skane": ("Malmö", 55.605, 13.0038),
    "skåne": ("Malmö", 55.605, 13.0038),
    "vastergotland": ("Göteborg", 57.7089, 11.9746),
    "västergötland": ("Göteborg", 57.7089, 11.9746),
    "norrland": ("Umeå", 63.8258, 20.2630),
    "smaland": ("Växjö", 56.8777, 14.8091),
    "småland": ("Växjö", 56.8777, 14.8091),
}

LIGHT_WEB_SEARCH_QUERIES = [
    "loppis kalender sverige site:se",
    "loppmarknad kalender site:se",
    "loppis kalender göteborg",
    "loppis kalender skåne",
    "loppis kalender uppsala",
    "bakluckeloppis sverige",
]

FULL_WEB_SEARCH_QUERIES = [
    *LIGHT_WEB_SEARCH_QUERIES,
    "loppistajm stockholm",
    "loppis kalender malmö",
    "loppis kalender norrland",
    "loppmarknad datum site:se",
    "garageloppis sverige",
    "loppis jönköping kalender",
    "loppis umeå",
]

SOCIAL_SEARCH_QUERIES = [
    "site:facebook.com/events loppis sverige",
    "site:facebook.com/events loppis göteborg",
    "site:facebook.com/events loppis skåne",
    "site:facebook.com/groups loppis sverige",
    "loppis site:instagram.com/p/ sverige",
    "bakluckeloppis facebook events",
]


def infer_site_location(site_name: str, base_url: str) -> tuple[str | None, float | None, float | None]:
    haystack = f"{site_name} {base_url}".lower()
    for key, (municipality, lat, lng) in SITE_LOCATION_HINTS.items():
        if key in haystack:
            return municipality, lat, lng
    return None, None, None


def coords_for_municipality(name: str | None) -> tuple[float, float] | None:
    if not name:
        return None
    lower = name.lower()
    for key, coords in MUNICIPALITY_COORDS.items():
        if key.lower() in lower or lower in key.lower():
            return coords
    return None
