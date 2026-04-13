import os

class Config:
    INPUT_DIR = "images"
    OUTPUT_DIR = "output"
    SUPPORTED_FORMATS = ('.jpg', '.jpeg')
    
    @staticmethod
    def get_output_dir():
        output_dir = Config.OUTPUT_DIR
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    
    @staticmethod
    def get_input_dir():
        return Config.INPUT_DIR
    
    @staticmethod
    def get_report_filename(image_name):
        return os.path.splitext(image_name)[0] + "_quality_report.html"
    
    @staticmethod
    def is_supported_image(filename):
        return filename.lower().endswith(Config.SUPPORTED_FORMATS)
