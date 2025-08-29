#!/usr/bin/env python3
"""
Generate tenant products CSV with 250 products per tenant.
"""

import csv
import json
import random

# Tenant configurations
TENANTS = {
    'tiktok': {
        'name': 'TikTok',
        'formats': ['video', 'take_over'],
        'delivery_type': 'non_guaranteed',
        'price_range': (15, 25),
        'geo': ['USA', 'UK', 'Germany', 'France', 'Australia', 'Singapore'],
        'devices': ['mobile', 'tablet'],
        'voice': '🔥 VIRAL ALERT! Your brand in front of 1B+ creators!'
    },
    'iheart-radio': {
        'name': 'iHeart Radio',
        'formats': ['audio'],
        'delivery_type': 'guaranteed',
        'price_range': (10, 15),
        'geo': ['USA'],
        'devices': ['mobile', 'smart_speaker', 'desktop'],
        'voice': '🌅 AMERICA\'S #1 AUDIO PLATFORM!'
    },
    'netflix': {
        'name': 'Netflix',
        'formats': ['video'],
        'delivery_type': 'guaranteed',
        'price_range': (50, 80),
        'geo': ['USA', 'UK', 'Germany', 'France', 'Australia', 'Singapore'],
        'devices': ['smart_tv', 'desktop', 'tablet', 'mobile'],
        'voice': '🎬 CINEMA AT HOME!'
    },
    'nytimes': {
        'name': 'New York Times',
        'formats': ['banner', 'native'],
        'delivery_type': 'guaranteed',
        'price_range': (30, 45),
        'geo': ['USA'],
        'devices': ['desktop', 'tablet', 'mobile'],
        'voice': '📰 TRUSTED JOURNALISM REACHES INFLUENTIAL DECISION-MAKERS!'
    }
}

# Product templates for each tenant
PRODUCT_TEMPLATES = {
    'tiktok': [
        'TikTok {category} Challenge',
        'TikTok {category} Takeover',
        'TikTok {category} Live Stream',
        'TikTok {category} Duet',
        'TikTok {category} Story',
        'TikTok {category} Sound Bite',
        'TikTok {category} Dance',
        'TikTok {category} Tutorial',
        'TikTok {category} Review',
        'TikTok {category} Vlog'
    ],
    'iheart-radio': [
        'iHeart {category} Hour',
        'iHeart {category} Drive',
        'iHeart {category} Commute',
        'iHeart {category} Weekend',
        'iHeart {category} Radio',
        'iHeart {category} Station',
        'iHeart {category} Network',
        'iHeart {category} Podcast',
        'iHeart {category} Show',
        'iHeart {category} Time'
    ],
    'netflix': [
        'Netflix {category} Collection',
        'Netflix {category} Series',
        'Netflix {category} Movie',
        'Netflix {category} Season',
        'Netflix {category} Weekend',
        'Netflix {category} Night',
        'Netflix {category} Special',
        'Netflix {category} Exclusive',
        'Netflix {category} Premiere',
        'Netflix {category} Marathon'
    ],
    'nytimes': [
        'New York Times {category} Section',
        'New York Times {category} Edition',
        'New York Times {category} Coverage',
        'New York Times {category} Report',
        'New York Times {category} Feature',
        'New York Times {category} Column',
        'New York Times {category} Page',
        'New York Times {category} Story',
        'New York Times {category} Content',
        'New York Times {category} Placement'
    ]
}

# Categories for each tenant
CATEGORIES = {
    'tiktok': ['Trending', 'Viral', 'Live', 'Dance', 'Beauty', 'Food', 'Comedy', 'Travel', 'Fashion', 'Fitness', 'Gaming', 'Music', 'Art', 'DIY', 'Pets', 'Family', 'Education', 'Business', 'Technology', 'Health', 'Sports', 'Entertainment', 'Lifestyle', 'Shopping', 'Home'],
    'iheart-radio': ['Morning', 'Afternoon', 'Evening', 'Night', 'Country', 'Rock', 'Pop', 'Hip Hop', 'Jazz', 'Classical', 'News', 'Sports', 'Talk', 'Comedy', 'Business', 'Weather', 'Traffic', 'Music', 'Entertainment', 'Lifestyle', 'Health', 'Family', 'Weekend', 'Drive'],
    'netflix': ['Premium', 'Original', 'Horror', 'Comedy', 'Drama', 'Action', 'Romance', 'Thriller', 'Documentary', 'Family', 'Sci-Fi', 'Fantasy', 'Crime', 'Mystery', 'Adventure', 'Animation', 'Historical', 'Musical', 'Western', 'War', 'Sports', 'Biography', 'Romantic Comedy', 'Superhero'],
    'nytimes': ['Business', 'Technology', 'Politics', 'World', 'National', 'Science', 'Health', 'Education', 'Arts', 'Sports', 'Opinion', 'Editorial', 'Weekend', 'Magazine', 'Book Review', 'Food', 'Travel', 'Real Estate', 'Automobiles', 'Style', 'Crossword', 'Obituaries', 'Corrections', 'Letters']
}

