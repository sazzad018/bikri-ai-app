
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "Cholbe AI",
    "SITE_HEADER": "Cholbe AI",
    "SITE_SUBHEADER": "Social media automation",
    "SITE_DROPDOWN": [
        {
            "icon": "home",
            "title": _("Visit homepage"),
            "link": "/",
        },
        {
            "icon": "info",
            "title": _("About us"),
            "link": "/i/about/",
        },
        {
            "icon": "phone",
            "title": _("Contact"),
            "link": "/i/contact/",
        },
        {
            "icon": "policy",
            "title": _("Privacy Policy"),
            "link": "/i/privacy-policy/",
        },
        {
            "icon": "gavel",
            "title": _("Terms of Service"),
            "link": "/i/terms-of-service/",
        },
        {
            "icon": "paid",
            "title": _("Refund Policy"),
            "link": "/i/refund-policy/",
        },
        # ...
    ],
    # "SITE_URL": "/",
    "SITE_ICON": lambda request: static("img/logo_icon.svg"),  # both modes, optimise for 32px height
    "SITE_LOGO": lambda request: static("img/logo.svg"),  # both modes, optimise for 32px height
    "SITE_SYMBOL": "speed",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("img/logo_icon.svg"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    # "ENVIRONMENT": "sample_app.environment_callback", # environment name in header
    # "ENVIRONMENT_TITLE_PREFIX": "sample_app.environment_title_prefix_callback", # environment name prefix in title tag
    "DASHBOARD_CALLBACK": "apps.core.views.dashboard_callback",
    "THEME": "light", # Force theme: "dark" or "light". Will disable theme switcher
    "STYLES": [
        lambda request: static("css/build.css"),
    ],
    # "SCRIPTS": [
    #     lambda request: static("js/script.js"),
    # ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
        },
        "primary": {
            "50": "hsl(25, 99%, 90%)",
            "100": "hsl(25, 99%, 85%)",
            "200": "hsl(25, 99%, 75%)",
            "300": "hsl(25, 99%, 65%)",
            "400": "hsl(25, 99%, 55%)",
            "500": "hsl(25, 99%, 50%)",
            "600": "hsl(25, 99%, 45%)",
            "700": "hsl(25, 99%, 35%)",
            "800": "hsl(25, 99%, 25%)",
            "900": "hsl(25, 99%, 15%)",
            "950": "hsl(25, 99%, 10%)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "command_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                    {
                        "title": _("Credit"),
                        "separator": True,
                        "icon": "add_card",
                        "link": reverse_lazy("credit:buy_credit"),
                    },
                ]
            },
            {
                "separator": True,
                "items": [
                    {
                        "title": _("Business Profiles"),
                        "icon": "business_center",
                        "link": reverse_lazy("admin:business_profile_businessprofile_changelist"),
                    },
                    {
                        "title": _("Conversations"),
                        "icon": "forum",
                        "link": reverse_lazy("admin:business_profile_conversation_changelist"),
                    },
                    {
                        "title": _("Products"),
                        "icon": "package_2",
                        "link": reverse_lazy("admin:business_profile_product_changelist"),
                    },
                    {
                        "title": _("Media Files"),
                        "icon": "perm_media",
                        "link": reverse_lazy("admin:business_profile_mediafiles_changelist"),
                    },
                    {
                        "title": _("Comment Presets"),
                        "icon": "rate_review",
                        "link": reverse_lazy("admin:business_profile_commentpreset_changelist"),
                    },
                    {
                        "title": _("Comment Logs"),
                        "icon": "list",
                        "link": reverse_lazy("admin:business_profile_commentlog_changelist"),
                    },
                    {
                        "title": _("WhatsApp Templates"),
                        "icon": "view_timeline",
                        "link": reverse_lazy("admin:business_profile_whatsapptemplate_changelist"),
                    },
                    {
                        "title": _("Orders"),
                        "icon": "receipt_long",
                        "link": reverse_lazy("admin:business_profile_order_changelist"),
                        "badge": "new",
                        "badge_variant": "primary",
                        "badge_style": "solid",
                    },
                ],
            },
            {
                "title": _("Administration"),
                "separator": True,
                "permission": False,
                "items": [
                    {
                        "title": _("Site Configuration"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:core_siteconfig_change", args=(1,)),  # core/siteconfig model changeform  pk=1
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": "Info Pages",
                        "icon": "info",
                        "link": reverse_lazy("admin:core_infopage_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Home Page"),
                        "icon": "home",
                        "link": reverse_lazy("admin:core_homepage_change", args=(1,)),  # core/homepage model changeform  pk=1
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Popups"),
                        "icon": "web_asset",
                        "link": reverse_lazy("admin:core_popup_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Files Storage"),
                        "icon": "folder",
                        "link": reverse_lazy("admin:core_galleryitem_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Users"),
                        "icon": "people",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Email Addresses"),
                        "icon": "email",
                        "link": reverse_lazy("admin:account_emailaddress_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Payment Attempts"),
                        "icon": "payment",
                        "link": reverse_lazy("admin:credit_paymentattempt_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    {
                        "title": _("Credit Transactions"),
                        "icon": "account_balance_wallet",
                        "link": reverse_lazy("admin:credit_credittransaction_changelist"),
                        "permission": lambda request: request.user.is_superuser,
                    }


                ],
            },
        ],
    },
}




def environment_callback(request):
    """
    Callback has to return a list of two values represeting text value and the color
    type of the label displayed in top right corner.
    """
    return ["Production", "danger"] # info, danger, warning, success


def badge_callback(request):
    return 3

def permission_callback(request):
    return request.user.has_perm("sample_app.change_model")