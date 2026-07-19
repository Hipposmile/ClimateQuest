from __future__ import annotations

from typing import cast

from django.contrib.sitemaps import Sitemap
from django.utils import translation


class LanguagePrefixedSitemapMixin(Sitemap):
    i18n = True
    alternates = True
    x_default = True

    def location(self, item):
        original_location = super().location(item)
        return f"/{translation.get_language()}{original_location}"


def build_localized_sitemap_class(sitemap_class: type[Sitemap]) -> type[Sitemap]:
    """Erzeugt aus einer bestehenden Sitemap-Klasse eine sprachpräfigierte Variante."""
    localized_class = type(
        f"Localized{sitemap_class.__name__}",
        (LanguagePrefixedSitemapMixin, sitemap_class),
        {},
    )
    return cast("type[Sitemap]", localized_class)


def build_localized_sitemaps(sitemap_classes: dict[str, type[Sitemap]]) -> dict[str, Sitemap]:
    """Baut aus einem Mapping {name: SitemapClass} das fertige sitemaps-Dict für urls.py."""
    return {
        name: build_localized_sitemap_class(sitemap_class)()
        for name, sitemap_class in sitemap_classes.items()
    }