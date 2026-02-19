from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.infrastructure.scraping.parsers.product_parser import ProductPageData, parse_product_page


def test_parse_product_page_extracts_notes_description_tags_and_images() -> None:
    html = """
    <html>
      <head>
        <meta name="description" content="A warm floral profile with elegant depth." />
      </head>
      <body>
        <div>Top Notes: Bergamot, Pink Pepper</div>
        <div>Heart Notes: Rose und Jasmine</div>
        <div>Base Notes: Vanilla; Musk</div>
        <div>Duftfamilie: Blumig, Frisch</div>
        <div>Geschlecht: Unisex</div>
        <div>Moleküle: Iso E Super</div>
        <img src="/images/amber-1.jpg" />
        <img data-src="https://cdn.example.com/amber-2.jpg" />
      </body>
    </html>
    """

    parsed = parse_product_page(html, "https://vicioso.example")

    assert parsed == ProductPageData(
        description="A warm floral profile with elegant depth.",
        notes_top=("Bergamot", "Pink Pepper"),
        notes_middle=("Rose", "Jasmine"),
        notes_base=("Vanilla", "Musk"),
        gender_tags=("Unisex",),
        scent_families=("Floral", "Fresh"),
        molecule_tags=("Iso E Super",),
        image_urls=(
            "https://vicioso.example/images/amber-1.jpg",
            "https://cdn.example.com/amber-2.jpg",
        ),
    )


def test_parse_product_page_uses_fallback_text_lines_and_attribute_tags() -> None:
    html = """
    <html>
      <body>
        <h3>Top Notes</h3>
        <ul><li>Lemon</li><li>Bergamot</li></ul>
        <h3>Middle Notes</h3>
        <ul><li>Rose</li></ul>
        <h3>Base Notes</h3>
        <ul><li>Cedar</li><li>Musk</li></ul>
        <div>This fragrance is made for elegant evening wear and long-lasting comfort.</div>
        <span data-family="Holzig"></span>
        <span data-family="Frisch"></span>
      </body>
    </html>
    """

    parsed = parse_product_page(html, "https://vicioso.example")

    assert parsed.notes_top == ("Lemon", "Bergamot")
    assert parsed.notes_middle == ("Rose",)
    assert parsed.notes_base == ("Cedar", "Musk")
    assert parsed.scent_families == ("Woody", "Fresh")
    assert parsed.description == "This fragrance is made for elegant evening wear and long-lasting comfort."


def test_parse_product_page_uses_jsonld_description_and_images_when_present() -> None:
    html = """
    <html>
      <head>
        <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "description": "A smooth woody gourmand perfume.",
            "image": ["/img/p1.jpg", "https://cdn.example.com/p2.jpg"]
          }
        </script>
      </head>
      <body>
        <div>Top Notes: Cardamom</div>
      </body>
    </html>
    """

    parsed = parse_product_page(html, "https://vicioso.example")

    assert parsed.description == "A smooth woody gourmand perfume."
    assert parsed.image_urls == (
        "https://vicioso.example/img/p1.jpg",
        "https://cdn.example.com/p2.jpg",
    )
    assert parsed.notes_top == ("Cardamom",)
