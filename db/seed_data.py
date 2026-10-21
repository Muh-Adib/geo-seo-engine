import json
import logging
from db.session import SessionLocal, init_db
from db.models import Brand, Service, LocationTarget, MediaAsset, Article

logger = logging.getLogger(__name__)

SEED_BRANDS = [
    {
        "id": "unimasi",
        "name": "UNIMASI",
        "slug": "unimasi",
        "platform": "WORDPRESS",
        "domain_url": "https://unimasi.com",
        "wp_endpoint_url": "https://unimasi.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Authoritative, master storytelling, high-ROI visual production, transparent remote pipeline.",
        "core_value_pillars": json.dumps([
            {"title": "CGI Storytelling Mastery", "desc": "Transforming complex mechanical and industrial concepts into visceral visual narratives."},
            {"title": "Bringing Vision to Reality", "desc": "Precision 3D modeling, texturing, and photorealistic lighting that drives engagement."}
        ]),
        "revision_guarantee": "Free 2x revision guarantee",
        "master_output_spec": "Uncompressed 4K master files",
        "cta_tagline": "🎥 Elevate your brand visuals across Australia with UNIMASI.",
        "services": [
            {
                "id": "unimasi-safety",
                "name": "3D Safety Induction Video",
                "pillar_url": "https://unimasi.com/services/3d-safety-induction",
                "anchor_variations": ["3D safety induction video", "HSE visual induction", "mining safety animation", "industrial safety video"],
                "technical_pipeline": ["3D modeling", "LOTO sequence", "fluid & hazard simulation", "LMS SCORM export"],
                "target_personas": ["COOs", "HSE Directors", "Safety Managers", "Operational Leaders"],
                "target_industries": ["Mining & Resources", "Heavy Construction", "Oil & Gas", "Manufacturing"],
                "sub_solutions": [
                    {"title": "Zero-Harm Visual Protocols", "desc": "Step-by-step 3D recreation of critical risk procedures."},
                    {"title": "LOTO & Hazard Sequences", "desc": "Clear animated lockout-tagout protocols preventing site incidents."},
                    {"title": "Emergency Evacuation Tours", "desc": "Virtual flythroughs of industrial plants for swift personnel egress."},
                    {"title": "Multilingual SCORM Packages", "desc": "Interactive LMS-ready induction modules for contractor compliance."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Safety Audit & Scripting", "desc": "Aligning visual scenarios with local workplace safety regulations."},
                    {"step": 2, "title": "Storyboard & Previsualization", "desc": "Drafting camera angles, hazard highlights, and timing."},
                    {"step": 3, "title": "Precision 3D Modeling", "desc": "Rigging heavy machinery, PPE equipment, and plant assets."},
                    {"step": 4, "title": "Post-Processing & Sound", "desc": "Foley effects, localized voiceover, and motion graphics callouts."},
                    {"step": 5, "title": "Master 4K Delivery", "desc": "Final render delivery in ProRes, MP4, and interactive SCORM formats."}
                ],
                "base_tags": [
                    "3d safety induction video", "hse animation studio", "mining safety video production", "industrial safety cgi",
                    "lockout tagout animation", "contractor induction video", "remote 3d studio yogyakarta", "zero harm safety visuals"
                ]
            },
            {
                "id": "unimasi-marketing",
                "name": "3D Commercial Production",
                "pillar_url": "https://unimasi.com/services/3d-commercial",
                "anchor_variations": ["3D commercial video", "CGI product showcase", "hyperrealistic 3D advertising"],
                "technical_pipeline": ["photoreal texturing", "cinematic lighting", "particle FX", "ACES color pipeline"],
                "target_personas": ["CMOs", "Marketing Directors", "Creative Directors", "Brand Managers"],
                "target_industries": ["Consumer Electronics", "Automotive", "Luxury Goods", "FMCG"],
                "sub_solutions": [
                    {"title": "CGI Product Launches", "desc": "Exploded views and macro camera moves that showcase product craftsmanship."},
                    {"title": "Anamorphic Billboard 3D", "desc": "Forced-perspective illusions engineered for massive curved LED screens."},
                    {"title": "Modular Social Ad Packs", "desc": "Repurposing 1 hero asset into 9:16 vertical stories, 1:1 feeds, and banners."},
                    {"title": "E-Commerce 3D Interactive", "desc": "Real-time web-ready 3D models for immersive product customization."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Creative Concept & Treatment", "desc": "Defining cinematic tone, moodboards, and narrative flow."},
                    {"step": 2, "title": "Animatic & 3D Layout", "desc": "Low-res 3D blocking to lock timing and dynamic camera motion."},
                    {"step": 3, "title": "High-Fidelity Texturing & Lighting", "desc": "Procedural shaders, raytraced refractions, and bespoke materials."},
                    {"step": 4, "title": "Simulation & Soundscape", "desc": "Fluid, cloth, particle simulations, and bespoke sound design."},
                    {"step": 5, "title": "4K Color Grade & Master Delivery", "desc": "ACES color-graded masters optimized for broadcast and digital."}
                ],
                "base_tags": [
                    "3d commercial video", "cgi advertising studio", "3d product animation", "photorealistic commercial",
                    "anamorphic billboard video", "3d animation studio australia", "visual storytelling yogyakarta"
                ]
            }
        ],
        "locations": [
            {
                "id": "unimasi-aus",
                "region_name": "Australia",
                "sub_cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
                "local_context_notes": "Reference Safe Work Australia regulations, mining hubs in Western Australia and Queensland, and Sydney/Melbourne commercial agency standards.",
                "location_tags": ["Australia 3D animation", "Sydney CGI studio", "Melbourne 3D commercial", "Perth mining safety video", "Brisbane visual effects"]
            },
            {
                "id": "unimasi-uae",
                "region_name": "UAE",
                "sub_cities": ["Dubai", "Abu Dhabi", "Sharjah", "Ajman"],
                "local_context_notes": "Mention Dubai Media City, luxury architectural standards, and futuristic DOOH outdoor screens.",
                "location_tags": ["Dubai 3D animation", "Abu Dhabi CGI production", "UAE commercial studio", "Middle East 3D video"]
            }
        ]
    },
    {
        "id": "unicam",
        "name": "UNICAM STUDIO",
        "slug": "unicam-studio",
        "platform": "WORDPRESS",
        "domain_url": "https://unicam.co.id",
        "wp_endpoint_url": "https://unicam.co.id/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "id",
        "brand_voice": "Inovatif, spektakuler, terdepan dalam seni proyeksi visual interaktif dan teknologi panggung.",
        "core_value_pillars": json.dumps([
            {"title": "Penguasaan Ilusi Dimensi Arsitektural", "desc": "Mengubah fasad bangunan bersejarah dan panggung modern menjadi kanvas cerita visual hidup."},
            {"title": "Teknologi Sinkronisasi Presisi Tinggi", "desc": "Perhitungan ANSI lumen, optical blending, dan timecode audio tanpa jeda."}
        ]),
        "revision_guarantee": "Garansi 2x revisi visual gratis",
        "master_output_spec": "Format video resolusi tinggi master 4K/8K uncompressed",
        "cta_tagline": "🎥 Wujudkan pertunjukan visual spektakuler Anda bersama UNICAM STUDIO.",
        "services": [
            {
                "id": "unicam-mapping",
                "name": "Jasa Video Mapping Indonesia",
                "pillar_url": "https://unicam.co.id/layanan/video-mapping",
                "anchor_variations": ["jasa video mapping", "jasa 3D mapping panggung", "jasa projection mapping fasad", "vendor video mapping indonesia"],
                "technical_pipeline": ["3D laser scanning", "warping & edge blending", "high lumen projection", "timecode show control"],
                "target_personas": ["Event Organizer", "Direktur Kreatif", "Dinas Pariwisata", "Brand Activation Manager"],
                "target_industries": ["Pariwisata & Budaya", "Konser & Festival Musik", "Peluncuran Produk Otomotif", "Exhibition Hall"],
                "sub_solutions": [
                    {"title": "Building Facade Mapping", "desc": "Transformasi visual monumental pada gedung cagar budaya dan pencakar langit."},
                    {"title": "Stage & Concert Visuals", "desc": "Visual panggung dinamis dengan sinkronisasi musik live timecode."},
                    {"title": "Immersive Room Projections", "desc": "Ruang imersif 360 derajat untuk galeri seni dan pameran interaktif."},
                    {"title": "Water Screen & Hologram", "desc": "Proyeksi ilusi melayang pada tirai air dan layar holografis panggung."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Survey & 3D Scanning Lokasi", "desc": "Pemindaian geometri fisik bidang proyeksi dengan millimeter-level precision."},
                    {"step": 2, "title": "Storyline & Audio Scoring", "desc": "Perancangan narasi visual, storyboard, dan komposisi musik orisinal."},
                    {"step": 3, "title": "Produksi Konten CGI 3D", "desc": "Pembuatan animasi ilusi kedalaman (trompe-l'oeil) resolusi ultra-tinggi."},
                    {"step": 4, "title": "Simulasi Warping & Pre-Viz", "desc": "Uji coba sudut tembak proyektor dalam model virtual 3D."},
                    {"step": 5, "title": "Eksekusi & Kalibrasi On-Site", "desc": "Penyelarasan optical edge blending dan eksekusi pertunjukan langsung."}
                ],
                "base_tags": [
                    "jasa video mapping indonesia", "vendor projection mapping", "video mapping gedung", "3d projection mapping panggung",
                    "studio video mapping yogyakarta", "harga jasa video mapping", "sewa proyektor lumen tinggi", "konten imersif 360"
                ]
            }
        ],
        "locations": [
            {
                "id": "unicam-id",
                "region_name": "Indonesia",
                "sub_cities": ["Jakarta", "Surabaya", "Bandung", "Semarang", "Yogyakarta", "Bali", "Medan", "Makassar"],
                "local_context_notes": "Sebutkan landmark gedung cagar budaya, festival seni kota, dan standar konser indoor/outdoor di kota-kota besar Indonesia.",
                "location_tags": ["video mapping jakarta", "video mapping surabaya", "jasa mapping bandung", "projection mapping bali", "vendor visual yogyakarta"]
            }
        ]
    },
    {
        "id": "segiatech",
        "name": "SEGIA Tech",
        "slug": "segia-tech",
        "platform": "WORDPRESS",
        "domain_url": "https://www.segiatech.com",
        "wp_endpoint_url": "https://www.segiatech.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Jakarta - Yogyakarta, Indonesia",
        "default_language": "id",
        "brand_voice": "Otoritatif, profesional, solutif, berorientasi hasil industri modern dan efisiensi AI.",
        "core_value_pillars": json.dumps([
            {"title": "Solusi AI Terintegrasi End-to-End", "desc": "Menjembatani model kecerdasan buatan canggih dengan sistem bisnis nyata."},
            {"title": "Kecepatan & Keamanan Standar Enterprise", "desc": "Arsitektur cloud scalable dengan jaminan kepatuhan data ketat."}
        ]),
        "revision_guarantee": "Garansi pendampingan integrasi teknis penuh",
        "master_output_spec": "Kode sumber teruji, dockerized microservices, dan dokumentasi API",
        "cta_tagline": "🎥 Transformasikan bisnis Anda dengan solusi AI terpercaya bersama SEGIA Tech.",
        "services": [
            {
                "id": "segia-aiapps",
                "name": "AI Apps Production Terpercaya",
                "pillar_url": "https://www.segiatech.com/ai-apps-production-terpercaya-jakarta/",
                "anchor_variations": ["ai apps production terpercaya", "jasa pembuatan aplikasi ai", "software house ai jakarta", "pengembangan sistem ai enterprise"],
                "technical_pipeline": ["LLM fine-tuning", "RAG pipeline architecture", "vector database indexing", "FastAPI microservices", "Docker deployment"],
                "target_personas": ["CTOs", "Product Managers", "Enterprise Founders", "Digital Transformation Directors"],
                "target_industries": ["Financial Services & Fintech", "Healthcare & Medical", "Retail & E-Commerce", "Logistics & Supply Chain"],
                "sub_solutions": [
                    {"title": "Custom Enterprise AI Agents", "desc": "Agen cerdas yang mengotomasi alur kerja operasional dan riset data kompleks."},
                    {"title": "RAG Knowledge Management", "desc": "Sistem tanya-jawab dokumen internal perusahaan dengan akurasi 99% tanpa halusinasi."},
                    {"title": "Predictive Analytics Systems", "desc": "Model machine learning untuk peramalan permintaan pasar dan pencegahan churn."},
                    {"title": "AI Computer Vision Solutions", "desc": "Otomasi inspeksi visual dan deteksi anomali pada lini produksi industri."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Audit Kebutuhan & Data Assessment", "desc": "Menganalisis kesiapan data, keamanan, dan target KPI efisiensi bisnis."},
                    {"step": 2, "title": "Desain Arsitektur & Prototyping", "desc": "Merancang pipeline model AI, schema database, dan integrasi API."},
                    {"step": 3, "title": "Training & Fine-Tuning Model", "desc": "Optimasi bobot model dan penerapan sistem RAG pada data perusahaan."},
                    {"step": 4, "title": "Pengujian Akurasi & Latensi", "desc": "Benchmarking evaluasi, stress testing, dan verifikasi keamanan data."},
                    {"step": 5, "title": "Deployment & Pemeliharaan", "desc": "Peluncuran sistem ke infrastruktur cloud dengan monitoring performa 24/7."}
                ],
                "base_tags": [
                    "ai apps production terpercaya", "jasa pembuatan aplikasi ai jakarta", "software house ai indonesia",
                    "pengembangan sistem rag enterprise", "konsultan machine learning", "vendor ai yogyakarta", "arsitektur ai cloud"
                ]
            }
        ],
        "locations": [
            {
                "id": "segia-id",
                "region_name": "Indonesia",
                "sub_cities": ["Jakarta", "Surabaya", "Bandung", "Semarang", "Yogyakarta", "Medan", "Bali", "Tangerang"],
                "local_context_notes": "Sebutkan ekosistem startup Jakarta, sentra industri Surabaya, dan kebutuhan transformasi digital korporat Indonesia.",
                "location_tags": ["software house jakarta", "jasa ai surabaya", "developer ai bandung", "software house yogyakarta", "solusi digital indonesia"]
            }
        ]
    },
    # 7 Additional Brands to complete the 10-Brand Portfolio
    {
        "id": "archivis",
        "name": "ARCHIVIS 3D",
        "slug": "archivis-3d",
        "platform": "WORDPRESS",
        "domain_url": "https://archivis.com",
        "wp_endpoint_url": "https://archivis.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Architectural elegance, hyperrealistic materials, investor-ready visualization.",
        "core_value_pillars": json.dumps([
            {"title": "Photorealistic Material Accuracy", "desc": "Accurate solar studies, physically based shaders, and real-world scale."},
            {"title": "Pre-Sale Commercial Impact", "desc": "Cinematic visual assets that accelerate off-the-plan property sales."}
        ]),
        "revision_guarantee": "Free 2x architectural revision guarantee",
        "master_output_spec": "Ultra-high resolution 8K renders and 4K video walkthroughs",
        "cta_tagline": "🎥 Showcase your architectural masterplan with ARCHIVIS 3D.",
        "services": [
            {
                "id": "archivis-render",
                "name": "3D Architectural Visualization",
                "pillar_url": "https://archivis.com/services/architectural-rendering",
                "anchor_variations": ["3D architectural visualization", "3D architectural render", "real estate 3D walkthrough", "property development rendering"],
                "technical_pipeline": ["BIM import", "Unreal Engine 5 lumen", "photoreal vegetation", "compositing"],
                "target_personas": ["Property Developers", "Lead Architects", "Real Estate Marketing Directors"],
                "target_industries": ["Luxury Residential", "Commercial Towers", "Hospitality Resorts", "Urban Masterplans"],
                "sub_solutions": [
                    {"title": "Exterior Masterplan Renders", "desc": "Dramatic daylight and twilight perspectives showcasing structural elegance."},
                    {"title": "Cinematic Interior Walkthroughs", "desc": "Smooth 60fps walkthroughs showing finishes, lighting, and spatial flow."},
                    {"title": "Interactive Real-Time VR", "desc": "Prospective buyers can explore unbuilt luxury residences in real time."},
                    {"title": "Solar & Shadow Studies", "desc": "Accurate seasonal sunlight animations for regulatory compliance."}
                ],
                "production_steps": [
                    {"step": 1, "title": "CAD & BIM Ingestion", "desc": "Translating architectural blueprints into optimized 3D geometry."},
                    {"step": 2, "title": "Lighting & Atmosphere Setup", "desc": "Configuring geographical sun coordinates and environmental lighting."},
                    {"step": 3, "title": "Bespoke Materiality & Interior Styling", "desc": "Texturing marble, timber, glass, and curated designer furniture."},
                    {"step": 4, "title": "Camera Choreography & Rendering", "desc": "Rendering 4K paths with cinematic framing and depth of field."},
                    {"step": 5, "title": "Final Color Grading & Delivery", "desc": "Color correction matching print brochure and digital campaign specs."}
                ],
                "base_tags": [
                    "3d architectural visualization", "architectural rendering studio", "property 3d walkthrough",
                    "real estate cgi australia", "3d render yogyakarta", "unbuilt property marketing", "exterior 3d render"
                ]
            }
        ],
        "locations": [
            {
                "id": "archivis-aus",
                "region_name": "Australia",
                "sub_cities": ["Sydney", "Melbourne", "Gold Coast", "Brisbane", "Perth"],
                "local_context_notes": "Mention luxury high-rise developments in Sydney CBD, Melbourne Southbank, and Gold Coast beachfront towers.",
                "location_tags": ["Sydney architectural rendering", "Melbourne 3D visualizer", "Brisbane property render", "Gold Coast CGI"]
            }
        ]
    },
    {
        "id": "safetymotion",
        "name": "SafetyMotion Studio",
        "slug": "safetymotion",
        "platform": "WORDPRESS",
        "domain_url": "https://safetymotion.com",
        "wp_endpoint_url": "https://safetymotion.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Rigorous, safety-compliant, life-saving visual clarity for industrial and energy sectors.",
        "core_value_pillars": json.dumps([
            {"title": "Hazard Clarity Without Compromise", "desc": "Every animation undergoes safety compliance scrutiny to prevent worksite accidents."},
            {"title": "High-Impact Remote Production", "desc": "Quick deployment from Yogyakarta to global industrial sites."}
        ]),
        "revision_guarantee": "Free 2x safety compliance revisions",
        "master_output_spec": "4K MP4 and SCORM 1.2/2004 LMS packages",
        "cta_tagline": "🎥 Protect your workforce with precision 3D safety animations.",
        "services": [
            {
                "id": "safetymotion-mining",
                "name": "Mining HSE Induction Video",
                "pillar_url": "https://safetymotion.com/services/mining-hse",
                "anchor_variations": ["mining HSE induction video", "mine site safety animation", "3D mining hazard training"],
                "technical_pipeline": ["mine site recreation", "heavy vehicle physics", "gas dispersion FX", "SCORM export"],
                "target_personas": ["Mining Site Managers", "HSE Officers", "Training Directors"],
                "target_industries": ["Open-Cut Mining", "Underground Mining", "Mineral Processing", "Smelting"],
                "sub_solutions": [
                    {"title": "Haul Truck Blind Spot Animations", "desc": "Visualizing exact operator blind spots to eradicate light vehicle collisions."},
                    {"title": "Underground Ventilation Protocols", "desc": "Simulating airflow, hazardous gas dispersion, and refuge chamber procedures."},
                    {"title": "Blasting Exclusion Zones", "desc": "3D aerial animations establishing blast radius protocols and warning signals."},
                    {"title": "Contractor Rapid Inductions", "desc": "Modular 5-minute animated modules that reduce contractor onboarding delays."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Safety SOP Audit", "desc": "Reviewing site safety documentation and incident prevention data."},
                    {"step": 2, "title": "Scripting & Hazard Mapping", "desc": "Pinpointing high-risk scenarios and lifesaving golden rules."},
                    {"step": 3, "title": "Rigorous 3D Modeling", "desc": "Building accurate rigs for heavy excavators, dump trucks, and conveyors."},
                    {"step": 4, "title": "Simulation & Voiceover", "desc": "Native English voiceover and dynamic on-screen hazard callouts."},
                    {"step": 5, "title": "LMS Export & Verification", "desc": "Testing SCORM packages across enterprise LMS platforms."}
                ],
                "base_tags": [
                    "mining hse induction video", "mine site safety animation", "underground mining 3d video",
                    "safe work australia mining video", "open cut mine safety animation", "contractor safety training cgi"
                ]
            }
        ],
        "locations": [
            {
                "id": "safetymotion-aus",
                "region_name": "Australia",
                "sub_cities": ["Perth", "Kalgoorlie", "Mackay", "Newcastle", "Mount Isa"],
                "local_context_notes": "Highlight Western Australia Pilbara iron ore operations, Queensland Bowen Basin coal, and Hunter Valley operations.",
                "location_tags": ["Perth mining video", "Pilbara safety induction", "Mackay mining animation", "Queensland mine safety"]
            }
        ]
    },
    {
        "id": "motioncraft",
        "name": "MotionCraft Studio",
        "slug": "motioncraft",
        "platform": "WORDPRESS",
        "domain_url": "https://motioncraft.com",
        "wp_endpoint_url": "https://motioncraft.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Energetic, cutting-edge motion graphics, bold typography, and visual momentum.",
        "core_value_pillars": json.dumps([
            {"title": "Visual Rhythm & Impact", "desc": "Seamless transitions and kinetic typography that hold viewer attention."},
            {"title": "Multi-Format Agility", "desc": "One master motion language adapted across all digital touchpoints."}
        ]),
        "revision_guarantee": "Free 2x creative revision guarantee",
        "master_output_spec": "ProRes 4444 and optimized web formats",
        "cta_tagline": "🎥 Ignite your brand story with MotionCraft Studio.",
        "services": [
            {
                "id": "motioncraft-saas",
                "name": "SaaS Product Demo Video",
                "pillar_url": "https://motioncraft.com/services/saas-demo-video",
                "anchor_variations": ["SaaS product demo video", "software explainer animation", "UI motion design studio"],
                "technical_pipeline": ["UI vector animation", "kinetic typography", "isometric illustration", "sound design"],
                "target_personas": ["SaaS Founders", "Growth Marketing Leads", "Product Marketing Managers"],
                "target_industries": ["B2B SaaS", "Fintech", "Cybersecurity", "HealthTech"],
                "sub_solutions": [
                    {"title": "Hero Website Explainers", "desc": "High-conversion 60-second animated videos for landing page hero sections."},
                    {"title": "Feature Deep-Dives", "desc": "Highlighting complex software workflows in digestible 30-second clips."},
                    {"title": "Product Launch Teasers", "desc": "Fast-paced kinetic teasers engineered for LinkedIn and X campaigns."},
                    {"title": "Onboarding Walkthroughs", "desc": "Clear animated guides that reduce user churn during trial phases."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Value Proposition Workshop", "desc": "Distilling complex software features into 3 core customer benefits."},
                    {"step": 2, "title": "Scripting & Visual Metaphors", "desc": "Crafting engaging analogies that explain data flows and integrations."},
                    {"step": 3, "title": "UI Styling & Motion Design", "desc": "Elevating real software interfaces with stylized isometric animation."},
                    {"step": 4, "title": "Sound Design & VO", "desc": "Matching energetic voiceover with crisp UI click foley and synth music."},
                    {"step": 5, "title": "Multi-Platform Export", "desc": "Delivering 16:9, 9:16 vertical, and looping GIF/Lottie assets."}
                ],
                "base_tags": [
                    "saas product demo video", "software explainer animation", "b2b saas video production",
                    "tech startup explainer video", "ui motion graphics studio", "animated app walkthrough"
                ]
            }
        ],
        "locations": [
            {
                "id": "motioncraft-us",
                "region_name": "United States",
                "sub_cities": ["San Francisco", "New York", "Austin", "Seattle", "Boston"],
                "local_context_notes": "Highlight Silicon Valley tech standards, Austin startup culture, and enterprise B2B expectations.",
                "location_tags": ["San Francisco SaaS video", "Austin tech explainer", "New York software animation", "US SaaS motion design"]
            }
        ]
    },
    {
        "id": "lumenspace",
        "name": "LumenSpace Immersive",
        "slug": "lumenspace",
        "platform": "WORDPRESS",
        "domain_url": "https://lumenspace.id",
        "wp_endpoint_url": "https://lumenspace.id/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "id",
        "brand_voice": "Magis, imersif, memadukan seni media baru dengan kearifan visual modern.",
        "core_value_pillars": json.dumps([
            {"title": "Eksplorasi Ruang & Sensorik", "desc": "Menciptakan instalasi seni interaktif di mana pengunjung menjadi bagian dari karya visual."},
            {"title": "Teknologi Sensor & Proyeksi Tanpa Batas", "desc": "Integrasi lidar sensor, kinect, dan proyektor resolusi tinggi."}
        ]),
        "revision_guarantee": "Garansi 2x revisi visual interaktif",
        "master_output_spec": "Master visual 360 uncompressed dan source code interaktif",
        "cta_tagline": "🎥 Ciptakan pengalaman magis di ruang Anda bersama LumenSpace.",
        "services": [
            {
                "id": "lumen-museum",
                "name": "Jasa Instalasi Museum Imersif",
                "pillar_url": "https://lumenspace.id/layanan/museum-imersif",
                "anchor_variations": ["jasa museum imersif", "instalasi seni interaktif", "ruang proyeksi 360 indonesia"],
                "technical_pipeline": ["360 dome projection", "touch sensor lidar", "interactive touch wall", "spatial audio"],
                "target_personas": ["Kurator Museum", "Pengelola Galeri Seni", "Direktur Taman Wisata", "Brand Experience Designer"],
                "target_industries": ["Museum & Cagar Budaya", "Galeri Seni Kontemporer", "Taman Hiburan Digital", "Mall & Exhibition Atrium"],
                "sub_solutions": [
                    {"title": "Ruang Sejarah Imersif 360", "desc": "Membawa pengunjung melintasi lorong waktu dengan animasi proyeksi dinding dan lantai serentak."},
                    {"title": "Dinding Interaktif Sentuh", "desc": "Karya visual yang merespons sentuhan tangan pengunjung menggunakan sensor presisi tinggi."},
                    {"title": "Dome Projection Planetarium", "desc": "Pengalaman sinematik kubah langit dengan visual galaksi dan alam semesta."},
                    {"title": "Interactive Floor Games", "desc": "Lantai proyeksi interaktif yang merespons langkah kaki untuk edukasi anak dan keluarga."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Studi Kuratorial & Akustik Ruang", "desc": "Menyelaraskan tema cerita dengan kondisi fisik ruang pameran."},
                    {"step": 2, "title": "Perancangan Sensor & Hardware", "desc": "Penempatan proyektor ultra-short throw, cermin, dan sensor lidar."},
                    {"step": 3, "title": "Produksi Animasi 360 Derajat", "desc": "Pembuatan konten visual tanpa jahitan (seamless stitch) resolusi 8K."},
                    {"step": 4, "title": "Pemrograman Interaksi Software", "desc": "Integrasi engine visual dengan sensor interaktif real-time."},
                    {"step": 5, "title": "Pemasangan & Commissioning", "desc": "Instalasi perangkat di lokasi, pengujian ketahanan hardware 24/7."}
                ],
                "base_tags": [
                    "jasa museum imersif indonesia", "vendor instalasi seni interaktif", "ruang proyeksi 360 derajat",
                    "interactive wall museum", "konten digital museum jakarta", "jasa pameran interaktif yogyakarta"
                ]
            }
        ],
        "locations": [
            {
                "id": "lumen-id",
                "region_name": "Indonesia",
                "sub_cities": ["Jakarta", "Yogyakarta", "Bali", "Surabaya", "Bandung", "Solo"],
                "local_context_notes": "Sebutkan pengembangan museum digital, galeri seni budaya, dan destinasi wisata edukasi.",
                "location_tags": ["museum imersif jakarta", "instalasi interaktif bali", "seni digital yogyakarta", "galeri seni bandung"]
            }
        ]
    },
    {
        "id": "brandvibe",
        "name": "BrandVibe Studio",
        "slug": "brandvibe",
        "platform": "WORDPRESS",
        "domain_url": "https://brandvibe.com.au",
        "wp_endpoint_url": "https://brandvibe.com.au/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Authentic, human-centric, inspiring employer brand visual narratives.",
        "core_value_pillars": json.dumps([
            {"title": "Authentic Cultural Resonance", "desc": "Showcasing real workplace values that attract tier-1 talent."},
            {"title": "Cinematic Storytelling", "desc": "Treating corporate culture with the visual fidelity of documentary cinema."}
        ]),
        "revision_guarantee": "Free 2x editorial revision guarantee",
        "master_output_spec": "4K ProRes masters and multi-channel social cutdowns",
        "cta_tagline": "🎥 Inspire top-tier talent with BrandVibe Studio.",
        "services": [
            {
                "id": "brandvibe-eb",
                "name": "Employer Branding Video",
                "pillar_url": "https://brandvibe.com.au/services/employer-branding",
                "anchor_variations": ["employer branding video", "corporate culture video production", "talent recruitment video studio"],
                "technical_pipeline": ["documentary cinematography", "remote animation hybrid", "employee interview editing", "color grading"],
                "target_personas": ["CHROs", "Chief People Officers", "Talent Acquisition Directors", "Head of Culture"],
                "target_industries": ["Technology & Scaleups", "Financial Services", "Healthcare Systems", "Renewable Energy"],
                "sub_solutions": [
                    {"title": "Day-In-The-Life Documentaries", "desc": "Authentic cinematic profiles of team members showcasing autonomy and growth."},
                    {"title": "Values & Mission Manifestos", "desc": "High-energy brand films communicating the organizational 'why'."},
                    {"title": "Executive Leadership Spotlights", "desc": "Warm, candid leadership conversations outlining company vision."},
                    {"title": "Graduate & Internship Campaigns", "desc": "Vibrant visual campaigns targeted at university graduates across social channels."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Culture & EVP Audit", "desc": "Distilling your Employee Value Proposition into relatable visual themes."},
                    {"step": 2, "title": "Storyboarding & Talent Casting", "desc": "Identifying inspiring internal champions and mapping interview arcs."},
                    {"step": 3, "title": "Remote/Hybrid Cinematography", "desc": "Combining localized footage with bespoke 3D/motion graphics from Yogyakarta."},
                    {"step": 4, "title": "Pacing & Emotional Editing", "desc": "Dynamic cutting paired with evocative acoustic and modern soundtracks."},
                    {"step": 5, "title": "Campaign Rollout Pack", "desc": "Master film plus 6 vertical cutdowns for LinkedIn, Instagram, and careers pages."}
                ],
                "base_tags": [
                    "employer branding video australia", "talent acquisition video production", "corporate culture film",
                    "recruitment marketing video sydney", "company culture video melbourne", "hybrid video production yogyakarta"
                ]
            }
        ],
        "locations": [
            {
                "id": "brandvibe-aus",
                "region_name": "Australia",
                "sub_cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Canberra"],
                "local_context_notes": "Focus on competitive tech hiring in Sydney/Melbourne, hybrid work culture, and diversity initiatives.",
                "location_tags": ["Sydney employer branding video", "Melbourne recruitment video", "Brisbane corporate culture", "Australia EVP film"]
            }
        ]
    },
    {
        "id": "cloudshift",
        "name": "CloudShift Digital",
        "slug": "cloudshift",
        "platform": "WORDPRESS",
        "domain_url": "https://cloudshift.id",
        "wp_endpoint_url": "https://cloudshift.id/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Jakarta - Yogyakarta, Indonesia",
        "default_language": "id",
        "brand_voice": "Handal, efisien, berstandar arsitektur cloud enterprise dengan SLA 99.99%.",
        "core_value_pillars": json.dumps([
            {"title": "Arsitektur Cloud Andal & Bebas Downtime", "desc": "Modernisasi infrastruktur legacy ke ekosistem cloud otomatis."},
            {"title": "Optimalisasi Biaya Komputasi", "desc": "Mengurangi pemborosan biaya server cloud hingga 40%."}
        ]),
        "revision_guarantee": "Garansi pendampingan migrasi tanpa downtime",
        "master_output_spec": "Infrastruktur Terraform, pipeline CI/CD, dan SLA operasional",
        "cta_tagline": "🎥 Percepat transformasi cloud enterprise Anda bersama CloudShift Digital.",
        "services": [
            {
                "id": "cloudshift-migrasi",
                "name": "Jasa Migrasi Cloud Enterprise",
                "pillar_url": "https://cloudshift.id/layanan/migrasi-cloud",
                "anchor_variations": ["jasa migrasi cloud enterprise", "konsultan cloud jakarta", "modernisasi infrastruktur aws gcp"],
                "technical_pipeline": ["Kubernetes containerization", "Terraform IaC", "zero-downtime database migration", "FinOps optimization"],
                "target_personas": ["VP of Engineering", "Head of IT Infrastructure", "Chief Information Officer"],
                "target_industries": ["Perbankan & Fintech", "E-Commerce Nasional", "Manufaktur", "Institusi Pendidikan"],
                "sub_solutions": [
                    {"title": "Migrasi Server Legacy ke Cloud", "desc": "Pemindahan sistem on-premise ke AWS, GCP, atau Azure tanpa gangguan layanan."},
                    {"title": "Kubernetes & Containerization", "desc": "Otomasi deployment dan auto-scaling aplikasi dengan cluster Kubernetes."},
                    {"title": "FinOps Cloud Cost Optimization", "desc": "Audit dan eliminasi beban komputasi berlebih untuk efisiensi biaya bulanan."},
                    {"title": "Disaster Recovery & Multi-Cloud", "desc": "Penerapan sistem backup lintas region untuk ketahanan bisnis mutlak."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Audit Infrastruktur & Pemetaan Dependensi", "desc": "Menilai beban kerja server dan skema database yang ada."},
                    {"step": 2, "title": "Perancangan Arsitektur Target", "desc": "Membuat blueprint Infrastructure as Code (IaC) dan simulasi failover."},
                    {"step": 3, "title": "Uji Coba Replikasi Data Staging", "desc": "Sinkronisasi data real-time pada lingkungan staging terisolasi."},
                    {"step": 4, "title": "Eksekusi Cutover Zero-Downtime", "desc": "Pengalihan traffic DNS pada jam operasional rendah dengan rollback plan."},
                    {"step": 5, "title": "Monitoring & Optimalisasi FinOps", "desc": "Pemantauan performa 24/7 dan optimalisasi alokasi resource komputasi."}
                ],
                "base_tags": [
                    "jasa migrasi cloud enterprise", "konsultan cloud jakarta", "migrasi aws tanpa downtime",
                    "jasa setup kubernetes", "finops cloud indonesia", "arsitektur multi cloud surabaya", "devops cloud yogyakarta"
                ]
            }
        ],
        "locations": [
            {
                "id": "cloudshift-id",
                "region_name": "Indonesia",
                "sub_cities": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Yogyakarta"],
                "local_context_notes": "Sebutkan kebutuhan regulasi data di Indonesia (data sovereignty), perbankan OJK, dan pusat data tier-3.",
                "location_tags": ["konsultan cloud jakarta", "cloud architect surabaya", "jasa devops bandung", "infrastruktur cloud indonesia"]
            }
        ]
    },
    {
        "id": "renderpulse",
        "name": "RenderPulse Labs",
        "slug": "renderpulse",
        "platform": "WORDPRESS",
        "domain_url": "https://renderpulse.com",
        "wp_endpoint_url": "https://renderpulse.com/wp-json/seo-engine/v1/publish",
        "api_secret_key": "unicam-geo-secret-key-2026",
        "hq_location": "Yogyakarta, Indonesia",
        "default_language": "en",
        "brand_voice": "Scientifically rigorous, visually mesmerizing biomedical and anatomical 3D visualization.",
        "core_value_pillars": json.dumps([
            {"title": "Medical Scientific Accuracy", "desc": "Verified by life science consultants for pharmaceutical MoA and medical device FDA clarity."},
            {"title": "Microscopic Photorealism", "desc": "Subsurface cellular scattering and molecular dynamics rendered in pristine 4K."}
        ]),
        "revision_guarantee": "Free 2x scientific accuracy revision guarantee",
        "master_output_spec": "4K ProRes masters and interactive 3D WebGL assets",
        "cta_tagline": "🎥 Bring life sciences to light with RenderPulse Labs.",
        "services": [
            {
                "id": "renderpulse-moa",
                "name": "Mechanism of Action (MoA) Animation",
                "pillar_url": "https://renderpulse.com/services/moa-animation",
                "anchor_variations": ["Mechanism of Action animation", "medical 3D animation studio", "biotech MoA video production"],
                "technical_pipeline": ["PDB molecular modeling", "cellular dynamics simulation", "subsurface scattering", "scientific narrative"],
                "target_personas": ["Biotech Founders", "Medical Directors", "Pharmaceutical Brand Leads", "Clinical Stage IR Leads"],
                "target_industries": ["Biopharmaceuticals", "Gene & Cell Therapy", "Medical Robotics", "Oncology Research"],
                "sub_solutions": [
                    {"title": "Cellular Receptor MoA Films", "desc": "Visualizing exact ligand-receptor binding and downstream signaling cascades."},
                    {"title": "Medical Device Surgical Walkthroughs", "desc": "Step-by-step 3D demonstration of minimally invasive surgical implants."},
                    {"title": "Investor Pitch Deck Visuals", "desc": "Condensing complex clinical trial science into engaging 90-second animations for venture capital."},
                    {"title": "Interactive 3D Molecular Viewers", "desc": "Real-time web-based protein explorations for medical congress presentations."}
                ],
                "production_steps": [
                    {"step": 1, "title": "Scientific Paper Ingestion", "desc": "Translating peer-reviewed clinical research and PDB data into visual milestones."},
                    {"step": 2, "title": "Medical Storyboarding & Scientific Review", "desc": "Mapping cellular structures and biological accuracy with client medical teams."},
                    {"step": 3, "title": "High-End Molecular CGI Production", "desc": "Simulating protein folding, membrane interactions, and physiological environments."},
                    {"step": 4, "title": "Cinematic Lighting & Microscopic Compositing", "desc": "Applying electron microscope depth-of-field and scientific labeling."},
                    {"step": 5, "title": "Congress & Regulatory Delivery", "desc": "Final broadcast-ready delivery formatted for medical conferences and investor presentations."}
                ],
                "base_tags": [
                    "mechanism of action animation", "medical 3d animation studio", "biotech visual production",
                    "pharma moa video australia", "scientific animation yogyakarta", "medical device cgi video"
                ]
            }
        ],
        "locations": [
            {
                "id": "renderpulse-us",
                "region_name": "United States",
                "sub_cities": ["Boston", "San Francisco", "San Diego", "Philadelphia", "New York"],
                "local_context_notes": "Highlight biotech hubs in Cambridge/Boston, South San Francisco life sciences clusters, and JP Morgan Healthcare conference standards.",
                "location_tags": ["Boston biotech animation", "San Francisco medical CGI", "San Diego life sciences video", "US medical animation studio"]
            }
        ]
    }
]

def seed_database():
    """Initializes and populates database with 10 brands, services, and location matrices."""
    init_db()
    db = SessionLocal()
    try:
        existing_count = db.query(Brand).count()
        if existing_count >= 10:
            logger.info(f"[Seed] Database already has {existing_count} brands. Skipping seed.")
            return

        logger.info(f"[Seed] Seeding {len(SEED_BRANDS)} complete brand ecosystems...")
        for b_data in SEED_BRANDS:
            brand = db.query(Brand).filter(Brand.id == b_data["id"]).first()
            if not brand:
                brand = Brand(
                    id=b_data["id"],
                    name=b_data["name"],
                    slug=b_data["slug"],
                    platform=b_data.get("platform", "WORDPRESS"),
                    domain_url=b_data["domain_url"],
                    wp_endpoint_url=b_data.get("wp_endpoint_url"),
                    api_secret_key=b_data.get("api_secret_key", "unicam-geo-secret-key-2026"),
                    hq_location=b_data.get("hq_location", "Yogyakarta, Indonesia"),
                    default_language=b_data.get("default_language", "en"),
                    brand_voice=b_data.get("brand_voice"),
                    core_value_pillars=b_data.get("core_value_pillars", "[]"),
                    revision_guarantee=b_data.get("revision_guarantee", "Free 2x revision guarantee"),
                    master_output_spec=b_data.get("master_output_spec", "Uncompressed 4K master files"),
                    cta_tagline=b_data.get("cta_tagline", "🎥 Elevate your visual content.")
                )
                db.add(brand)
                db.flush()

            # Seed Services
            for s_data in b_data.get("services", []):
                srv = db.query(Service).filter(Service.id == s_data["id"]).first()
                if not srv:
                    srv = Service(
                        id=s_data["id"],
                        brand_id=brand.id,
                        name=s_data["name"],
                        pillar_url=s_data["pillar_url"],
                        anchor_variations=json.dumps(s_data.get("anchor_variations", [])),
                        technical_pipeline=json.dumps(s_data.get("technical_pipeline", [])),
                        target_personas=json.dumps(s_data.get("target_personas", [])),
                        target_industries=json.dumps(s_data.get("target_industries", [])),
                        sub_solutions=json.dumps(s_data.get("sub_solutions", [])),
                        production_steps=json.dumps(s_data.get("production_steps", [])),
                        estimated_timeline=s_data.get("estimated_timeline", "2 to 5 weeks"),
                        deliverable_formats=json.dumps(s_data.get("deliverable_formats", [])),
                        base_tags=json.dumps(s_data.get("base_tags", []))
                    )
                    db.add(srv)

            # Seed Location Targets
            for l_data in b_data.get("locations", []):
                loc = db.query(LocationTarget).filter(LocationTarget.id == l_data["id"]).first()
                if not loc:
                    loc = LocationTarget(
                        id=l_data["id"],
                        brand_id=brand.id,
                        region_name=l_data["region_name"],
                        sub_cities=json.dumps(l_data.get("sub_cities", [])),
                        local_context_notes=l_data.get("local_context_notes", ""),
                        location_tags=json.dumps(l_data.get("location_tags", []))
                    )
                    db.add(loc)

            # Seed Sample Media Asset
            media = db.query(MediaAsset).filter(MediaAsset.id == f"{brand.id}-media-1").first()
            if not media:
                media = MediaAsset(
                    id=f"{brand.id}-media-1",
                    brand_id=brand.id,
                    service_id=b_data.get("services", [{}])[0].get("id") if b_data.get("services") else None,
                    file_url=f"https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1280&q=80",
                    role="FEATURED",
                    alt_text_template="{primary_keyword} - {brand_name}",
                    title_template="Professional {service_name} in {location} by {brand_name}",
                    caption_template="High-resolution visual production for {primary_keyword}."
                )
                db.add(media)

        db.commit()
        logger.info("[Seed] 10 Brand ecosystems seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"[Seed] Error seeding database: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
