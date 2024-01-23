from typing import List, Tuple
from functools import wraps
import concurrent.futures
import logging
import time


class Colors:
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    ORANGE = "\033[38;5;208m"
    PINK = "\033[95m"
    RESET = "\033[0m"


class CustomLogger:
    """
    Custom logger class for handling both console and file logging.

    :param log_file: Path to the log file.
    :param console_level: Logging level for console output (default INFO).
    :param file_level: Logging level for file output (default ERROR).
    """

    def __init__(
        self,
        log_file: str,
        console_level: int = logging.INFO,
        file_level: int = logging.ERROR,
    ):
        self.logger = logging.getLogger("custom_logger")
        self.logger.setLevel(logging.INFO)

        # Log for console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # Log for file
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(file_level)
        file_formatter = logging.Formatter(
            "%(levelname)s, %(asctime)s %(module)s %(funcName)s %(lineno)d - %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def log(self, message: str, level: int = logging.INFO):
        """
        Method for recording messages in the log.

        :param message: Message for writing to the log.
        :param level: Logging level (default Info).
        """
        self.logger.log(level, message)


class Factorize:
    """
    Class for factorization operations.

    :param logger: Logger instance for logging.
    """

    def __init__(self, logger: CustomLogger):
        self.logger = logger

    def timing_decorator(func):
        """
        Decorator for measuring the execution time of a function.

        :param func: Function to be decorated.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            all_time = end_time - start_time
            args[0].logger.log(
                f"{Colors.BLUE}Execution time: {all_time} seconds{Colors.RESET}"
            )
            return result

        return wrapper

    def factorize(self, number: int) -> List[int]:
        """
        Function for factorization of the number.

        :param number: The number that needs to be factorized.
        :return: List of number dividers.
        """
        factors = []
        try:
            for num in range(1, int(number**0.5) + 1):
                if number % num == 0:
                    factors.append(num)
                    if num != number // num:
                        factors.append(number // num)
        except Exception as e:
            self.logger.log(f"Error in factorize: {str(e)}", level=logging.ERROR)
        return sorted(factors)

    def factorize_all_parallel_chunked(
        self, chunk: List[int]
    ) -> List[Tuple[int, List[int]]]:
        """
        Function for parallel factorization of the list of numbers.

        :param chunk: Part of the list of numbers for factorization.
        :return: List of motorcade containing the number and its divider.
        """
        result = []

        for number in chunk:
            try:
                result.append((number, self.factorize(number)))
            except Exception as e:
                self.logger.log(
                    f"Error in factorize_all_parallel_chunked: {str(e)}",
                    level=logging.ERROR,
                )

        return result

    @timing_decorator
    def process_factorization(
        self, numbers_to_factorize: List[int], num_processes: int
    ) -> List[Tuple[int, List[int]]]:
        """
        Method for processing factorization of the list of numbers using parallelism.

        :param numbers_to_factorize: List of numbers for factorization.
        :param num_processes: The number of processes for parallel processing.
        :return: List of tuples containing the number and its dividers.
        """

        try:
            chunk_size = len(numbers_to_factorize) // num_processes
            remainder = len(numbers_to_factorize) % num_processes
            chunks = []
            start = 0

            for process in range(num_processes):
                end = start + chunk_size + (1 if process < remainder else 0)
                chunks.append(numbers_to_factorize[start:end])
                start = end

            with concurrent.futures.ProcessPoolExecutor(
                max_workers=num_processes
            ) as executor:
                futures = [
                    executor.submit(self.factorize_all_parallel_chunked, chunk)
                    for chunk in chunks
                ]

                result_parallel = []

                for future in concurrent.futures.as_completed(futures):
                    try:
                        result_parallel.extend(future.result())
                    except Exception as e:
                        self.logger.log(
                            f"Error in process_factorization: {str(e)}",
                            level=logging.ERROR,
                        )

            return result_parallel

        except Exception as e:
            self.logger.log(f"Error in process_factorization: {str(e)}")

    def write_to_file(self, result_parallel: List[Tuple[int, List[int]]]) -> None:
        """
        Write factorization results to a file.

        :param result_parallel: List of tuples containing the number and its dividers.
        """
        with open("factorization_results.txt", "w") as file:
            self.result_parallel = result_parallel
            for item in result_parallel:
                file.write(f"{item}\n")
        self.logger.log(
            f"{Colors.GREEN}The results are successfully preserved in factorization_results.txt{Colors.RESET}"
        )
