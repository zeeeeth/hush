"""
Script to create a names_to_coords.csv file that maps station names to their lat/lng coordinates.
"""

import pandas as pd


def create_names_to_coords():
    # Load the MTA stops cache
    stops_df = pd.read_csv("../../data/processed/mta_stops_cache.csv")
    
    # Create a mapping of name -> {lat, lng}
    # Use a dict to deduplicate (same station name may appear multiple times with N/S variants)
    names_to_coords = {}
    
    for _, row in stops_df.iterrows():
        name = row["name"]
        lat = row["lat"]
        lng = row["lng"]
        
        # Only add if not already in the dict (first occurrence wins)
        # This avoids duplicates from N/S variants
        if name not in names_to_coords:
            names_to_coords[name] = {
                "lat": lat,
                "lng": lng
            }
    
    # Sort by name for easier reading
    sorted_names = sorted(names_to_coords.items())
    
    # Write to CSV
    output_df = pd.DataFrame([
        {"name": name, "lat": coords["lat"], "lng": coords["lng"]}
        for name, coords in sorted_names
    ])
    output_df.to_csv("../../data/processed/names_to_coords.csv", index=False)
    
    print(f"Created names_to_coords.csv with {len(sorted_names)} unique stations")
    
    # Print a sample
    print("\nSample entries:")
    for i, (name, coords) in enumerate(sorted_names):
        if i >= 5:
            break
        print(f"  {name}: ({coords['lat']}, {coords['lng']})")


if __name__ == "__main__":
    create_names_to_coords()
