import time
from astropy.time import Time
from src.contact_prediction import ContactPredictor, PRESET_GROUND_STATIONS
from src.orbital_mechanics import OrbitalMechanics, OrbitalElements

orb = OrbitalMechanics()
cp = ContactPredictor(orb)
cp.add_ground_station(PRESET_GROUND_STATIONS["svalbard"])

elements = OrbitalElements(
    semi_major_axis=7000,
    eccentricity=0.001,
    inclination=98.7,
    raan=180.0,
    arg_perigee=0.0,
    true_anomaly=0.0,
    epoch=time.time(),
)
start = time.time()
end = start + 0.5 * 3600
step = 30
print("t, elevation (deg)")

t = start
while t <= end:
    state = orb.propagate_orbit(elements, t)
    elev, az = cp.calculate_elevation_azimuth(
        state.position, PRESET_GROUND_STATIONS["svalbard"], Time(t, format="unix")
    )
    vis = cp.is_visible(
        state.position, PRESET_GROUND_STATIONS["svalbard"], Time(t, format="unix")
    )
    print(f"{t:.0f}, {elev:.3f}, vis={vis}")
    t += step

print("done")
