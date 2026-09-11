from django.db import models
from django_jsonform.models.fields import JSONField


class HomePage(models.Model):
    # seo
    title = models.CharField(max_length=255, default="Cholbe AI - AI powered customer service")
    meta_description = models.TextField(null=True, blank=True)
    meta_keywords = models.TextField(null=True, blank=True)
    extra_head = models.TextField(null=True, blank=True, help_text="Additional HTML to include in the <head> section of the page")

    # hero section
    hero_tag = models.CharField(max_length=255)
    hero_title = models.CharField(max_length=255)
    hero_subtitle = models.CharField(max_length=500)
    see_demo_url = models.CharField(default="#", max_length=255)

    #chat ui
    CONVERSATION_SCHEMA = {
        "type": "array",
        "title": "Conversation Flow",
        "items": {
            "oneOf": [
                # 1. Text Message Schema
                {
                    "title": "Text Message",
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "bot"], "default": "user"},
                        "type": {"type": "string", "enum": ["text"], "default": "text", "widget": "hidden"}, # Let enum act as standard validator
                        "content": {"type": "string", "widget": "textarea", "title": "Text Message"}, # Unique Key
                        "cooldown": {"type": "integer", "default": 1000}
                    },
                    "required": ["role", "type", "content", "cooldown"]
                },
                # 2. Products Schema
                {
                    "title": "Products Message",
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["bot"], "default": "bot"},
                        "type": {"type": "string", "enum": ["products"], "default": "products", "widget": "hidden"},
                        "content": { # Unique Key
                            "type": "array",
                            "title": "Products List",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "subtitle": {"type": "string"},
                                    "image": {"type": "string", "format": "uri"}
                                },
                                "required": ["title", "subtitle", "image"]
                            }
                        },
                        "cooldown": {"type": "integer", "default": 3000}
                    },
                    "required": ["role", "type", "content", "cooldown"]
                },
                # 3. Image Schema
                {
                    "title": "Image Message",
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "bot"], "default": "bot"},
                        "type": {"type": "string", "enum": ["image"], "default": "image", "widget": "hidden"},
                        "content": {"type": "string", "format": "uri", "title": "Image URL"}, # Unique Key
                        "cooldown": {"type": "integer", "default": 1500}
                    },
                    "required": ["role", "type", "content", "cooldown"]
                },
                # 4. Replies Schema
                {
                    "title": "Quick Replies",
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["bot"], "default": "bot"},
                        "type": {"type": "string", "enum": ["replies"], "default": "replies", "widget": "hidden"},
                        "content": { # Unique Key
                            "type": "array",
                            "title": "Reply Options",
                            "items": {"type": "string"}
                        },
                        "cooldown": {"type": "integer", "default": 1500}
                    },
                    "required": ["role", "type", "content", "cooldown"]
                },
                # 5. Receipt Schema
                {
                    "title": "Receipt Message",
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["bot"], "default": "bot"},
                        "type": {"type": "string", "enum": ["receipt"], "default": "receipt", "widget": "hidden"},
                        "content": {"type": "string", "widget": "textarea"}, # Unique Key
                        "cooldown": {"type": "integer", "default": 5000}
                    },
                    "required": ["role", "type", "content", "cooldown"]
                }
            ]
        }
    } 

    phone_chat = JSONField(schema=CONVERSATION_SCHEMA, default=list)

    #support
    support_whatsapp_number=models.CharField(null=True, blank=True, help_text="e.g. 8801xxxxxxx", max_length=100)

    # pricing
    pricing_title = models.CharField(max_length=255, default="Pricing")
    pricing_subtitle = models.CharField(max_length=500, default="We offer competitive pricing for your convenience")

    # brands
    BRANDS_SCHEMA = {
        "type": "array",
        "title": "Brands List",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "title": "Brand Name"},
                "logo": {"type": "string", "format": "uri", "title": "Brand Logo URL"},
                "url": {"type": "string", "format": "uri", "title": "Brand URL"}
            },
            "required": ["name", "logo"]
        }
    }
    brands_title = models.CharField(max_length=255, default="Trusted by leading brands")
    brands_subtitle = models.CharField(max_length=500, default="We work with the leading brands in Bangladesh")
    brands = JSONField(default=list, null=True, blank=True, schema=BRANDS_SCHEMA, help_text="List of brands with name and logo URL")

    # reviews section
    REVIEWS_SCHEMA = {
        "type": "array",
        "title": "Reviews List",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "title": "Reviewer Name"},
                "designation": {"type": "string", "title": "Reviewer Designation"},
                "photo": {"type": "string", "format": "uri", "title": "Reviewer Photo URL"},
                "rating": {"type": "number", "minimum": 0, "maximum": 5, "title": "Rating (0-5)"},
                "comment": {"type": "string", "widget": "textarea", "title": "Review Comment"}
            },
            "required": ["name", "designation", "photo", "rating", "comment"]
        }
    }
    reviews_title = models.CharField(max_length=255, default="What our customers say")
    reviews_subtitle = models.CharField(max_length=500, default="Customer reviews and testimonials")
    reviews = JSONField(default=list, schema=REVIEWS_SCHEMA, help_text="List of reviews with name, designation, photo URL, rating and comment")

    # FAQ section
    FAQ_SCHEMA = {
        "type": "array",
        "title": "FAQ List",
        "items": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "title": "FAQ Question"},
                "answer": {"type": "string", "widget": "textarea", "title": "FAQ Answer"}
            },
            "required": ["question", "answer"]
        }
    }
    faq_title = models.CharField(max_length=255, default="Frequently Asked Questions")
    faqs = JSONField(default=list, schema=FAQ_SCHEMA, help_text="List of frequently asked questions with question and answer")

    # footer
    footer_text = models.CharField(max_length=255)
    SOCIAL_LINKS_SCHEMA = {
        "type": "array",
        "title": "Social Links",
        "items": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "title": "Social Media Platform"},
                "icon": {"type": "string", "title": "SVG Icon"},
                "url": {"type": "string", "format": "uri", "title": "Profile URL"}
            },
            "required": ["platform", "icon", "url"]
        }
    }
    social_links = JSONField(default=list, schema=SOCIAL_LINKS_SCHEMA)
    # link groups -> list of links with group name and list of links (name and url)
    LINKS_SCHEMA = {
        "type": "array",
        "title": "Footer Link Groups",
        "items": {
            "type": "object",
            "properties": {
                "group_name": {"type": "string", "title": "Link Group Name"},
                "links": {
                    "type": "array",
                    "title": "Links in Group",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "title": "Link Name"},
                            "url": {"type": "string", "format": "uri", "title": "Link URL"}
                        },
                        "required": ["name", "url"]
                    }
                }
            },
            "required": ["group_name", "links"]
        }
    }
    link_groups = JSONField(default=list, schema=LINKS_SCHEMA)


    def __str__(self):
        return "Home Page Content"
    
class HomePageSection(models.Model):
    homepage = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="sections", default=1)
    html = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]