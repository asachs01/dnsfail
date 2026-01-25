# Contributing

First off, thank you for considering contributing to this project!

## Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the application

### With hardware
To run the script on a Raspberry Pi with the LED matrix and button connected, simply execute the python script:
```bash
sudo python3 dns_counter.py
```
`sudo` is required for GPIO access.

### Without hardware (Mock mode)
A mock mode for development without the physical hardware is planned but not yet implemented. This will allow running the script on any machine.

## Code Style

This project uses `black` for code formatting and `isort` for import sorting. Before submitting a pull request, please format your code:
```bash
black .
isort .
```

## Branch Naming Convention

Please use the following convention for your branch names:
- `feat/descriptive-name` for new features.
- `fix/descriptive-name` for bug fixes.
- `docs/descriptive-name` for documentation changes.

## Pull Request Process

1.  Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2.  Update the `README.md` with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
3.  Increase the version numbers in any examples and the `README.md` to the new version that this Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
4.  You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Testing on real hardware

If you have the required hardware (Raspberry Pi, RGB LED Matrix, button), you can test your changes by running the script as described in the "Running the application" section. Ensure all functionality works as expected before submitting a pull request.
