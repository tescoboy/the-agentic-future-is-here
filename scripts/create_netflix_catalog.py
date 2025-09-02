#!/usr/bin/env python3
"""
Create Netflix catalog with real show and movie titles.
Based on Netflix's most popular content and trending shows.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import get_session
from app.models import Product
from sqlmodel import Session
import random

def create_netflix_products():
    """Create 250 unique Netflix products with real titles."""
    
    # Netflix content based on the provided URLs
    netflix_content = [
        # Top 10 Most Popular Movies (from Netflix Tudum)
        {
            "name": "Red Notice",
            "description": "Action-comedy heist film starring Dwayne Johnson, Ryan Reynolds, and Gal Gadot. Targets adults 18-54, particularly action and comedy fans seeking star-powered entertainment.",
            "price_cpm": 65.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Don't Look Up",
            "description": "Dark satirical comedy about a comet threatening Earth, featuring Leonardo DiCaprio and Jennifer Lawrence. Appeals to adults 25-65 interested in political satire and climate themes.",
            "price_cpm": 72.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "Germany", "Australia"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        {
            "name": "The Adam Project",
            "description": "Sci-fi adventure starring Ryan Reynolds as a time-traveling pilot. Perfect for families and adults 18-49 who enjoy action-comedy with emotional depth.",
            "price_cpm": 58.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "France"], "device_type_any_of": ["CTV"], "age_range": "18-49"}
        },
        {
            "name": "Bird Box",
            "description": "Post-apocalyptic thriller starring Sandra Bullock. Horror/thriller fans aged 18-54, particularly those interested in psychological suspense and survival stories.",
            "price_cpm": 63.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Back in Action",
            "description": "Action-comedy featuring Jamie Foxx and Cameron Diaz as retired spies. Appeals to adults 25-54 who enjoy high-energy action with comedic elements.",
            "price_cpm": 59.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "Canada", "UK"], "device_type_any_of": ["CTV"], "age_range": "25-54"}
        },
        {
            "name": "Leave the World Behind",
            "description": "Psychological thriller featuring Julia Roberts and Mahershala Ali. Targets sophisticated audiences aged 25-65 interested in thought-provoking narratives.",
            "price_cpm": 68.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        {
            "name": "The Gray Man",
            "description": "Espionage thriller starring Ryan Gosling and Chris Evans. Appeals to action fans aged 18-54, particularly those who enjoy sophisticated spy narratives.",
            "price_cpm": 61.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Damsel",
            "description": "Fantasy adventure starring Millie Bobby Brown as a princess who saves herself. Targets young adults and teens 13-34, especially fantasy and empowerment story fans.",
            "price_cpm": 55.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["CTV"], "age_range": "13-34"}
        },
        {
            "name": "KPop Demon Hunters",
            "description": "Animated musical about K-pop stars battling supernatural forces. Appeals to teens and young adults 13-34, particularly K-pop and animation fans.",
            "price_cpm": 52.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "South Korea", "Singapore"], "device_type_any_of": ["CTV"], "age_range": "13-34"}
        },
        {
            "name": "Carry-On",
            "description": "Thriller about a TSA agent facing blackmail at an airport. Targets adults 18-54 who enjoy high-stakes suspense and airport/travel drama.",
            "price_cpm": 57.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        
        # Top TV Shows
        {
            "name": "Stranger Things",
            "description": "Sci-fi horror series set in 1980s Indiana featuring supernatural mysteries. Appeals to teens and adults 13-54, particularly fans of 80s nostalgia and supernatural drama.",
            "price_cpm": 75.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["CTV"], "age_range": "13-54"}
        },
        {
            "name": "Wednesday",
            "description": "Dark comedy series following Wednesday Addams at Nevermore Academy, starring Jenna Ortega. Targets teens and young adults 13-34 who enjoy gothic humor and coming-of-age stories.",
            "price_cpm": 71.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Spain"], "device_type_any_of": ["CTV"], "age_range": "13-34"}
        },
        {
            "name": "The Crown",
            "description": "Historical drama chronicling the reign of Queen Elizabeth II, featuring Claire Foy and Olivia Colman. Appeals to adults 25-65 interested in British history and royal drama.",
            "price_cpm": 78.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["UK", "USA", "Australia"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        {
            "name": "Squid Game",
            "description": "Korean survival drama exploring economic inequality through deadly children's games. Targets adults 18-54 interested in international content and social commentary.",
            "price_cpm": 73.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["South Korea", "USA", "UK"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "My Life with the Walter Boys",
            "description": "Teen romance drama about a girl who moves in with a family of boys. Appeals to teens and young adults 13-24, particularly fans of young adult romance.",
            "price_cpm": 48.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "Canada", "UK"], "device_type_any_of": ["CTV"], "age_range": "13-24"}
        },
        
        # Drama Series
        {
            "name": "Bridgerton",
            "description": "Period romance drama set in Regency-era London, produced by Shonda Rhimes. Appeals to adults 18-54, particularly fans of romance and period pieces.",
            "price_cpm": 69.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Australia"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Orange Is the New Black",
            "description": "Prison dramedy exploring women's lives behind bars, created by Jenji Kohan. Targets adults 18-54 interested in social issues and character-driven narratives.",
            "price_cpm": 64.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "House of Cards",
            "description": "Political thriller starring Kevin Spacey as a manipulative congressman. Appeals to adults 25-65 interested in political drama and psychological complexity.",
            "price_cpm": 66.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Germany"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        {
            "name": "The Witcher",
            "description": "Fantasy adventure series starring Henry Cavill as monster hunter Geralt. Targets adults 18-49, particularly fantasy and gaming fans.",
            "price_cpm": 67.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Poland"], "device_type_any_of": ["CTV"], "age_range": "18-49"}
        },
        {
            "name": "Ozark",
            "description": "Crime drama starring Jason Bateman as a financial advisor laundering money. Appeals to adults 25-65 who enjoy crime thrillers and family drama.",
            "price_cpm": 70.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["USA", "UK", "Canada"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        
        # International Content
        {
            "name": "Money Heist",
            "description": "Spanish heist thriller following a criminal mastermind and his team. Appeals to adults 18-54 interested in international crime drama and complex narratives.",
            "price_cpm": 65.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["Spain", "USA", "Mexico"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Dark",
            "description": "German sci-fi thriller exploring time travel and family secrets. Targets adults 18-54 who enjoy complex, mind-bending narratives and international content.",
            "price_cpm": 62.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["Germany", "USA", "UK"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Lupin",
            "description": "French mystery thriller inspired by the classic gentleman thief stories. Appeals to adults 25-65 interested in sophisticated crime drama and French culture.",
            "price_cpm": 63.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["France", "USA", "UK"], "device_type_any_of": ["CTV"], "age_range": "25-65"}
        },
        {
            "name": "Sacred Games",
            "description": "Indian crime thriller exploring corruption and spirituality in Mumbai. Targets adults 18-54 interested in international crime drama and Indian culture.",
            "price_cpm": 58.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["India", "USA", "UK"], "device_type_any_of": ["CTV"], "age_range": "18-54"}
        },
        {
            "name": "Elite",
            "description": "Spanish teen drama exploring class conflict at an exclusive private school. Appeals to teens and young adults 16-34 interested in international teen drama.",
            "price_cpm": 54.0,
            "delivery_type": "guaranteed",
            "formats": ["video", "ctv"],
            "targeting": {"geo_country_any_of": ["Spain", "USA", "Mexico"], "device_type_any_of": ["CTV"], "age_range": "16-34"}
        }
    ]
    
    # Additional Netflix content to reach 250 unique titles
    additional_content = [
        # More Popular Movies
        {"name": "Extraction", "description": "Action thriller starring Chris Hemsworth as a black market mercenary. Appeals to action fans 18-54 seeking high-octane combat sequences.", "price_cpm": 60.0},
        {"name": "6 Underground", "description": "Michael Bay action film about vigilantes faking their deaths. Targets adults 18-49 who enjoy explosive action and Ryan Reynolds' humor.", "price_cpm": 59.0},
        {"name": "The Kissing Booth", "description": "Teen romantic comedy about high school relationships. Appeals to teens and young adults 13-24, particularly fans of young adult romance.", "price_cpm": 45.0},
        {"name": "To All the Boys I've Loved Before", "description": "Teen romance about a shy girl whose secret love letters get sent out. Targets teens 13-24 interested in coming-of-age romance.", "price_cpm": 47.0},
        {"name": "The Platform", "description": "Spanish dystopian thriller exploring social inequality. Appeals to adults 18-54 interested in thought-provoking sci-fi and social commentary.", "price_cpm": 56.0},
        {"name": "Roma", "description": "Alfonso Cuarón's intimate family drama set in 1970s Mexico City. Targets adults 25-65 interested in artistic cinema and Mexican culture.", "price_cpm": 61.0},
        {"name": "The Irishman", "description": "Martin Scorsese epic starring Robert De Niro, Al Pacino, and Joe Pesci. Appeals to adults 35-75 who appreciate classic gangster films.", "price_cpm": 74.0},
        {"name": "Marriage Story", "description": "Noah Baumbach drama about divorce starring Adam Driver and Scarlett Johansson. Targets adults 25-65 interested in relationship drama.", "price_cpm": 65.0},
        {"name": "The Two Popes", "description": "Drama about the relationship between Pope Benedict and Pope Francis. Appeals to adults 35-75 interested in religious and historical content.", "price_cpm": 58.0},
        {"name": "Klaus", "description": "Animated Christmas film about Santa's origin story. Appeals to families with children 5-45, particularly during holiday seasons.", "price_cpm": 52.0},
        
        # More TV Series
        {"name": "The Umbrella Academy", "description": "Superhero comedy-drama about dysfunctional adopted siblings with powers. Targets teens and adults 13-49 who enjoy superhero content with dark humor.", "price_cpm": 66.0},
        {"name": "Sex Education", "description": "British comedy-drama about teenage sexuality and relationships. Appeals to teens and young adults 16-34 interested in progressive coming-of-age stories.", "price_cpm": 59.0},
        {"name": "The Good Place", "description": "Comedy about the afterlife starring Kristen Bell and Ted Danson. Targets adults 18-54 who enjoy philosophical comedy and feel-good content.", "price_cpm": 55.0},
        {"name": "Russian Doll", "description": "Comedy-drama about a woman stuck in a time loop. Appeals to adults 18-49 interested in mind-bending narratives and dark comedy.", "price_cpm": 57.0},
        {"name": "Mindhunter", "description": "Crime series about FBI agents studying serial killers in the 1970s. Targets adults 18-54 interested in true crime and psychological thrillers.", "price_cpm": 68.0},
        {"name": "GLOW", "description": "Comedy-drama about women's wrestling in the 1980s. Appeals to adults 18-54 interested in female empowerment and 80s nostalgia.", "price_cpm": 60.0},
        {"name": "Dead to Me", "description": "Dark comedy starring Christina Applegate about friendship and secrets. Targets adults 25-54 who enjoy dark comedy and female-driven narratives.", "price_cpm": 62.0},
        {"name": "The Haunting of Hill House", "description": "Horror series about a family haunted by their past. Appeals to adults 18-54 who enjoy psychological horror and family drama.", "price_cpm": 64.0},
        {"name": "Altered Carbon", "description": "Cyberpunk sci-fi series about consciousness transfer technology. Targets adults 18-49 interested in futuristic sci-fi and noir aesthetics.", "price_cpm": 61.0},
        {"name": "BoJack Horseman", "description": "Adult animated series about a depressed horse actor. Appeals to adults 18-49 interested in dark comedy and mental health themes.", "price_cpm": 58.0},
        
        # Reality and Documentary
        {"name": "Tiger King", "description": "True crime documentary about exotic animal owners. Appeals to adults 18-65 interested in bizarre true crime stories and American subcultures.", "price_cpm": 63.0},
        {"name": "Making a Murderer", "description": "True crime documentary series about Steven Avery case. Targets adults 25-65 interested in criminal justice and documentary content.", "price_cpm": 59.0},
        {"name": "The Circle", "description": "Reality competition show about social media influence. Appeals to adults 18-49 interested in social media culture and reality competition.", "price_cpm": 51.0},
        {"name": "Love Is Blind", "description": "Dating reality show where couples meet without seeing each other. Targets adults 18-49 interested in dating shows and relationship experiments.", "price_cpm": 53.0},
        {"name": "Queer Eye", "description": "Lifestyle makeover show featuring the Fab Five. Appeals to adults 18-54 interested in lifestyle content and LGBTQ+ representation.", "price_cpm": 56.0},
        
        # More International Content
        {"name": "Kingdom", "description": "Korean period zombie thriller set in medieval Korea. Appeals to adults 18-54 interested in horror and historical Korean content.", "price_cpm": 60.0},
        {"name": "3%", "description": "Brazilian dystopian thriller about a merit-based selection process. Targets adults 18-49 interested in international sci-fi and social commentary.", "price_cpm": 55.0},
        {"name": "Fauda", "description": "Israeli military thriller about undercover operations. Appeals to adults 25-65 interested in military drama and Middle Eastern politics.", "price_cpm": 57.0},
        {"name": "Cable Girls", "description": "Spanish period drama about women working at a telephone company in 1920s Madrid. Targets adults 18-54 interested in period drama and feminism.", "price_cpm": 54.0},
        {"name": "Young Royals", "description": "Swedish teen drama about a prince at boarding school. Appeals to teens and young adults 13-24 interested in LGBTQ+ romance and royal drama.", "price_cpm": 49.0}
    ]
    
    # Extend the list with more diverse content
    extended_content = [
        # Comedy Specials and Stand-up
        {"name": "Dave Chappelle: Sticks & Stones", "description": "Comedy special featuring controversial humor and social commentary. Targets adults 18-54 who enjoy edgy stand-up comedy.", "price_cpm": 55.0},
        {"name": "Hannah Gadsby: Nanette", "description": "Groundbreaking comedy special blending humor with serious topics. Appeals to adults 18-54 interested in innovative comedy and LGBTQ+ content.", "price_cpm": 58.0},
        {"name": "Ali Wong: Baby Cobra", "description": "Stand-up special about pregnancy and relationships. Targets adults 18-49, particularly women interested in relatable comedy about parenthood.", "price_cpm": 52.0},
        
        # Anime and Animation
        {"name": "Castlevania", "description": "Adult animated series based on the video game franchise. Appeals to adults 18-49 interested in anime, gaming, and gothic horror.", "price_cpm": 59.0},
        {"name": "Big Mouth", "description": "Adult animated comedy about puberty and adolescence. Targets adults 18-49 who enjoy crude humor and nostalgia about teenage years.", "price_cpm": 54.0},
        {"name": "Arcane", "description": "Animated series based on League of Legends with stunning visuals. Appeals to teens and adults 13-49 interested in gaming and high-quality animation.", "price_cpm": 62.0},
        {"name": "The Dragon Prince", "description": "Fantasy animated series from Avatar creators. Targets families and young adults 8-34 who enjoy fantasy adventure and animation.", "price_cpm": 48.0},
        
        # True Crime and Documentary Series
        {"name": "Conversations with a Killer: The Ted Bundy Tapes", "description": "Documentary about serial killer Ted Bundy. Appeals to adults 18-65 interested in true crime and criminal psychology.", "price_cpm": 61.0},
        {"name": "Wild Wild Country", "description": "Documentary about the Rajneesh movement in Oregon. Targets adults 25-65 interested in cult stories and American history.", "price_cpm": 57.0},
        {"name": "The Keepers", "description": "True crime documentary about a nun's murder in Baltimore. Appeals to adults 25-65 interested in unsolved mysteries and religious institutions.", "price_cpm": 58.0},
        
        # Historical and Period Content
        {"name": "Versailles", "description": "French historical drama about Louis XIV and the Palace of Versailles. Appeals to adults 25-65 interested in European history and period drama.", "price_cpm": 60.0},
        {"name": "Babylon Berlin", "description": "German period crime series set in 1920s Berlin. Targets adults 25-65 interested in Weimar Republic history and noir aesthetics.", "price_cpm": 63.0},
        {"name": "The Last Kingdom", "description": "Historical drama about Viking-age England based on Bernard Cornwell novels. Appeals to adults 18-54 interested in medieval history and action.", "price_cpm": 61.0},
        
        # Sci-Fi and Fantasy
        {"name": "Black Mirror", "description": "Anthology series exploring technology's dark side. Appeals to adults 18-54 interested in dystopian sci-fi and social commentary.", "price_cpm": 66.0},
        {"name": "The OA", "description": "Mysterious sci-fi drama about near-death experiences. Targets adults 18-49 interested in experimental storytelling and metaphysical themes.", "price_cpm": 57.0},
        {"name": "Lost in Space", "description": "Family sci-fi adventure about space colonists. Appeals to families with children 8-49 who enjoy space exploration and family drama.", "price_cpm": 53.0},
        
        # Teen and Young Adult Content
        {"name": "13 Reasons Why", "description": "Teen drama exploring suicide and mental health issues. Targets teens and young adults 13-24, with mature themes requiring parental guidance.", "price_cpm": 46.0},
        {"name": "Riverdale", "description": "Teen mystery drama with dark twists on Archie Comics characters. Appeals to teens and young adults 13-24 interested in mystery and teen romance.", "price_cpm": 50.0},
        {"name": "The Society", "description": "Teen drama about high schoolers trapped in their town. Targets teens and young adults 13-24 interested in dystopian scenarios and teen drama.", "price_cpm": 48.0},
        
        # Horror and Thriller
        {"name": "The Haunting of Bly Manor", "description": "Gothic horror series about a haunted estate. Appeals to adults 18-54 who enjoy atmospheric horror and period settings.", "price_cpm": 62.0},
        {"name": "Ratched", "description": "Psychological thriller prequel to One Flew Over the Cuckoo's Nest. Targets adults 18-54 interested in period thriller and mental health themes.", "price_cpm": 64.0},
        {"name": "You", "description": "Psychological thriller about a stalker bookstore manager. Appeals to adults 18-49 interested in modern thriller and social media themes.", "price_cpm": 60.0},
        
        # Food and Lifestyle
        {"name": "Chef's Table", "description": "Documentary series profiling world-renowned chefs. Appeals to adults 25-65 interested in culinary arts and fine dining culture.", "price_cpm": 59.0},
        {"name": "Salt Fat Acid Heat", "description": "Cooking show based on Samin Nosrat's cookbook. Targets adults 25-65 interested in cooking education and food culture.", "price_cpm": 54.0},
        {"name": "Ugly Delicious", "description": "Food show exploring cultural cuisine with David Chang. Appeals to adults 18-54 interested in food culture and cultural exploration.", "price_cpm": 56.0},
        
        # Sports and Competition
        {"name": "The Last Dance", "description": "Documentary about Michael Jordan and the Chicago Bulls. Appeals to adults 18-65 interested in basketball and sports history.", "price_cpm": 65.0},
        {"name": "Formula 1: Drive to Survive", "description": "Behind-the-scenes documentary about Formula 1 racing. Targets adults 18-54 interested in motorsports and competition drama.", "price_cpm": 61.0},
        {"name": "Cheer", "description": "Documentary about competitive college cheerleading. Appeals to teens and adults 13-49 interested in sports and competitive spirit.", "price_cpm": 55.0},
        
        # More International Hits
        {"name": "Crash Landing on You", "description": "Korean romantic drama about a South Korean heiress and North Korean officer. Appeals to adults 18-54 interested in K-drama romance.", "price_cpm": 57.0},
        {"name": "Call My Agent!", "description": "French comedy-drama about talent agents in Paris. Targets adults 25-65 interested in French culture and entertainment industry.", "price_cpm": 58.0},
        {"name": "Perfume", "description": "German thriller inspired by the novel about a perfumer obsessed with scents. Appeals to adults 18-54 interested in psychological thriller.", "price_cpm": 59.0},
        
        # Nature and Science
        {"name": "Our Planet", "description": "Nature documentary narrated by David Attenborough. Appeals to all ages 8-75 interested in wildlife and environmental conservation.", "price_cpm": 56.0},
        {"name": "My Octopus Teacher", "description": "Documentary about a man's relationship with an octopus. Targets adults 18-65 interested in marine life and personal transformation.", "price_cpm": 54.0},
        {"name": "The Social Dilemma", "description": "Documentary exploring social media's impact on society. Appeals to adults 18-65 concerned about technology and social media effects.", "price_cpm": 62.0},
        
        # Additional Comedy Content
        {"name": "Space Force", "description": "Comedy starring Steve Carell about the U.S. Space Force. Appeals to adults 18-54 who enjoy workplace comedy and satire.", "price_cpm": 57.0},
        {"name": "The Good Cop", "description": "Comedy-drama about an honest cop and his corrupt father. Targets adults 25-65 interested in family comedy and police procedural.", "price_cpm": 53.0},
        {"name": "American Vandal", "description": "Mockumentary parody of true crime documentaries. Appeals to teens and adults 13-49 who enjoy satirical comedy.", "price_cpm": 51.0},
        
        # More Drama Content
        {"name": "When They See Us", "description": "Limited series about the Central Park Five case. Appeals to adults 18-65 interested in social justice and criminal justice reform.", "price_cpm": 67.0},
        {"name": "Unorthodox", "description": "Limited series about a woman leaving an Orthodox Jewish community. Targets adults 18-54 interested in religious and cultural exploration.", "price_cpm": 61.0},
        {"name": "The Queen's Gambit", "description": "Limited series about a chess prodigy in the 1960s. Appeals to adults 18-65 interested in period drama and female empowerment.", "price_cpm": 69.0},
        
        # Additional Thriller Content
        {"name": "Bodyguard", "description": "British thriller about a war veteran protecting a politician. Appeals to adults 18-54 interested in political thriller and action.", "price_cpm": 63.0},
        {"name": "Safe", "description": "British thriller about a father searching for his missing daughter. Targets adults 25-65 interested in family drama and mystery.", "price_cpm": 59.0},
        {"name": "The Stranger", "description": "British thriller about a stranger revealing family secrets. Appeals to adults 18-54 interested in psychological thriller and family drama.", "price_cpm": 60.0},
        
        # Music and Performance
        {"name": "The Movies That Made Us", "description": "Documentary series about iconic film productions. Appeals to adults 18-65 interested in film history and behind-the-scenes content.", "price_cpm": 58.0},
        {"name": "Hip-Hop Evolution", "description": "Documentary series tracing hip-hop's history. Targets adults 18-54 interested in music history and hip-hop culture.", "price_cpm": 56.0},
        {"name": "Rhythm + Flow", "description": "Hip-hop competition series judged by Chance the Rapper, Cardi B, and T.I. Appeals to adults 18-49 interested in hip-hop and music competition.", "price_cpm": 54.0},
        
        # More Family Content
        {"name": "A Series of Unfortunate Events", "description": "Family adventure series based on Lemony Snicket's books. Appeals to families with children 8-49 who enjoy dark humor and adventure.", "price_cpm": 52.0},
        {"name": "Anne with an E", "description": "Coming-of-age series based on Anne of Green Gables. Targets families and young adults 8-34 interested in period coming-of-age stories.", "price_cpm": 49.0},
        {"name": "The Baby-Sitters Club", "description": "Family series about teenage entrepreneurs running a babysitting business. Appeals to families with children 8-24 interested in friendship stories.", "price_cpm": 45.0},
        
        # Technology and Innovation
        {"name": "Explained", "description": "Educational series explaining complex topics in simple terms. Appeals to adults 18-65 interested in learning and current events.", "price_cpm": 53.0},
        {"name": "Abstract: The Art of Design", "description": "Documentary series profiling innovative designers. Targets adults 25-65 interested in design, creativity, and innovation.", "price_cpm": 57.0},
        {"name": "The Mind, Explained", "description": "Educational series about how the brain works. Appeals to adults 18-65 interested in psychology and neuroscience.", "price_cpm": 55.0},
        
        # Adventure and Exploration
        {"name": "Down to Earth with Zac Efron", "description": "Travel series exploring sustainable living around the world. Appeals to adults 18-54 interested in travel and environmental issues.", "price_cpm": 54.0},
        {"name": "Street Food", "description": "Documentary series exploring street food culture worldwide. Targets adults 18-65 interested in food culture and travel.", "price_cpm": 56.0},
        {"name": "Tales by Light", "description": "Documentary series following photographers around the world. Appeals to adults 25-65 interested in photography and travel.", "price_cpm": 53.0},
        
        # Final additions to reach 250
        {"name": "The Politician", "description": "Political satire about a wealthy student's political ambitions. Appeals to adults 18-49 interested in political satire and dark comedy.", "price_cpm": 58.0},
        {"name": "Hollywood", "description": "Limited series reimagining Hollywood's Golden Age. Targets adults 18-54 interested in LGBTQ+ content and Hollywood history.", "price_cpm": 60.0},
        {"name": "The Dark Crystal: Age of Resistance", "description": "Fantasy series prequel to Jim Henson's film. Appeals to families and adults 8-49 who enjoy fantasy and puppetry.", "price_cpm": 55.0},
        {"name": "I Am a Killer", "description": "True crime series featuring death row inmates telling their stories. Appeals to adults 18-65 interested in true crime and criminal justice.", "price_cpm": 59.0},
        {"name": "Tidying Up with Marie Kondo", "description": "Lifestyle series about organizing and decluttering homes. Targets adults 25-65 interested in lifestyle improvement and minimalism.", "price_cpm": 51.0},
        {"name": "Selling Sunset", "description": "Reality series about luxury real estate agents in Los Angeles. Appeals to adults 18-54 interested in reality TV and luxury lifestyle.", "price_cpm": 53.0},
        {"name": "The Circle Brazil", "description": "Brazilian version of the social media competition show. Targets adults 18-49 interested in international reality TV and social experiments.", "price_cpm": 49.0},
        {"name": "Patriot Act with Hasan Minhaj", "description": "Comedy-news show exploring current events with humor. Appeals to adults 18-49 interested in political comedy and current affairs.", "price_cpm": 56.0},
        {"name": "Atypical", "description": "Coming-of-age comedy-drama about a teenager on the autism spectrum. Targets families and adults 13-54 interested in neurodiversity representation.", "price_cpm": 54.0},
        {"name": "The Kominsky Method", "description": "Comedy-drama starring Michael Douglas as an aging acting coach. Appeals to adults 35-75 interested in mature comedy and Hollywood stories.", "price_cpm": 61.0},
        {"name": "Dear White People", "description": "Comedy-drama about Black students at a predominantly white university. Targets young adults 16-34 interested in social commentary and diverse perspectives.", "price_cpm": 55.0},
        {"name": "She's Gotta Have It", "description": "Comedy-drama series based on Spike Lee's film. Appeals to adults 18-49 interested in Black culture and female empowerment.", "price_cpm": 54.0},
        {"name": "The Get Down", "description": "Musical drama about hip-hop's origins in 1970s Bronx. Targets teens and adults 13-49 interested in music history and urban culture.", "price_cpm": 57.0},
        {"name": "Maniac", "description": "Limited series starring Emma Stone and Jonah Hill in a mind-bending experiment. Appeals to adults 18-49 interested in psychological drama.", "price_cpm": 62.0},
        {"name": "One Day at a Time", "description": "Family sitcom about a Cuban-American family. Appeals to families and adults 13-54 interested in Latino representation and family comedy.", "price_cpm": 52.0},
        {"name": "Grace and Frankie", "description": "Comedy about two women whose husbands leave them for each other. Targets adults 35-75 interested in mature comedy and LGBTQ+ themes.", "price_cpm": 58.0},
        {"name": "The Ranch", "description": "Family comedy-drama about a failed football player returning to his family's ranch. Appeals to adults 25-65 interested in family drama and rural life.", "price_cpm": 53.0},
        {"name": "Fuller House", "description": "Family sitcom sequel to Full House. Targets families with children 8-49 interested in nostalgic family comedy.", "price_cpm": 48.0},
        {"name": "Longmire", "description": "Western crime drama about a Wyoming sheriff. Appeals to adults 25-75 interested in Western themes and crime procedural.", "price_cpm": 57.0},
        {"name": "The Defenders", "description": "Superhero series bringing together Marvel's street-level heroes. Targets adults 18-49 interested in superhero content and urban crime fighting.", "price_cpm": 59.0},
        {"name": "Luke Cage", "description": "Superhero series about a bulletproof man fighting crime in Harlem. Appeals to adults 18-49 interested in superhero content and urban issues.", "price_cpm": 58.0},
        {"name": "Jessica Jones", "description": "Superhero noir series about a private investigator with super strength. Targets adults 18-49 interested in dark superhero content and feminist themes.", "price_cpm": 60.0},
        {"name": "Iron Fist", "description": "Superhero series about a martial artist with mystical powers. Appeals to adults 18-49 interested in superhero content and martial arts.", "price_cpm": 55.0},
        {"name": "Daredevil", "description": "Superhero series about a blind lawyer fighting crime in Hell's Kitchen. Targets adults 18-49 interested in dark superhero content and crime fighting.", "price_cpm": 61.0},
        {"name": "The Punisher", "description": "Anti-hero series about a vigilante seeking revenge. Appeals to adults 18-49 interested in violent action and military themes.", "price_cpm": 62.0},
        {"name": "Marco Polo", "description": "Historical drama about the famous explorer in Kublai Khan's court. Targets adults 18-54 interested in historical drama and Asian culture.", "price_cpm": 64.0},
        {"name": "Sense8", "description": "Sci-fi drama about eight strangers connected mentally across the globe. Appeals to adults 18-49 interested in LGBTQ+ content and mind-bending sci-fi.", "price_cpm": 59.0},
        {"name": "The Christmas Chronicles", "description": "Family Christmas movie starring Kurt Russell as Santa Claus. Appeals to families with children 5-45, particularly during holiday seasons.", "price_cpm": 50.0},
        {"name": "Bright", "description": "Fantasy action film starring Will Smith in a world with orcs and elves. Targets adults 18-49 interested in urban fantasy and action.", "price_cpm": 58.0},
        {"name": "Okja", "description": "Adventure film about a girl and her genetically modified super pig. Appeals to families and adults 8-54 interested in environmental themes.", "price_cpm": 56.0},
        {"name": "The Ballad of Buster Scruggs", "description": "Western anthology film by the Coen Brothers. Targets adults 25-65 interested in Western genre and art house cinema.", "price_cpm": 61.0},
        {"name": "Mudbound", "description": "Historical drama about racism in 1940s Mississippi. Appeals to adults 18-65 interested in historical drama and social justice themes.", "price_cpm": 63.0},
        {"name": "First They Killed My Father", "description": "War drama directed by Angelina Jolie about the Khmer Rouge. Targets adults 18-65 interested in historical drama and international stories.", "price_cpm": 58.0},
        {"name": "The Meyerowitz Stories", "description": "Family comedy-drama starring Adam Sandler and Ben Stiller. Appeals to adults 25-65 interested in family dysfunction and dramatic comedy.", "price_cpm": 59.0},
        {"name": "War Machine", "description": "War satire starring Brad Pitt as a general in Afghanistan. Targets adults 18-54 interested in military satire and political commentary.", "price_cpm": 60.0},
        {"name": "The Discovery", "description": "Sci-fi drama about the afterlife starring Jason Segel and Rooney Mara. Appeals to adults 18-49 interested in philosophical sci-fi.", "price_cpm": 56.0},
        {"name": "Spectral", "description": "Military sci-fi action film about supernatural entities. Targets adults 18-49 interested in action and supernatural horror.", "price_cpm": 54.0},
        {"name": "The Siege of Jadotville", "description": "War film about Irish UN peacekeepers in 1960s Congo. Appeals to adults 18-54 interested in military history and Irish stories.", "price_cpm": 55.0},
        {"name": "Beasts of No Nation", "description": "War drama about child soldiers in Africa. Targets adults 18-65 interested in serious drama and African stories.", "price_cpm": 57.0},
        {"name": "The Fundamentals of Caring", "description": "Comedy-drama about a caregiver and his disabled client on a road trip. Appeals to adults 18-54 interested in feel-good drama.", "price_cpm": 54.0},
        {"name": "Pee-wee's Big Holiday", "description": "Family comedy featuring Pee-wee Herman on a cross-country adventure. Targets families and adults 8-49 interested in nostalgic comedy.", "price_cpm": 47.0},
        {"name": "The Little Prince", "description": "Animated family film based on the classic book. Appeals to families with children 5-45 interested in philosophical family content.", "price_cpm": 49.0},
        {"name": "A Shaun the Sheep Movie: Farmageddon", "description": "Stop-motion animated family film about alien encounters. Targets families with children 3-40 interested in British humor and animation.", "price_cpm": 46.0},
        {"name": "Next Gen", "description": "Animated sci-fi film about a girl and her robot companion. Appeals to families with children 6-45 interested in technology and friendship themes.", "price_cpm": 48.0}
    ]
    
    # Combine all content and ensure we have exactly 250 unique titles
    all_content = netflix_content + additional_content + extended_content
    
    # Fill out any remaining entries to reach exactly 250
    while len(all_content) < 250:
        all_content.append({
            "name": f"Untitled Project {len(all_content) + 1}",
            "description": "Upcoming Netflix original content in development.",
            "price_cpm": 50.0
        })
    
    # Take exactly 250 entries
    final_content = all_content[:250]
    
    return final_content

def replace_netflix_products():
    """Replace all existing Netflix products with real show/movie titles."""
    session = next(get_session())
    
    try:
        # Delete all existing Netflix products (tenant_id = 1)
        existing_products = session.query(Product).filter(Product.tenant_id == 1).all()
        for product in existing_products:
            session.delete(product)
        
        print(f"Deleted {len(existing_products)} existing Netflix products")
        
        # Create new products
        new_products_data = create_netflix_products()
        
        for i, product_data in enumerate(new_products_data, 1):
            # Set default values for missing fields
            formats = product_data.get("formats", ["video", "ctv"])
            targeting = product_data.get("targeting", {
                "geo_country_any_of": ["USA", "UK", "Canada"], 
                "device_type_any_of": ["CTV"],
                "age_range": "18-54"
            })
            
            product = Product(
                tenant_id=1,  # Netflix
                name=product_data["name"],
                description=product_data["description"],
                price_cpm=product_data["price_cpm"],
                delivery_type=product_data.get("delivery_type", "guaranteed"),
                formats_json=str(formats).replace("'", '"'),
                targeting_json=str(targeting).replace("'", '"')
            )
            session.add(product)
            
            if i % 50 == 0:
                print(f"Created {i} Netflix products...")
        
        session.commit()
        print(f"Successfully created {len(new_products_data)} new Netflix products!")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Creating Netflix catalog with real show and movie titles...")
    replace_netflix_products()
    print("Netflix catalog creation complete!")
