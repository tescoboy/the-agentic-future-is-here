"""
Seed data utilities for creating test tenants and products.
Runs on every startup to ensure test data is always available.
"""

import logging
from sqlalchemy.orm import Session
from app.models import Tenant, Product
from app.repos.tenants import create_tenant
from app.repos.products import create_product

logger = logging.getLogger(__name__)


def seed_test_data(session: Session) -> None:
    """
    Create test tenants and products if they don't exist.
    Runs on every startup to ensure test data is available.
    """
    logger.info("Checking for test data...")
    
    # Try to create tenants and products from CSV
    csv_success = _seed_from_csv(session)
    
    # If CSV seeding failed, create basic test data
    if not csv_success:
        logger.info("CSV seeding failed, creating basic test data...")
        _seed_basic_test_data(session)
    
    logger.info("Test data seeding completed")


def _ensure_test_tenant(session: Session) -> Tenant:
    """Ensure test tenant exists, create if it doesn't."""
    # Check if test tenant exists
    existing_tenant = session.query(Tenant).filter(Tenant.slug == "test-tenant").first()
    if existing_tenant:
        logger.info(f"Test tenant already exists: {existing_tenant.name}")
        return existing_tenant
    
    # Create test tenant
    test_tenant = create_tenant(session, "Test Tenant", "test-tenant")
    logger.info(f"Created test tenant: {test_tenant.name}")
    return test_tenant


