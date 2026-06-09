import csv
import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen


STORE_URL = "https://24h.pchome.com.tw/store/DSAA31"
MIN_REVIEW_COUNT = 1
MIN_RATING_VALUE = 4.9


@dataclass
class Product:
    id: str
    name: str
    describe: str
    review_count: int | None
    rating_value: float | None
    price: int


def fetch_page(*, page: int) -> str:
    url = f"{STORE_URL}?p={page}" if page > 1 else STORE_URL
    with urlopen(url) as response:
        return response.read().decode("utf-8")


def parse_products(*, html: str) -> list[Product]:
    key = 'initProdList\\":'
    start = html.find(key)
    if start == -1:
        return []

    array_start = html.find("[", start)
    raw = html[array_start:].replace('\\"', '"')
    products, _ = json.JSONDecoder().raw_decode(raw)
    return [
        Product(
            id=p["id"],
            name=p["name"],
            describe=p.get("describe", ""),
            review_count=p["reviewCount"],
            rating_value=p["ratingValue"],
            price=p["price"],
        )
        for p in products
    ]


def scrape_all_products() -> list[Product]:
    products: list[Product] = []
    page = 1
    while True:
        batch = parse_products(html=fetch_page(page=page))
        if not batch:
            break
        products.extend(batch)
        page += 1
    return products


def is_best_product(*, product: Product) -> bool:
    return (
        product.rating_value is not None
        and product.review_count is not None
        and product.rating_value > MIN_RATING_VALUE
        and product.review_count >= MIN_REVIEW_COUNT
    )


def is_intel_i5(*, product: Product) -> bool:
    pattern = r"(?<!\w)i5(?!\w)"
    return bool(
        re.search(pattern, product.name, re.IGNORECASE)
        or re.search(pattern, product.describe, re.IGNORECASE)
    )


def calculate_z_score(*, price: int, average: float, std_dev: float) -> float:
    if std_dev == 0:
        return 0.0
    return (price - average) / std_dev


def write_lines(*, path: Path, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


def write_csv(*, path: Path, rows: list[list]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)


def save_product_ids(*, path: Path, products: list[Product]) -> None:
    write_lines(path=path, lines=[p.id for p in products])


def save_best_product_ids(*, path: Path, products: list[Product]) -> None:
    best_ids = [p.id for p in products if is_best_product(product=p)]
    write_lines(path=path, lines=best_ids)


def print_i5_average_price(*, products: list[Product]) -> None:
    i5_prices = [p.price for p in products if is_intel_i5(product=p)]
    print(statistics.mean(i5_prices))


def save_price_standardization(*, path: Path, products: list[Product]) -> None:
    prices = [p.price for p in products]
    average = statistics.mean(prices)
    std_dev = statistics.pstdev(prices)
    rows = [
        [p.id, p.price, calculate_z_score(price=p.price, average=average, std_dev=std_dev)]
        for p in products
    ]
    write_csv(path=path, rows=rows)


def main() -> None:
    base_path = Path(__file__).parent
    products = scrape_all_products()

    # Task 1
    save_product_ids(path=base_path / "products.txt", products=products) 
    
    # Task 2
    save_best_product_ids(path=base_path / "best-products.txt", products=products)  
    
    # Task 3
    print_i5_average_price(products=products)  
    
    # Task 4
    save_price_standardization(path=base_path / "standardization.csv", products=products)  # Task 4


if __name__ == "__main__":
    main()
