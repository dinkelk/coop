import multiprocessing
import math
import decimal
import os

# Global variables to hold the state
processes = []
workers_active = False

def compute_pi():
    """Calculate pi using the Gauss-Legendre algorithm to desired precision."""
    # Set decimal precision high enough for 20 digits
    decimal.getcontext().prec = 25

    a = decimal.Decimal(1)
    b = decimal.Decimal(1) / decimal.Decimal(math.sqrt(2))
    t = decimal.Decimal(0.25)
    p = decimal.Decimal(1)

    for _ in range(25):  # Increased number of iterations for more precision
        a_next = (a + b) / 2
        b = decimal.Decimal(a * b).sqrt()
        t -= p * (a - a_next) ** 2
        a = a_next
        p *= 2

    pi_value = (a + b) ** 2 / (4 * t)
    return pi_value

def worker():
    """Set process priority to lowest and continuously compute pi to occupy CPU."""
    os.nice(19)  # Set low priority
    while True:
        pi_value = compute_pi()
        # Uncomment this if you want output
        # print(f"Computed pi: {pi_value:.20f}")

def start_workers(num_cores):
    """Start worker processes."""
    global processes, workers_active
    if workers_active:
        print("Workers are already running.")
        return
    stop_workers()  # Ensure no leftover processes
    for _ in range(num_cores):
        p = multiprocessing.Process(target=worker)
        processes.append(p)
        p.start()
    workers_active = True

def stop_workers():
    """Stop all running worker processes."""
    global processes, workers_active
    for p in processes:
        p.terminate()
    processes = []
    workers_active = False

def are_workers_active():
    """Return a boolean indicating if workers are active."""
    return workers_active

def main(num_cores):
    """Starts the worker processes."""
    start_workers(num_cores)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Heat up the CPU by computing pi.")
    parser.add_argument(
        "-c", "--cores",
        type=int,
        help="Number of CPU cores to use. Defaults to number of available cores."
    )
    args = parser.parse_args()

    if args.cores is None:
        num_cores = multiprocessing.cpu_count()
    else:
        num_cores = args.cores

    print(f"Using {num_cores} cores to compute pi continuously with low priority.")
    main(num_cores)