def _ensure_test_products(session: Session, tenant_id: int) -> None:
    """Ensure test products exist, create if they don't."""
    # Check if we already have test products
    existing_count = session.query(Product).filter(Product.tenant_id == tenant_id).count()
    if existing_count >= 20:
        logger.info(f"Test products already exist: {existing_count} products")
        return
    
    # Create 20 test products
    test_products = [
        {
            "name": "Premium Audio Sponsorship",
            "description": "High-quality audio sponsorship for premium content with guaranteed delivery and extensive reach across multiple platforms.",
            "price_cpm": 25.50,
            "delivery_type": "guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Video Takeover Campaign",
            "description": "Immersive video takeover experience with full-screen engagement and interactive elements for maximum brand impact.",
            "price_cpm": 45.75,
            "delivery_type": "guaranteed",
            "formats_json": '["video", "take_over"]',
            "targeting_json": '{"geo_country_any_of": ["USA"], "device_type_any_of": ["desktop", "tablet"]}'
        },
        {
            "name": "Native Content Integration",
            "description": "Seamless native content integration that matches the look and feel of the platform for authentic brand storytelling.",
            "price_cpm": 18.25,
            "delivery_type": "non_guaranteed",
            "formats_json": '["native"]',
            "targeting_json": '{"geo_country_any_of": ["UK", "Germany"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Banner Display Network",
            "description": "Wide-reaching banner display network with precise targeting and real-time optimization for optimal performance.",
            "price_cpm": 12.80,
            "delivery_type": "non_guaranteed",
            "formats_json": '["banner"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "Canada"], "device_type_any_of": ["mobile", "desktop", "tablet"]}'
        },
        {
            "name": "Smart Speaker Audio",
            "description": "Voice-activated audio advertising optimized for smart speakers and voice assistants with conversational engagement.",
            "price_cpm": 32.40,
            "delivery_type": "guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["smart_speaker"]}'
        },
        {
            "name": "Mobile-First Video",
            "description": "Mobile-optimized video campaigns designed for vertical viewing with swipeable content and interactive features.",
            "price_cpm": 28.90,
            "delivery_type": "guaranteed",
            "formats_json": '["video"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "France"], "device_type_any_of": ["mobile"]}'
        },
        {
            "name": "Premium Banner Suite",
            "description": "Premium banner advertising suite with high-impact placements and advanced targeting capabilities for brand awareness.",
            "price_cpm": 22.15,
            "delivery_type": "guaranteed",
            "formats_json": '["banner"]',
            "targeting_json": '{"geo_country_any_of": ["Germany", "France"], "device_type_any_of": ["desktop", "tablet"]}'
        },
        {
            "name": "Interactive Native",
            "description": "Interactive native content with gamification elements and user engagement features for deeper brand connection.",
            "price_cpm": 35.60,
            "delivery_type": "guaranteed",
            "formats_json": '["native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Audio Streaming Sponsorship",
            "description": "Exclusive audio streaming sponsorship with pre-roll and mid-roll placements for music and podcast content.",
            "price_cpm": 19.75,
            "delivery_type": "non_guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["mobile", "smart_speaker"]}'
        },
        {
            "name": "Video Interstitial",
            "description": "Full-screen video interstitial ads with skip options and engaging content for maximum viewer attention.",
            "price_cpm": 38.20,
            "delivery_type": "guaranteed",
            "formats_json": '["video"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "Germany"], "device_type_any_of": ["mobile", "tablet"]}'
        },
        {
            "name": "Banner Retargeting",
            "description": "Intelligent banner retargeting campaigns with dynamic content and personalized messaging for conversion optimization.",
            "price_cpm": 15.45,
            "delivery_type": "non_guaranteed",
            "formats_json": '["banner"]',
            "targeting_json": '{"geo_country_any_of": ["UK", "France", "Singapore"], "device_type_any_of": ["desktop", "mobile"]}'
        },
        {
            "name": "Native Story Format",
            "description": "Story-style native content with vertical scrolling and immersive storytelling for social media platforms.",
            "price_cpm": 26.80,
            "delivery_type": "guaranteed",
            "formats_json": '["native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["mobile"]}'
        },
        {
            "name": "Audio Podcast Sponsorship",
            "description": "Premium podcast sponsorship with host-read ads and integrated content for authentic brand integration.",
            "price_cpm": 42.30,
            "delivery_type": "guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "Canada"], "device_type_any_of": ["mobile", "desktop", "smart_speaker"]}'
        },
        {
            "name": "Video Outstream",
            "description": "Outstream video advertising that plays outside of video content with autoplay and sound-off optimization.",
            "price_cpm": 31.65,
            "delivery_type": "non_guaranteed",
            "formats_json": '["video"]',
            "targeting_json": '{"geo_country_any_of": ["Germany", "France", "UK"], "device_type_any_of": ["desktop", "mobile"]}'
        },
        {
            "name": "Banner Programmatic",
            "description": "Programmatic banner advertising with real-time bidding and automated optimization for cost-effective reach.",
            "price_cpm": 11.20,
            "delivery_type": "non_guaranteed",
            "formats_json": '["banner"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["mobile", "desktop", "tablet"]}'
        },
        {
            "name": "Native In-Feed",
            "description": "In-feed native advertising that seamlessly integrates with content feeds for natural user experience.",
            "price_cpm": 24.50,
            "delivery_type": "guaranteed",
            "formats_json": '["native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "France"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Audio Background",
            "description": "Background audio advertising with ambient sound integration and non-intrusive brand messaging.",
            "price_cpm": 16.90,
            "delivery_type": "non_guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["Australia", "Singapore"], "device_type_any_of": ["smart_speaker", "mobile"]}'
        },
        {
            "name": "Video Overlay",
            "description": "Non-intrusive video overlay ads with click-to-expand functionality and contextual relevance.",
            "price_cpm": 29.75,
            "delivery_type": "guaranteed",
            "formats_json": '["video"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "Canada", "UK"], "device_type_any_of": ["desktop", "tablet"]}'
        },
        {
            "name": "Banner Rich Media",
            "description": "Rich media banner advertising with interactive elements, animations, and expandable content.",
            "price_cpm": 33.40,
            "delivery_type": "guaranteed",
            "formats_json": '["banner"]',
            "targeting_json": '{"geo_country_any_of": ["Germany", "France", "Singapore"], "device_type_any_of": ["desktop", "mobile"]}'
        },
        {
            "name": "Native Sponsored Content",
            "description": "Sponsored content in native format with editorial-style presentation and organic user engagement.",
            "price_cpm": 37.85,
            "delivery_type": "guaranteed",
            "formats_json": '["native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["mobile", "desktop"]}'
        }
    ]
    
    # Create products (only if we don't have enough)
    products_to_create = 20 - existing_count
    for i in range(products_to_create):
        product_data = test_products[i]
        product = create_product(
            session=session,
            tenant_id=tenant_id,
            name=product_data["name"],
            description=product_data["description"],
            price_cpm=product_data["price_cpm"],
            delivery_type=product_data["delivery_type"],
            formats_json=product_data["formats_json"],
            targeting_json=product_data["targeting_json"]
        )
        logger.info(f"Created test product: {product.name}")
    
    logger.info(f"Created {products_to_create} test products (total: {existing_count + products_to_create})")


