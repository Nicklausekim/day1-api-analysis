"""
Day 1 - API Data Analysis Using Python Structures
Squad Python Specialization - Data Science, AI & Analytics
"""
import json
from pathlib import Path


import matplotlib.pyplot as plt
import pandas as pd
import requests
from matplotlib.ticker import MaxNLocator

API_URL = "https://jsonplaceholder.typicode.com/users"

CUSTOMER_COLUMNS = [
    "customer_id", "name", "username", "email", "email_domain", "phone",
    "city", "zipcode", "latitude", "longitude", "company", "website",
]


OUTPUT_DIR = Path(__file__).parent / "output"


def get_customers(url: str = API_URL) -> list[dict]:
    """Fetch the customer list. Report failures clearly instead of crashing."""
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        print(f"Error: the request to {url} took longer than 10 seconds and was stopped.")
        return []
    except requests.exceptions.ConnectionError:
        print("Error: could not connect to the server. Check your internet connection.")
        return []
    except requests.exceptions.RequestException as error:
        print(f"Error: the request failed ({error}).")
        return []

    if response.status_code != 200:
        print(f"Error: the server replied with status code {response.status_code} instead of 200.")
        return []

    try:
        customers = response.json()
    except ValueError:
        print("Error: the server's reply was not valid JSON.")
        return []

    return customers

def explore(record: dict, indent: int = 0) -> None:
    """Print every key in a (possibly nested) record with its type, indented by depth."""
    for key, value in record.items():
        print("    " * indent + f"{key}: {type(value).__name__}")

        if isinstance(value, dict):
            explore(value, indent + 1)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    explore(item, indent + 1)

def to_float(value) -> float:
    """Convert a value to a float. Return NaN (not a number) if it can't be converted."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def extract_attributes(customers: list[dict]) -> list[dict]:
    """Return one flat dict per customer with the attributes listed in the task."""
    rows = []
    for customer in customers:
        address = customer.get("address", {})
        geo = address.get("geo", {})
        company = customer.get("company", {})
        email = customer.get("email", "")

        row = {
            "customer_id": customer.get("id"),
            "name": customer.get("name"),
            "username": customer.get("username"),
            "email": email,
            "email_domain": email.split("@")[-1].split(".")[-1].lower(),
            "phone": customer.get("phone"),
            "city": address.get("city"),
            "zipcode": address.get("zipcode"),
            "latitude": to_float(geo.get("lat")),
            "longitude": to_float(geo.get("lng")),
            "company": company.get("name"),
            "website": customer.get("website"),
        }
        rows.append(row)

    return rows


def unique_cities(customers: list[dict]) -> set[str]:
    """Return the set of distinct cities."""
    return {customer["city"] for customer in customers if customer.get("city")}

def city_counts(customers: list[dict]) -> dict[str, int]:
    """Count customers per city using a loop and/or a dict comprehension (no Counter, no pandas)."""
    counts = {}
    for customer in customers:
        city = customer.get("city")
        if not city:
            continue
        if city in counts:
            counts[city] += 1
        else:
            counts[city] = 1
    return counts


def email_domain_counts(customers: list[dict]) -> dict[str, int]:
    """Count customers per email top-level domain (e.g. 'biz', 'tv')."""
    domains = [customer["email_domain"] for customer in customers if customer.get("email_domain")]
    return {domain: domains.count(domain) for domain in set(domains)}


def sort_counts(counts: dict[str, int]) -> dict[str, int]:
    """Return counts sorted from most to least common, then alphabetically to break ties."""
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Turn the flat customer rows into a pandas DataFrame with a fixed column order."""
    return pd.DataFrame(rows, columns=CUSTOMER_COLUMNS)

def export_csvs(df: pd.DataFrame, counts: dict[str, int], output_dir: Path = OUTPUT_DIR) -> None:
    """Save the customer table and the city counts as CSV files, without the pandas index."""
    output_dir.mkdir(parents=True, exist_ok=True)

    city_df = pd.DataFrame(list(counts.items()), columns=["city", "customer_count"])
    city_df = city_df.sort_values(["customer_count", "city"], ascending=[False, True])

    customers_path = output_dir / "customers.csv"
    city_path = output_dir / "city_counts.csv"

    try:
        df.to_csv(customers_path, index=False)
        city_df.to_csv(city_path, index=False)
    except PermissionError:
        print("Error: could not save the CSV files. Close them if they are open in Excel, then run again.")
        return

    print(f"\nSaved               : {customers_path.relative_to(Path(__file__).parent)}")
    print(f"Saved               : {city_path.relative_to(Path(__file__).parent)}")

def plot_distribution(counts: dict[str, int], path: Path,
                      title: str = "Customers by city",
                      xlabel: str = "City") -> None:
    """Save a labelled bar chart of the distribution to path."""
    if not counts:
        print(f"Nothing to plot for {path.name}: there is no data.")
        return

    labels = list(counts.keys())
    values = list(counts.values())

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values, color="#2E86AB")
    ax.bar_label(bars)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Number of customers")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except PermissionError:
        print(f"Error: could not save {path.name}. Close it if it is open, then run again.")
        return
    finally:
        plt.close(fig)

    print(f"Chart saved to      : {path.parent.name}/{path.name}")


if __name__ == "__main__":
    customers = get_customers()
    print(f"Customers retrieved : {len(customers)}")

    if customers:
        print("\nStructure of one customer record:")
        explore(customers[0])

        rows = extract_attributes(customers)

        cities = unique_cities(rows)
        print(f"\nUnique cities       : {len(cities)}")
        print(f"Cities              : {sorted(cities)}")

        if len(cities) == len(rows):
            print("Every customer lives in a different city.")
        else:
            print(f"{len(rows) - len(cities)} customers share a city with another customer.")

        cities_count = sort_counts(city_counts(rows))
        domains_count = sort_counts(email_domain_counts(rows))

        top_city = list(cities_count)[0]
        print(f"Most common city    : {top_city} ({cities_count[top_city]})")

        print("\nCustomers per city (most to least common):")
        for city, count in cities_count.items():
            print(f"  {city:<15} {count}")

        print(f"\nEmail domains       : {domains_count}")

        df = to_dataframe(rows)
        print(f"\nDataFrame shape     : {df.shape}")
        print("\nDataFrame dtypes:")
        print(df.dtypes)

        pandas_cities = df["city"].value_counts().to_dict()
        pandas_domains = df.groupby("email_domain").size().to_dict()
        print(f"\nPandas agrees on city counts   : {pandas_cities == cities_count}")
        print(f"Pandas agrees on domain counts : {pandas_domains == domains_count}")

        export_csvs(df, cities_count)

        plot_distribution(cities_count, OUTPUT_DIR / "customer_distribution.png")
        plot_distribution(
            domains_count,
            OUTPUT_DIR / "email_domain_distribution.png",
            title="Customers by email domain",
            xlabel="Email top-level domain",
        )

