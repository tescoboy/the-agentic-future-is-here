#!/usr/bin/env python3
"""
Create Spotify music catalog with real artists, albums, and singles.
Based on Spotify's popular content and trending music.
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_session
from app.models import Product
from sqlmodel import Session, select
import random

def create_spotify_music_products():
    """Create 250 unique Spotify music products with real artists, albums, and singles."""
    
    # Spotify content based on the provided URLs
    spotify_content = [
        # Popular Artists from Spotify
        {
            "name": "Kendrick Lamar",
            "description": "Hip-hop and rap artist known for conscious lyrics and innovative sound. Appeals to ages 16-35, urban and suburban demographics, music enthusiasts and social justice advocates.",
            "price_cpm": 45.0,
            "delivery_type": "CTV",
            "targeting": "Urban Youth",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "Drake",
            "description": "Canadian rapper and R&B singer, mainstream appeal with melodic rap style. Targets ages 16-40, diverse urban demographics, pop and hip-hop fans worldwide.",
            "price_cpm": 50.0,
            "delivery_type": "CTV",
            "targeting": "Mainstream Music",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "The Weeknd",
            "description": "R&B and pop artist with dark, atmospheric sound. Appeals to ages 18-35, nightlife and music festival attendees, fans of alternative R&B.",
            "price_cpm": 48.0,
            "delivery_type": "CTV",
            "targeting": "Young Adults",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "Morgan Wallen",
            "description": "Country music superstar with crossover appeal. Targets ages 18-45, rural and suburban demographics, country and pop music fans.",
            "price_cpm": 42.0,
            "delivery_type": "Audio",
            "targeting": "Country Music",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "Post Malone",
            "description": "Genre-blending artist mixing hip-hop, rock, and pop. Appeals to ages 16-35, diverse demographics, fans of experimental and mainstream music.",
            "price_cpm": 46.0,
            "delivery_type": "CTV",
            "targeting": "Gen Z/Millennial",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "Taylor Swift",
            "description": "Global pop superstar with massive fanbase across genres. Targets ages 13-45, predominantly female but broad appeal, pop and country music fans.",
            "price_cpm": 55.0,
            "delivery_type": "CTV",
            "targeting": "Pop Music",
            "formats": ["Video", "Audio", "Display"]
        },
        {
            "name": "Billie Eilish",
            "description": "Alternative pop artist with unique aesthetic and sound. Appeals to ages 13-30, Gen Z demographic, fans of indie and alternative music.",
            "price_cpm": 47.0,
            "delivery_type": "CTV",
            "targeting": "Gen Z Alternative",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "Sabrina Carpenter",
            "description": "Rising pop star with Disney origins, now mainstream success. Targets ages 13-25, teenage and young adult female demographic, pop music fans.",
            "price_cpm": 40.0,
            "delivery_type": "Audio",
            "targeting": "Teen Pop",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "SZA",
            "description": "Contemporary R&B artist with introspective lyrics and smooth vocals. Appeals to ages 18-35, urban demographics, R&B and neo-soul fans.",
            "price_cpm": 44.0,
            "delivery_type": "Audio",
            "targeting": "R&B/Neo-Soul",
            "formats": ["Audio", "Video"]
        },
        {
            "name": "Future",
            "description": "Trap and hip-hop artist known for auto-tuned vocals and heavy beats. Targets ages 16-35, urban demographics, trap and hip-hop enthusiasts.",
            "price_cpm": 43.0,
            "delivery_type": "Audio",
            "targeting": "Hip-Hop/Trap",
            "formats": ["Audio", "Video"]
        },
        
        # Popular Albums
        {
            "name": "HIT ME HARD AND SOFT",
            "description": "Billie Eilish's latest album showcasing her evolution as an artist. Appeals to ages 13-30, alternative pop fans, streaming-first audience.",
            "price_cpm": 47.0,
            "delivery_type": "Audio",
            "targeting": "Alternative Pop",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "Short n' Sweet",
            "description": "Sabrina Carpenter's breakthrough album with catchy pop anthems. Targets ages 13-25, teen and young adult demographics, pop music enthusiasts.",
            "price_cpm": 40.0,
            "delivery_type": "Audio",
            "targeting": "Teen Pop",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "CHROMAKOPIA",
            "description": "Tyler, The Creator's experimental album blending hip-hop with alternative sounds. Appeals to ages 16-35, hip-hop and alternative music fans.",
            "price_cpm": 45.0,
            "delivery_type": "Audio",
            "targeting": "Alternative Hip-Hop",
            "formats": ["Audio", "Video"]
        },
        {
            "name": "SOS",
            "description": "SZA's critically acclaimed R&B album with emotional depth and smooth production. Targets ages 18-35, R&B fans, urban demographics.",
            "price_cpm": 44.0,
            "delivery_type": "Audio",
            "targeting": "Contemporary R&B",
            "formats": ["Audio", "Video"]
        },
        {
            "name": "Un Verano Sin Ti",
            "description": "Bad Bunny's reggaeton masterpiece that dominated global charts. Appeals to ages 16-40, Latino demographics, reggaeton and Latin music fans.",
            "price_cpm": 48.0,
            "delivery_type": "Audio",
            "targeting": "Latin Music",
            "formats": ["Audio", "Video"]
        },
        
        # Trending Songs (from Top 50 Global and trending)
        {
            "name": "BIRDS OF A FEATHER",
            "description": "Billie Eilish's hit single with dreamy production and introspective lyrics. Targets ages 13-30, alternative pop fans, TikTok-active audience.",
            "price_cpm": 47.0,
            "delivery_type": "Audio",
            "targeting": "Gen Z Pop",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "Die With A Smile",
            "description": "Lady Gaga and Bruno Mars collaboration combining pop and soul elements. Appeals to ages 18-45, mainstream pop fans, cross-generational appeal.",
            "price_cpm": 52.0,
            "delivery_type": "CTV",
            "targeting": "Mainstream Pop",
            "formats": ["Video", "Audio"]
        },
        {
            "name": "Tears",
            "description": "Trending emotional ballad with viral TikTok appeal. Targets ages 16-30, social media active users, fans of emotional pop music.",
            "price_cpm": 38.0,
            "delivery_type": "Audio",
            "targeting": "TikTok Viral",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "Man I Need",
            "description": "Olivia Dean's soulful R&B track gaining mainstream recognition. Appeals to ages 18-35, R&B enthusiasts, UK music scene followers.",
            "price_cpm": 41.0,
            "delivery_type": "Audio",
            "targeting": "Neo-Soul",
            "formats": ["Audio", "Display"]
        },
        {
            "name": "Golden",
            "description": "Upbeat pop anthem with cross-cultural appeal and energetic production. Targets ages 16-35, pop music fans, dance and EDM enthusiasts.",
            "price_cpm": 43.0,
            "delivery_type": "Audio",
            "targeting": "Dance Pop",
            "formats": ["Audio", "Video"]
        },
    ]
    
    # Generate additional unique entries to reach 250
    additional_artists = [
        "Ariana Grande", "Ed Sheeran", "Dua Lipa", "Olivia Rodrigo", "Lil Nas X",
        "Doja Cat", "Harry Styles", "Adele", "Bruno Mars", "Rihanna",
        "Bad Bunny", "J Balvin", "Rosalía", "The Chainsmokers", "Calvin Harris",
        "David Guetta", "Martin Garrix", "Skrillex", "Deadmau5", "Diplo",
        "Kanye West", "Jay-Z", "Eminem", "50 Cent", "Snoop Dogg",
        "Dr. Dre", "Lil Wayne", "Nicki Minaj", "Cardi B", "Megan Thee Stallion",
        "Lizzo", "Beyoncé", "Alicia Keys", "John Legend", "Frank Ocean",
        "Childish Gambino", "Tyler, The Creator", "Mac Miller", "Logic",
        "Chance the Rapper", "Big Sean", "2 Chainz", "Travis Scott", "A$AP Rocky",
        "Kid Cudi", "Lana Del Rey", "Halsey", "Charli XCX", "BLACKPINK",
        "BTS", "Stray Kids", "TWICE", "NewJeans", "IU"
    ]
    
    additional_albums = [
        "Folklore", "Evermore", "Midnights", "1989 (Taylor's Version)", "Red (Taylor's Version)",
        "After Hours", "Dawn FM", "Beauty Behind the Madness", "Starboy", "Blinding Lights",
        "Purpose", "Changes", "Justice", "Ghost Stories", "÷ (Divide)",
        "Perfect", "Shape of You", "Bad Habits", "Future Nostalgia", "Dua Lipa",
        "SOUR", "Guts", "Good 4 U", "Drivers License", "Vampire",
        "Montero", "Industry Baby", "Old Town Road", "Panini", "Star Walkin'",
        "Planet Her", "Hot Pink", "Say So", "Kiss Me More", "Paint The Town Red",
        "Fine Line", "Harry's House", "As It Was", "Watermelon Sugar", "Adore You",
        "30", "25", "21", "Someone Like You", "Rolling in the Deep",
        "24K Magic", "Uptown Funk", "That's What I Like", "Count On Me", "Just The Way You Are"
    ]
    
    additional_singles = [
        "Blinding Lights", "Watermelon Sugar", "Levitating", "Good 4 U", "Industry Baby",
        "Stay", "Heat Waves", "Anti-Hero", "As It Was", "Running Up That Hill",
        "Bad Habit", "I'm Good", "Unholy", "Flowers", "Kill Bill",
        "Vampire", "Seven", "Paint The Town Red", "Greedy", "What It Is",
        "Cruel Summer", "Midnight Rain", "Karma", "Lavender Haze", "Espresso",
        "Unholy", "I'm Good (Blue)", "Calm Down", "Flowers", "Kill Bill",
        "Boy's a Liar Pt. 2", "Fast Car", "Dance The Night", "Parachute",
        "Spider-Man: Across the Spider-Verse", "What It Is (Block Boy)", "Lovin On Me",
        "Texas Hold 'Em", "Fortnight", "I Had Some Help", "Not Like Us", "Please Please Please",
        "Good Luck, Babe!", "Taste", "I Can Do It With a Broken Heart", "Ordinary"
    ]
    
    # Generate genre-specific content
    genres = [
        ("Hip-Hop", ["Rap", "Trap", "Boom Bap", "Drill", "Conscious Rap"]),
        ("Pop", ["Dance Pop", "Electropop", "Teen Pop", "Art Pop", "Synth Pop"]),
        ("R&B", ["Contemporary R&B", "Neo-Soul", "Alternative R&B", "Smooth R&B", "Trap Soul"]),
        ("Electronic", ["EDM", "House", "Techno", "Dubstep", "Trance"]),
        ("Rock", ["Indie Rock", "Alternative Rock", "Pop Rock", "Hard Rock", "Punk Rock"]),
        ("Country", ["Modern Country", "Country Pop", "Americana", "Folk Country", "Country Rock"]),
        ("Latin", ["Reggaeton", "Latin Pop", "Bachata", "Salsa", "Regional Mexican"]),
        ("K-Pop", ["Korean Pop", "K-Hip Hop", "K-R&B", "K-Rock", "K-Indie"])
    ]
    
    # Create comprehensive catalog
    all_products = spotify_content.copy()
    
    # Add more artists
    for artist in additional_artists:
        genre_info = random.choice(genres)
        subgenre = random.choice(genre_info[1])
        all_products.append({
            "name": artist,
            "description": f"{subgenre} artist with distinctive style and growing fanbase. Appeals to ages {random.choice(['13-25', '16-35', '18-40', '20-45'])}, {random.choice(['urban', 'suburban', 'diverse', 'mainstream'])} demographics, {genre_info[0].lower()} music enthusiasts.",
            "price_cpm": round(random.uniform(35.0, 60.0), 2),
            "delivery_type": random.choice(["Audio", "CTV", "Display"]),
            "targeting": subgenre,
            "formats": random.choice([["Audio"], ["Video"], ["Audio", "Video"], ["Audio", "Display"], ["Video", "Audio", "Display"]])
        })
    
    # Add more albums
    for album in additional_albums:
        genre_info = random.choice(genres)
        subgenre = random.choice(genre_info[1])
        all_products.append({
            "name": album,
            "description": f"Popular {subgenre.lower()} album with critical acclaim and commercial success. Targets ages {random.choice(['16-30', '18-35', '20-40', '25-45'])}, {genre_info[0].lower()} fans, streaming-first audience.",
            "price_cpm": round(random.uniform(35.0, 55.0), 2),
            "delivery_type": random.choice(["Audio", "CTV"]),
            "targeting": f"{subgenre} Album",
            "formats": random.choice([["Audio"], ["Audio", "Display"], ["Audio", "Video"]])
        })
    
    # Add more singles
    for single in additional_singles:
        genre_info = random.choice(genres)
        subgenre = random.choice(genre_info[1])
        all_products.append({
            "name": single,
            "description": f"Chart-topping {subgenre.lower()} single with viral appeal and radio play. Appeals to ages {random.choice(['13-25', '16-35', '18-40'])}, social media active users, {genre_info[0].lower()} enthusiasts.",
            "price_cpm": round(random.uniform(30.0, 50.0), 2),
            "delivery_type": random.choice(["Audio", "CTV", "Display"]),
            "targeting": f"{subgenre} Single",
            "formats": random.choice([["Audio"], ["Audio", "Display"], ["Video", "Audio"]])
        })
    
    # Ensure we have exactly 250 unique products
    unique_products = []
    seen_names = set()
    
    for product in all_products:
        if product["name"] not in seen_names and len(unique_products) < 250:
            unique_products.append(product)
            seen_names.add(product["name"])
    
    # Fill remaining slots if needed
    while len(unique_products) < 250:
        genre_info = random.choice(genres)
        subgenre = random.choice(genre_info[1])
        unique_name = f"Trending {subgenre} Track {len(unique_products) + 1}"
        
        if unique_name not in seen_names:
            unique_products.append({
                "name": unique_name,
                "description": f"Emerging {subgenre.lower()} track gaining popularity across streaming platforms. Targets ages 16-35, early music adopters, {genre_info[0].lower()} discovery audience.",
                "price_cpm": round(random.uniform(30.0, 45.0), 2),
                "delivery_type": random.choice(["Audio", "Display"]),
                "targeting": f"Emerging {subgenre}",
                "formats": ["Audio"]
            })
            seen_names.add(unique_name)
    
    return unique_products[:250]

def replace_spotify_products():
    """Replace all existing Spotify products with new music catalog."""
    session = next(get_session())
    
    try:
        # Delete existing Spotify products (tenant_id = 5)
        existing_products = session.exec(
            select(Product).where(Product.tenant_id == 5)
        ).all()
        
        print(f"🗑️  Deleting {len(existing_products)} existing Spotify products...")
        
        for product in existing_products:
            session.delete(product)
        session.commit()
        
        # Create new products
        new_products = create_spotify_music_products()
        print(f"🎵 Creating {len(new_products)} new Spotify music products...")
        
        for product_data in new_products:
            product = Product(
                tenant_id=5,  # Spotify tenant ID
                name=product_data["name"],
                description=product_data["description"],
                price_cpm=product_data["price_cpm"],
                delivery_type=product_data["delivery_type"],
                formats_json=json.dumps(product_data["formats"]),  # Convert to JSON string
                targeting_json=json.dumps({"targeting": product_data["targeting"]})  # Convert to JSON string
            )
            session.add(product)
        
        session.commit()
        print("✅ Spotify music catalog created successfully!")
        
        # Verify the results
        final_count = len(session.exec(select(Product).where(Product.tenant_id == 5)).all())
        print(f"📊 Final Spotify product count: {final_count}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    replace_spotify_products()
