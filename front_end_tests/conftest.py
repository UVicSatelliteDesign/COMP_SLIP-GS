def pytest_addoption(parser):
    parser.addoption(
        "--max-commands", action="store", default=5, type=int,
        help="Maximum number of commands to test"
    )
    parser.addoption(
        "--max-graphs", action="store", default=5, type=int,
        help="Maximum number of graphs to test"
    )
    parser.addoption(
        "--max_images", action="store", default=50, type=int,
        help="Max no. of images to generate for stress test"
    )