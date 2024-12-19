import os
import re
import pdfplumber
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class PonDictCreator:
    """
    A class to process PDF files from a directory and create a PON dictionary.
    """
    def __init__(self, config: dict):
        """
        Initializes the PonDictCreator with configuration and directory path.

        :param config: Configuration dictionary.
        :param process_dir: Path to the directory containing PDF files.
        """
        self.config = config
        self.process_dir = config["directories"]["tmp_dir"]
        self.full_dict = {}

        logger.info("Initialized PonDictCreator")
        logger.info(f"Processing directory: {self.process_dir}")

    @staticmethod
    def _extract_pdf_text(pdf_path: str) -> str:
        """
        Extracts text content from a PDF file.

        :param pdf_path: Path to the PDF file.
        :return: Extracted text as a string.
        """
        text = ""
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return ""

    def _parse_circuit_info(self, text: str) -> str:
        """
        Parses circuit information (EVC or UNI) from the extracted text.

        :param text: Extracted text from PDF.
        :return: Circuit information string.
        """
        evc_header = self.config['tmo_circuits']['evc_target_header']
        uni_header = self.config['tmo_circuits']['uni_target_header']
        evc_pattern = rf"\b\d+\.\b{self.config['tmo_circuits']['evc_uniq_keys']}\.\S*\."
        uni_pattern = rf"\b\d+\.\b(" + "|".join(self.config['tmo_circuits']['uni_uniq_keys']) + r")\.\S*\."

        def search_header(header, pattern):
            if header in text:
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if header in line and i + 1 < len(lines):
                        match = re.search(pattern, lines[i + 1])
                        if match:
                            return match.group(0)
            return None

        # Try EVC header first, then UNI header
        return search_header(evc_header, evc_pattern) or search_header(uni_header, uni_pattern)

    @staticmethod
    def _parse_contact_info(text: str) -> dict:
        """
        Extracts contact information (name, phone, email) from the extracted text.

        :param text: Extracted text from PDF.
        :return: A dictionary containing contact details.
        """
        contact_info = {"name": None, "phone": None, "email": None}
        name_phone_pattern = re.search(r"INIT TEL NO\s+([\w\s]+)\s+(\d{3}-\d{3}-\d{4})", text)
        email_pattern = re.search(r"IMPCON EMAIL MAIN TEL NO\s+([\w\.\-]+@[\w\.\-]+)", text)

        if name_phone_pattern:
            contact_info["name"] = name_phone_pattern.group(1).strip()
            contact_info["phone"] = name_phone_pattern.group(2).strip()
        if email_pattern:
            contact_info["email"] = email_pattern.group(1).strip()

        return contact_info

    @staticmethod
    def _parse_date_info(text: str) -> str:
        """
        Parses the date from the extracted text.

        :param text: Extracted text from PDF.
        :return: Extracted date string or None.
        """
        pattern = r"FDT\s*\n(\d{2}-\d{2}-\d{4})"
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _create_pon_dict(self, process_dir) -> dict:
        """
        Processes the PDF files in the specified directory and creates a dictionary with extracted data.

        :return: A dictionary containing extracted and processed data.
        """
        # pon_number = os.path.basename(process_dir)
        # pon_dict = {}
        # pon_dict[pon_number] = {
        #     "evc1": None, "evc2": None, "uni": None, "tower_name": pon_number,
        #     "contact_name": None, "contact_phone": None, "contact_email": None
        # }
        # pon_data = pon_dict[pon_number]
        # logger.info(f"Started processing directory: {process_dir}")

        # for filename in os.listdir(process_dir):
        #     file_path = os.path.join(process_dir, filename)
        #     logger.info(f"Processing file: {file_path}")

        #     # Extract and parse text from the PDF
        #     text = self._extract_pdf_text(file_path)
        #     date_sent = self._parse_date_info(text)
        #     contact_info = self._parse_contact_info(text)
        #     circuit_info = self._parse_circuit_info(text)

        #     # Update the PON dictionary with extracted data
        #     if date_sent:
        #         pon_data["date_sent"] = date_sent
        #         logger.info(f"Date extracted: {date_sent}")

        #     if contact_info.get("name"):
        #         pon_data["contact_name"] = contact_info["name"]
        #     if contact_info.get("phone"):
        #         pon_data["contact_phone"] = contact_info["phone"]
        #     if contact_info.get("email"):
        #         pon_data["contact_email"] = contact_info["email"]

        #     if circuit_info:
        #         logger.info(f"Circuit found: {circuit_info}")
        #         if self.config["tmo_circuits"]["evc_uniq_keys"] in circuit_info:
        #             pon_data["evc1"] = pon_data["evc1"] or circuit_info
        #         elif any(key in circuit_info for key in self.config["tmo_circuits"]["uni_uniq_keys"]):
        #             pon_data["uni"] = circuit_info
        #         else:
        #             pon_data["evc2"] = circuit_info

        # logger.info(f"Finished processing directory: {process_dir}")
        # return pon_dict

        dict_of_values = {}
        pon_num = os.path.basename(process_dir)
        dict_pon = dict_of_values[pon_num] = {"evc1": None, "evc2": None, "uni": None, "tower_name": pon_num,
                                            "contact_name": None, "contact_phone": None, "contact_email": None}

        try:
            for item in os.listdir(process_dir):
                
                file_path = os.path.join(process_dir, item)
                text =  self._extract_pdf_text(file_path)
                date_info = self._parse_date_info(text)
                contact_info = self._parse_contact_info(text)
                cir = self._parse_circuit_info(text)
                logger.info(f" Circuit found: {cir}")
                
                if date_info:
                    dict_pon["date_sent"] = date_info

                if contact_info.get('name'):
                    dict_pon["contact_name"] = contact_info['name']
                if contact_info.get('phone'):
                    dict_pon["contact_phone"] = contact_info['phone']
                if contact_info.get('email'):
                    dict_pon["contact_email"] = contact_info['email']
                    
                
                if self.config["tmo_circuits"]["evc_uniq_keys"] in cir:
                    if dict_pon["evc1"] is None:  
                        dict_pon["evc1"] = cir
                    else:  
                        dict_pon["evc2"] = cir
                
                elif any(key in cir for key in self.config["tmo_circuits"]["uni_uniq_keys"]):
                    dict_pon["uni"] = cir
                
                else: logger.error(f" Circuit is not found: {cir}")

        except Exception as e: logger.error(e)   

        return dict_of_values




    def create_full_dict(self) -> dict:
        for item in os.listdir(self.process_dir):
            new = self._create_pon_dict(os.path.join(self.process_dir, item))
            self.full_dict.update(new)
        return self.full_dict