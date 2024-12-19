import os
import re
import logging
from extract_msg import Message 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FileManager:
    """
    A class for managing .msg files, extracting PDF attachments, and organizing them into directories.
    """

    def __init__(self, config: dict):
        """
        Initializes the FileManager with configuration.

        :param config: Configuration dictionary containing directory paths.
        """
        self.msg_dir = config["directories"]["msg_dir"]
        # self.output_dir = config["directories"]["output_dir"]
        self.tmp_dir = config["directories"]["tmp_dir"]

        os.makedirs(self.msg_dir, exist_ok=True)
        # os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)
        
        logger.info("FileManager initialized.")
        logger.info(f"Message directory: {self.msg_dir}")
        # logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Temporary directory: {self.tmp_dir}")

    @staticmethod
    def _get_pon_from_msg(msg_filename: str) -> str:
        """
        Extracts PON number from a .msg file name using a regex pattern.

        :param msg_filename: Name of the .msg file.
        :return: Extracted PON number or None.
        """
        pattern = r"PON_([\w\d]+)"
        match = re.search(pattern, msg_filename)
        if match:
            return match.group(1)
        logger.info(f"No PON number found in filename: {msg_filename}")
        return None

    @staticmethod
    def _extract_pdfs_from_msg(msg_path: str, pdf_save_dir: str):
        """
        Extracts PDF attachments from a .msg file and saves them to the designated directory.

        :param msg_path: Path to the .msg file.
        :param pdf_save_dir: Path to the directory where PDFs will be saved.
        """
        try:
            logger.info(f"Processing .msg file: {msg_path}")
            msg_file = Message(msg_path)

            for attachment in msg_file.attachments:
                if attachment.longFilename.endswith('.pdf'):
                    base_name, extension = os.path.splitext(attachment.longFilename)
                    save_path = os.path.join(pdf_save_dir, attachment.longFilename)

                    # Ensure unique filenames
                    counter = 1
                    while os.path.exists(save_path):
                        new_name = f"{base_name}-{counter}{extension}"
                        save_path = os.path.join(pdf_save_dir, new_name)
                        counter += 1

                    # Save PDF file
                    with open(save_path, 'wb') as pdf_file:
                        pdf_file.write(attachment.data)
                    logger.info(f"PDF saved: {save_path}")
        except Exception as e:
            logger.error(f"Failed to extract PDFs from {msg_path}: {e}")

    def process_msg_directory(self):
        """
        Processes the message directory, extracts PDFs from .msg files,
        and organizes them into folders based on PON numbers.
        """
        if not os.path.exists(self.msg_dir):
            logger.warning(f"Message directory does not exist: {self.msg_dir}")
            return

        if not os.listdir(self.msg_dir):
            logger.info("No files found in the message directory.")
            return

        wrong_files = []

        for filename in os.listdir(self.msg_dir):
            try:
                pon_number = self._get_pon_from_msg(filename)
                if not pon_number:
                    logger.warning(f"No PON number extracted from file: {filename}")
                    continue

                # Create a directory for the PON number
                pon_folder_path = os.path.join(self.tmp_dir, pon_number)
                os.makedirs(pon_folder_path, exist_ok=True)

                # Extract PDFs and save to the PON directory
                msg_path = os.path.join(self.msg_dir, filename)
                self._extract_pdfs_from_msg(msg_path, pon_folder_path)
            except Exception as e:
                wrong_files.append((filename, str(e)))
                logger.error(f"Error processing file {filename}: {e}")

        if wrong_files:
            logger.warning("Some files could not be processed:")
            for file, error in wrong_files:
                logger.warning(f"File: {file}, Error: {error}")

    @staticmethod
    def clear_directory(directory_path: str):
        """
        Deletes all files and subdirectories in the specified directory.

        :param directory_path: Path to the directory to clear.
        """
        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return

        logger.info(f"Clearing directory: {directory_path}")
        for root, dirs, files in os.walk(directory_path, topdown=False):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete file: {file_path}, {e}")

            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    os.rmdir(dir_path)
                except Exception as e:
                    logger.error(f"Failed to delete folder: {dir_path}, {e}")

        logger.info(f"Directory {directory_path} has been cleared.")
