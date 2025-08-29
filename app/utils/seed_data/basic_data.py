"""
Basic test data creation functions.
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
    from .csv_importer import _seed_from_csv
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
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["mobile"]}'
        },
        {
            "name": "Programmatic Display",
            "description": "Automated programmatic display advertising with real-time bidding and advanced audience targeting capabilities.",
            "price_cpm": 15.60,
            "delivery_type": "non_guaranteed",
            "formats_json": '["banner", "native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "Canada", "UK"], "device_type_any_of": ["desktop", "mobile"]}'
        },
        {
            "name": "Podcast Sponsorship",
            "description": "Targeted podcast sponsorship with host-read endorsements and engaged audience demographics.",
            "price_cpm": 22.30,
            "delivery_type": "guaranteed",
            "formats_json": '["audio"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Social Media Stories",
            "description": "Full-screen social media stories with swipe-up functionality and immersive brand experiences.",
            "price_cpm": 35.20,
            "delivery_type": "guaranteed",
            "formats_json": '["video", "stories"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "France"], "device_type_any_of": ["mobile"]}'
        },
        {
            "name": "Connected TV Advertising",
            "description": "Premium connected TV advertising with high-quality video content and household-level targeting.",
            "price_cpm": 42.80,
            "delivery_type": "guaranteed",
            "formats_json": '["video"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["smart_tv"]}'
        },
        {
            "name": "In-App Advertising",
            "description": "Native in-app advertising seamlessly integrated into mobile applications for optimal user experience.",
            "price_cpm": 19.45,
            "delivery_type": "non_guaranteed",
            "formats_json": '["native", "banner"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Singapore"], "device_type_any_of": ["mobile"]}'
        },
        {
            "name": "Digital Out-of-Home",
            "description": "Digital out-of-home advertising on screens in high-traffic locations with dynamic content capabilities.",
            "price_cpm": 38.90,
            "delivery_type": "guaranteed",
            "formats_json": '["video", "banner"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["digital_signage"]}'
        },
        {
            "name": "Gaming Advertising",
            "description": "Immersive gaming advertising with in-game placements and interactive brand experiences.",
            "price_cpm": 26.75,
            "delivery_type": "non_guaranteed",
            "formats_json": '["video", "native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "E-commerce Retargeting",
            "description": "Precision retargeting campaigns for e-commerce with dynamic product ads and conversion optimization.",
            "price_cpm": 16.20,
            "delivery_type": "non_guaranteed",
            "formats_json": '["banner", "native"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "Newsletter Sponsorship",
            "description": "Premium newsletter sponsorship with editorial integration and engaged subscriber audiences.",
            "price_cpm": 24.60,
            "delivery_type": "guaranteed",
            "formats_json": '["native", "banner"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["desktop", "mobile"]}'
        },
        {
            "name": "Live Streaming Sponsorship",
            "description": "Live streaming sponsorship with real-time engagement and interactive audience participation.",
            "price_cpm": 31.80,
            "delivery_type": "guaranteed",
            "formats_json": '["video", "live"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["mobile", "desktop"]}'
        },
        {
            "name": "AR/VR Advertising",
            "description": "Immersive augmented and virtual reality advertising with interactive 3D brand experiences.",
            "price_cpm": 48.50,
            "delivery_type": "guaranteed",
            "formats_json": '["ar", "vr"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Singapore"], "device_type_any_of": ["mobile", "vr_headset"]}'
        },
        {
            "name": "Voice Search Optimization",
            "description": "Voice search optimized advertising with conversational AI and voice-activated brand interactions.",
            "price_cpm": 29.30,
            "delivery_type": "non_guaranteed",
            "formats_json": '["audio", "voice"]',
            "targeting_json": '{"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["smart_speaker", "mobile"]}'
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


def _seed_basic_test_data(session: Session) -> None:
    """Create basic test data if CSV seeding fails."""
    # Create a basic test tenant
    test_tenant = _ensure_test_tenant(session)
    
    # Create some basic test products
    _ensure_test_products(session, test_tenant.id)
    
    logger.info("Basic test data created successfully")