def _seed_from_csv(session: Session) -> bool:
    """Seed tenants and products from CSV file. Returns True if successful, False otherwise."""
    import csv
    import json
    import os
    from pathlib import Path
    
    # Try multiple possible paths
    possible_paths = [
        "./catalog_final.csv",
        "catalog_final.csv",
        "../catalog_final.csv",
        Path(__file__).parent.parent.parent / "catalog_final.csv"
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        logger.warning(f"CSV file not found in any of these locations: {possible_paths}")
        return False
    
    logger.info(f"Found CSV file at: {csv_path}")
    
    # Track created tenants
    tenants = {}
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        product_count = 0
        for row in reader:
            tenant_slug = row['tenant_slug']
            
            # Create tenant if it doesn't exist
            if tenant_slug not in tenants:
                tenant = _ensure_tenant_from_csv(session, tenant_slug)
                tenants[tenant_slug] = tenant
            
            # Create product
            _create_product_from_csv(session, row, tenants[tenant_slug].id)
            product_count += 1
            
            # Log progress every 100 products
            if product_count % 100 == 0:
                logger.info(f"Processed {product_count} products...")
    
                logger.info(f"Seeded {len(tenants)} tenants with products from CSV")
            return True


def _seed_basic_test_data(session: Session) -> None:
    """Create basic test data if CSV seeding fails."""
    # Create a basic test tenant
    test_tenant = _ensure_test_tenant(session)
    
    # Create some basic test products
    _ensure_test_products(session, test_tenant.id)
    
    logger.info("Basic test data created successfully")


def _ensure_tenant_from_csv(session: Session, tenant_slug: str) -> Tenant:
    """Ensure tenant exists, create if it doesn't."""
    existing_tenant = session.query(Tenant).filter(Tenant.slug == tenant_slug).first()
    if existing_tenant:
        logger.info(f"Tenant already exists: {existing_tenant.name}")
        return existing_tenant
    
    # Create tenant with appropriate name
    tenant_names = {
        'tiktok': 'TikTok',
        'iheart-radio': 'iHeart Radio',
        'netflix': 'Netflix',
        'nytimes': 'New York Times'
    }
    
    tenant_name = tenant_names.get(tenant_slug, tenant_slug.title())
    tenant = create_tenant(session, tenant_name, tenant_slug)
    logger.info(f"Created tenant: {tenant.name}")
    return tenant


def _create_product_from_csv(session: Session, row: dict, tenant_id: int) -> None:
    """Create product from CSV row."""
    # Check if product already exists
    existing_product = session.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.name == row['product_name']
    ).first()
    
    if existing_product:
        return  # Product already exists
    
    # Create product
    product = create_product(
        session=session,
        tenant_id=tenant_id,
        name=row['product_name'],
        description=row['description'],
        price_cpm=float(row['price_cpm']),
        delivery_type=row['delivery_type'],
        formats_json=row['formats'],
        targeting_json=row['targeting_json']
    )
    
    logger.debug(f"Created product: {product.name}")
