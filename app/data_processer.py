import polars as pl
from copy import deepcopy
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PonDictProcessor:
    """
    A class to process PON dictionaries by adding data, sorting by type, and grouping by date.
    """
    def __init__(self, config: dict):
        """
        Initializes the PonDictProcessor with a configuration dictionary.

        :param config: Configuration dictionary.
        """
        self.config = config

    @staticmethod
    def add_cvlan_data(pon_dict: dict, config: dict) -> tuple:
        """
        Adds CVLAN data to the dictionary using the lookup DataFrame.

        :param pon_dict: Dictionary containing pon data.
        :param config: Configuration dictionary.
        :return: Updated dictionary and list of suspicious tower numbers.
        """
        pon_dict = deepcopy(pon_dict)
        suspicious_towers = []
        columns_mapping = config["tmo_circuits"]["tmo_columns_mapping"]
        lookup_df = pl.read_csv(config["tmo_circuits"]["tmo_lookup_path"])

        for key, value in pon_dict.items():
            tower_name = value["tower_name"]

            cvlan_evc1 = PonDictProcessor._get_cvlan(lookup_df, columns_mapping, tower_name, value["evc1"], "evc1", suspicious_towers)
            cvlan_evc2 = PonDictProcessor._get_cvlan(lookup_df, columns_mapping, tower_name, value["evc2"], "evc2", suspicious_towers)

            # Combine CVLAN values
            combined_cvlan = f"{cvlan_evc1 or ''}/{cvlan_evc2 or ''}".strip("/")
            if combined_cvlan:
                value["cvlan"] = combined_cvlan
            else:
                logger.info(f"No CVLAN found for site: {key}")

        return pon_dict, suspicious_towers

    @staticmethod
    def _get_cvlan(lookup_df, columns_mapping, tower_name, evc_value, evc_key, suspicious_towers):
        """
        Retrieves CVLAN value for a specific tower and EVC.

        :param lookup_df: Polars DataFrame for CVLAN lookup.
        :param columns_mapping: Column name mapping from configuration.
        :param tower_name: Name of the tower.
        :param evc_value: EVC value to search.
        :param evc_key: Key indicating EVC type (evc1 or evc2).
        :param suspicious_towers: List to collect suspicious towers.
        :return: CVLAN value or None.
        """
        try:
            result = lookup_df.filter([
                pl.col(columns_mapping["tower_column"]) == tower_name,
                pl.col(columns_mapping["evc_column"]) == evc_value
            ])["CVLAN"]
            return result.item() if len(result) == 1 else None
        except Exception as e:
            logger.error(f"Error retrieving CVLAN for {evc_key} at {tower_name}: {e}")
            suspicious_towers.append(tower_name)
            return None

    @staticmethod
    def add_address_data(pon_dict: dict, config: dict) -> dict:
        """
        Adds address data to the dictionary using the site lookup DataFrame.

        :param pon_dict: Dictionary containing pon data.
        :param config: Configuration dictionary.
        :return: Updated dictionary with address data.
        """
        pon_dict = deepcopy(pon_dict)
        address_df = pl.read_excel(config["site_lookup"]["df_of_sites_dir"])

        for key, value in pon_dict.items():
            try:
                site_info = address_df.filter(pl.col("Site Name") == key).row(0, named=True)
                value.update(site_info)
                value.pop("Site Name", None)
            except Exception as e:
                logger.warning(f"No address data found for site: {key} - {e}")
        return pon_dict

    @staticmethod
    def sort_by_type(pon_dict: dict, config: dict) -> dict:
        """
        Sorts pon_dict by type into pdisc, fdisc, and no_type.

        :param pon_dict: Dictionary containing pon data.
        :param config: Configuration dictionary.
        :return: Sorted dictionary by type.
        """
        lookup_df = pl.read_csv(config["tmo_circuits"]["tmo_lookup_path"])
        sorted_dict = {"pdisc": {"vlan": {}, "unievc": {}}, "fdisc": {}, "no_type": {}}

        for key, value in pon_dict.items():
            tower_filter = lookup_df.filter(pl.col("Tower Name") == key)
            uni, evc1, evc2 = value.get("uni"), value.get("evc1"), value.get("evc2")

            if len(tower_filter) > 2:
                if uni and evc1 and evc2:
                    sorted_dict["pdisc"]["unievc"][key] = value
                elif evc1 and evc2 and not uni:
                    sorted_dict["pdisc"]["vlan"][key] = value
                else:
                    sorted_dict["no_type"][key] = value
            else:
                if uni and evc1 and evc2:
                    sorted_dict["fdisc"][key] = value
                else:
                    sorted_dict["no_type"][key] = value

        return sorted_dict

    @staticmethod
    def sort_by_date(pon_dict: dict) -> dict:
        """
        Sorts pon_dict data by 'date_sent'.

        :param pon_dict: Dictionary containing pon data.
        :return: Dictionary grouped by 'date_sent'.
        """
        grouped_dict = defaultdict(lambda: defaultdict(dict))

        def group_entries(entries, target):
            for key, value in entries.items():
                date_sent = value.get("date_sent")
                if date_sent:
                    target[date_sent][key] = value

        for section in ["unievc", "vlan"]:
            group_entries(pon_dict.get("pdisc", {}).get(section, {}), grouped_dict[section])
        for section in ["fdisc", "no_type"]:
            group_entries(pon_dict.get(section, {}), grouped_dict[section])

        return {section: dict(data) for section, data in grouped_dict.items()}

    def process(self, pon_dict: dict) -> dict:
        """
        Orchestrates the processing of PON data:
        1. Adds CVLAN and address data.
        2. Sorts by type.
        3. Sorts by date.

        :param pon_dict: The initial PON dictionary.
        :return: Final processed dictionary.
        """
        logger.info("Starting PON dictionary processing...")
        pon_dict, suspicious_towers = self.add_cvlan_data(pon_dict, self.config)
        if suspicious_towers:
            logger.warning(f"Suspicious towers encountered: {suspicious_towers}")

        pon_dict = self.add_address_data(pon_dict, self.config)
        sorted_by_type = self.sort_by_type(pon_dict, self.config)
        sorted_by_date = self.sort_by_date(sorted_by_type)

        logger.info("PON dictionary processing completed.")
        return sorted_by_date
