from factorize import CustomLogger, Factorize, Colors
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging
import shutil
import re
import os


# ​Determination of constants and data structures
JPEG_IMAGES = []
JPG_IMAGES = []
PNG_IMAGES = []
SVG_IMAGES = []
MP3_AUDIO = []
OGG_AUDIO = []
WAV_AUDIO = []
AMR_AUDIO = []
AVI_VIDEO = []
MP4_VIDEO = []
MOV_VIDEO = []
MKV_VIDEO = []
DOC_DOCS = []
DOCX_DOCS = []
TXT_DOCS = []
PDF_DOCS = []
XLSX_DOCS = []
PPTX_DOCS = []
ARCHIVES = []
MY_OTHER = []

REGISTER_EXTENSION = {
    "JPEG": JPEG_IMAGES,
    "JPG": JPG_IMAGES,
    "PNG": PNG_IMAGES,
    "SVG": SVG_IMAGES,
    "MP3": MP3_AUDIO,
    "OGG": OGG_AUDIO,
    "WAV": WAV_AUDIO,
    "AMR": AMR_AUDIO,
    "AVI": AVI_VIDEO,
    "MP4": MP4_VIDEO,
    "MOV": MOV_VIDEO,
    "MKV": MKV_VIDEO,
    "DOC": DOC_DOCS,
    "DOCX": DOCX_DOCS,
    "TXT": TXT_DOCS,
    "PDF": PDF_DOCS,
    "XLSX": XLSX_DOCS,
    "PPTX": PPTX_DOCS,
    "ZIP": ARCHIVES,
    "GZ": ARCHIVES,
    "TAR": ARCHIVES,
}

FOLDERS = []
EXTENSIONS = set()
UNKNOWN = set()

pattern = r"\W"

CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = (
    "a",
    "b",
    "v",
    "g",
    "d",
    "e",
    "yo",
    "zh",
    "z",
    "i",
    "y",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "kh",
    "ts",
    "ch",
    "sh",
    "shch",
    "'",
    "y",
    "'",
    "e",
    "yu",
    "ya",
    "ye",
    "i",
    "yi",
    "g",
)

TRANS = {}

for c, l in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    TRANS[ord(c)] = l
    TRANS[ord(c.upper())] = l.upper()


class MediaHandler:
    """
    Class for file sorted operations.

    :param logger: Logger instance for logging.
    """

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def get_extension(self, name: str) -> str:
        """Determination of functions for processing files and folders."""
        return Path(name).suffix[1:].upper()

    def normalize(self, name: str) -> str:
        """Normalizes the name of the file."""
        filename, ext = os.path.splitext(name)
        filename = re.sub(pattern, "_", filename.translate(TRANS))
        return filename + ext

    def handle_media(self, file_name: Path, target_folder: Path):
        """Processes multimedia files."""
        try:
            target_folder.mkdir(exist_ok=True, parents=True)
            new_file_path = target_folder / self.normalize(file_name.name)
            shutil.move(str(file_name), str(new_file_path))
        except Exception as e:
            pass

    def handle_archive(self, file_name: Path, target_folder: Path):
        """Processes archives."""
        target_folder.mkdir(exist_ok=True, parents=True)
        folder_for_file = target_folder / self.normalize(
            file_name.name.replace(file_name.suffix, "")
        )
        folder_for_file.mkdir(exist_ok=True, parents=True)
        try:
            shutil.unpack_archive(
                str(file_name.absolute()), str(folder_for_file.absolute())
            )
        except shutil.ReadError:
            folder_for_file.rmdir()
            return
        file_name.unlink()

    def process_files(self, file_list, target_folder):
        """Processes files."""
        for file in file_list:
            self.handle_media(file, target_folder)

    def process_images(self, images, target_folder):
        """Processes images."""
        self.process_files(images, target_folder)

    def process_audio(self, audio, target_folder):
        """Processes audio files."""
        self.process_files(audio, target_folder)

    def process_video(self, video, target_folder):
        """Processes video files."""
        self.process_files(video, target_folder)

    def process_documents(self, documents, target_folder):
        """Processes documents."""
        self.process_files(documents, target_folder)

    def process_archives(self, archives, target_folder):
        """Processes archives."""
        for archive in archives:
            self.handle_archive(archive, target_folder)

    def scan(self, folder: Path):
        """Scans the contents of the folder."""
        for item in folder.iterdir():
            if item.is_dir():
                if item.name not in (
                    "archives",
                    "video",
                    "audio",
                    "documents",
                    "images",
                    "MY_OTHER",
                ):
                    FOLDERS.append(item)
                    self.scan(item)
                continue
            extension = self.get_extension(item.name)
            full_name = folder / item.name
            if not extension:
                MY_OTHER.append(full_name)
            else:
                try:
                    REGISTER_EXTENSION[extension].append(full_name)
                    EXTENSIONS.add(extension)
                except KeyError:
                    UNKNOWN.add(extension)
                    MY_OTHER.append(full_name)

    def process_folder(self, folder):
        """Processes the contents of the folder."""
        local_files = []
        local_folders = []

        result_folder = Path("result")
        result_folder.mkdir(exist_ok=True)

        for item in folder.iterdir():
            if item.is_dir():
                local_folders.append(item)
            else:
                local_files.append(item)

        with ThreadPoolExecutor(max_workers=5) as executor:
            for subfolder in local_folders:
                executor.submit(self.process_folder, subfolder)

            executor.submit(
                self.process_images,
                JPEG_IMAGES + JPG_IMAGES + PNG_IMAGES + SVG_IMAGES,
                result_folder / "images",
            )
            executor.submit(
                self.process_audio,
                MP3_AUDIO + OGG_AUDIO + WAV_AUDIO + AMR_AUDIO,
                result_folder / "audio",
            )
            executor.submit(
                self.process_video,
                AVI_VIDEO + MP4_VIDEO + MOV_VIDEO + MKV_VIDEO,
                result_folder / "video",
            )
            executor.submit(
                self.process_documents,
                DOC_DOCS + DOCX_DOCS + TXT_DOCS + PDF_DOCS + XLSX_DOCS + PPTX_DOCS,
                result_folder / "documents",
            )
            executor.submit(self.process_archives, ARCHIVES, result_folder / "archives")
            executor.submit(self.process_files, MY_OTHER, result_folder / "MY_OTHER")

    def run(self, folder: Path):
        """Triggers the processing of the folder from the command line argument."""
        self.scan(folder)
        self.process_folder(folder)


