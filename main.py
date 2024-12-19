import logging
import os
import shutil
from app.config import Config
from app.data_processer import PonDictProcessor
from app.pdf_parser import PonDictCreator
from app.exporter import Exporter
from app.file_manager import FileManager
from utils.logging_config import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("______________________________Script started______________________________")
    config = Config("./config.json")

    file_manager = FileManager(config)
    creator = PonDictCreator(config)
    processor = PonDictProcessor(config)
    exporter = Exporter(config)

    # customer = config["config_templates"]["customer"]
    output_dir = config["directories"]["output_dir"]
    tmp_dir = config["directories"]["tmp_dir"]
    file_format = ".xlsx"


    file_manager.clear_directory(output_dir)
    file_manager.clear_directory(tmp_dir)


    file_manager.process_msg_directory()
    pon_dict = creator.create_full_dict()
    final_dict = processor.process(pon_dict)
    
    for k, val in final_dict.items():
        
        for key, value in val.items():
            
            basic_path = os.path.join(output_dir, k, key)
            sites_path = os.path.join(basic_path, f"{len(value)}-SITES")
            os.makedirs(basic_path, exist_ok=True)
            os.makedirs(sites_path, exist_ok=True)

            for pon in value.keys():
                pon_path = os.path.join(sites_path, pon)
                if os.path.exists(pon_path):
                    pass
                else: shutil.move(os.path.join(tmp_dir, pon), pon_path)

            excel_output_path = f"{basic_path}/CONFIGURATOR-{key}-{k}-{len(value)}-SITES{file_format}" 
            exporter.export(value, excel_output_path)
    
    logger.info("Script finished successfully. Enjoy =)")
    
if __name__ == "__main__":
    main()