def generate_products():
    """Generate 250 products per tenant."""
    products = []
    
    for tenant_slug, config in TENANTS.items():
        print(f"Generating products for {config['name']}...")
        
        for i in range(250):
            # Select random category and template
            category = random.choice(CATEGORIES[tenant_slug])
            template = random.choice(PRODUCT_TEMPLATES[tenant_slug])
            
            # Generate product name
            product_name = template.format(category=category)
            
            # Generate description with tenant voice
            description = generate_description(tenant_slug, category, config)
            
            # Generate price
            price = round(random.uniform(*config['price_range']), 2)
            
            # Generate targeting
            targeting = {
                "geo_country_any_of": random.sample(config['geo'], min(3, len(config['geo']))),
                "device_type_any_of": config['devices']
            }
            
            # Create product
            product = {
                'tenant_slug': tenant_slug,
                'product_name': product_name,
                'description': description,
                'price_cpm': price,
                'delivery_type': config['delivery_type'],
                'formats': json.dumps(config['formats']),
                'targeting_json': json.dumps(targeting)
            }
            
            products.append(product)
    
    return products

def generate_description(tenant, category, config):
    """Generate description with tenant-specific voice."""
    voices = {
        'tiktok': [
            f"🔥 VIRAL ALERT! Your brand in front of 1B+ creators! Join the #TikTok{category} movement with our {category.lower()} sponsorship. Perfect for brands wanting to tap into Gen Z's favorite platform. Reach millions of engaged users who love to discover new products through authentic creator content. Limited availability - get trending NOW! 🚀",
            f"🎥 LIVE & UNFILTERED! Take over TikTok {category.lower()} with your brand message reaching 500K+ real-time viewers. Perfect for product launches, announcements, or brand awareness. Our creators bring authenticity and engagement that traditional ads can't match. When TikTok goes {category.lower()}, your brand goes viral! 📱",
            f"🎵 SOUND ON! Your brand becomes the soundtrack of TikTok {category.lower()} with our exclusive sponsorship. When creators use your branded content, millions hear your message. Perfect for brands wanting to be part of TikTok's {category.lower()} culture. Make some noise! 🔊"
        ],
        'iheart-radio': [
            f"🌅 AMERICA'S {category.upper()} RITUAL! Reach 50M+ listeners during peak {category.lower()} time with guaranteed delivery. Your message hits when America is most engaged. Perfect for brands targeting {category.lower()} audiences. Start their {category.lower()} with your brand! 🎵",
            f"🚗 {category.upper()} DOMINANCE! Capture 45M+ listeners during {category.lower()} hours with guaranteed reach. Your brand message reaches America when they're most engaged. Perfect for brands wanting to connect with {category.lower()} audiences. Make {category.lower()} yours! 🎵",
            f"🏠 HOME SWEET HOME! Reach 30M+ households through {category.lower()} programming with guaranteed delivery. Your brand message reaches families in their most comfortable environment. Perfect for {category.lower()} brands. Be part of their {category.lower()}! 🎵"
        ],
        'netflix': [
            f"🎬 CINEMA AT HOME! Sponsor our {category.lower()} collection reaching 200M+ subscribers who choose quality entertainment. Your brand appears before the world's most sought-after {category.lower()} content. When Netflix premieres {category.lower()}, your brand shines! 🌟",
            f"📺 ORIGINAL CONTENT EXCLUSIVE! Sponsor Netflix's award-winning {category.lower()} series reaching 200M+ engaged subscribers. Your brand appears before {category.lower()} content that viewers can't find anywhere else. Perfect for premium brands wanting exclusive access to Netflix's most loyal {category.lower()} audience. Be original with us! 🏆",
            f"🎭 A-LIST {category.upper()} EXCLUSIVE! Sponsor our {category.lower()} content reaching 100M+ enthusiasts. Your brand appears before Hollywood's most beloved {category.lower()} content. Perfect for premium brands wanting to associate with {category.lower()} excellence. Star power meets brand power! ⭐"
        ],
        'nytimes': [
            f"📰 TRUSTED JOURNALISM REACHES INFLUENTIAL DECISION-MAKERS! Premium {category.lower()} placement on America's most trusted news source. Your brand appears alongside Pulitzer Prize-winning {category.lower()} journalism reaching 5M+ daily readers. Perfect for brands wanting premium context and influential {category.lower()} audience. When quality matters, advertise with quality! 🏆",
            f"💼 {category.upper()} LEADERS READ HERE! Premium placement in our {category.lower()} section reaching 2M+ professionals daily. Your brand appears alongside {category.lower()} news that moves markets. Perfect for brands wanting to reach {category.lower()} decision-makers. Reach the {category.lower()} leaders! 📈",
            f"📖 SEAMLESS INTEGRATION! {category.capitalize()} content that matches the look and feel of The New York Times. Your brand story told through trusted {category.lower()} journalism reaching 5M+ engaged readers. Perfect for brands wanting authentic {category.lower()} storytelling in premium context. Be part of the {category.lower()} story! ✍️"
        ]
    }
    
    return random.choice(voices[tenant])

def write_csv(products, filename='data/tenant_products.csv'):
    """Write products to CSV file."""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['tenant_slug', 'product_name', 'description', 'price_cpm', 'delivery_type', 'formats', 'targeting_json']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for product in products:
            writer.writerow(product)
    
    print(f"Generated {len(products)} products in {filename}")

if __name__ == '__main__':
    products = generate_products()
    write_csv(products)