def main():
    """The main function for processing"""
    try:
        logger = CustomLogger("error.log")
        logger.log(
            f"""{Colors.ORANGE}Please select the operating mode.{Colors.RESET}
{Colors.BLUE}Enter <sort> to sort the folder by extance or <fact> to obtain a promise divider of numbers.{Colors.RESET}"""
        )
        logger.log(
            f"{Colors.WARNING}To get out of the program enter <exit> <quit> <q>.{Colors.RESET}"
        )
        while True:
            user_input = input(f"{Colors.BOLD}Enter the command: {Colors.RESET}")
            if user_input == "sort":
                path_folder = input(
                    f"{Colors.BOLD}Enter the path to the folder: {Colors.RESET}"
                )
                path_folder = Path(path_folder)
                if path_folder:
                    media_handler = MediaHandler(logger)
                    media_handler.run(path_folder)
                    logger.log(
                        f"{Colors.GREEN}Files have been successfully sorted.{Colors.RESET}"
                    )
                    logger.log(
                        f"{Colors.GREEN}Sorted files are in the Result folde.{Colors.RESET}"
                    )
            elif user_input == "fact":
                factorizer = Factorize(logger)

                numbers_to_factorize = list(
                    range(
                        int(
                            input(
                                f"{Colors.BOLD}Enter the starting number for factorization: {Colors.RESET}"
                            )
                        ),
                        int(
                            input(
                                f"{Colors.BOLD}Enter the ending number for factorization: {Colors.RESET}"
                            )
                        ),
                    )
                )
                number_processes = int(
                    input(f"{Colors.BOLD}Enter the number of processes: {Colors.RESET}")
                )
                if number_processes < 1:
                    number_processes = 2
                num_processes = min(
                    22, max(number_processes, len(numbers_to_factorize) // 1000)
                )

                factorizer.write_to_file(
                    factorizer.process_factorization(
                        numbers_to_factorize, num_processes
                    )
                )

            elif user_input in ["exit", "quit", "q"]:
                logger.log(f"{Colors.ORANGE}Good bye!{Colors.RESET}")
                break

            else:
                logger.log(
                    f"{Colors.FAIL}Wrong commands, please try again.{Colors.RESET}"
                )

    except Exception as e:
        logger.log(f"Error in main: {str(e)}", level=logging.ERROR)


if __name__ == "__main__":
    main()
