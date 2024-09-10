import requests


base_url = 'https://new.hypatiacatalog.com/hypatia/api/planets/'

all_params = ['pl_mass', 'pl_radius']

def get_planet_data(pl_mass_min: float = None, pl_mass_max: float = None,
                    pl_radius_min: float = None, pl_radius_max: float = None):
    params = {}
    for param in all_params:
        value = locals()[param + '_min']
        if value is not None:
            params[param + '_min'] = value
        value = locals()[param + '_max']
        if value is not None:
            params[param + '_max'] = value
    response = requests.get(base_url, params=params)
    return response.json()


if __name__ == '__main__':
    planet_data = get_planet_data(pl_mass_min=0.3, pl_mass_max=2.0, pl_radius_min=0.5, pl_radius_max=2.0)
    for planet in planet_data:
        simbad_name = planet['_id']
        nea_name = planet['nea_name']
        planets_list = planet['planets_list']
        print(f"Star {simbad_name} (NEA name: {nea_name}) has {len(planets_list)} planets")
        for planet in planets_list:
            planet_letter = planet['letter']
            planet_mass = planet['pl_mass']
            planet_radius = planet['pl_radius']
            print(f"  Planet {planet_letter} has mass {planet_mass} and radius {planet_radius}")
