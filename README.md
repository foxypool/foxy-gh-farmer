Foxy-GH-Farmer
======

Foxy-GH-Farmer is a simplified Gigahorse farmer for the chia blockchain using the Foxy-Pool Gigahorse node to farm without a full node running on your machine.

> **Note**:
> If you can run a full node, you should!

Foxy-GH-Farmer is useful in the following scenarios:
- Your hardware does not support running a full node

## Installing

### Using the binary

1. Download the latest binary zip for your OS from the [releases page](https://github.com/foxypool/foxy-gh-farmer/releases/latest)
2. Run the binary, it will create a default `foxy-gh-farmer.yaml` in the current directory based on your current chia `config.yaml`
3. Edit the `foxy-gh-farmer.yaml` to your liking and restart foxy-gh-farmer
4. Profit!

### Running from source

1. Clone the git repo and cd into it: `git clone https://github.com/foxypool/foxy-gh-farmer && cd foxy-gh-farmer`
2. Install the dependencies: `pip install .`
3. Run using `foxy-gh-farmer`, it will create a default `foxy-gh-farmer.yaml` in the current directory based on your current chia `config.yaml`
4. Edit the `foxy-gh-farmer.yaml` to your liking and restart foxy-gh-farmer
5. Profit!

### Using docker

A docker image based on the provided [Dockerfile](https://github.com/foxypool/foxy-gh-farmer/blob/main/Dockerfile) is available via `ghcr.io/foxypool/foxy-gh-farmer:latest`.
For specific tags see [this list](https://github.com/foxypool/foxy-gh-farmer/pkgs/container/foxy-gh-farmer).
A [docker-compose.yaml](https://github.com/foxypool/foxy-gh-farmer/blob/main/docker-compose.yaml) example is available as well, to get started.

Currently, this requires you to have a working `foxy-gh-farmer.yaml` already available to mount into the container. See this [example configuration](https://docs.foxypool.io/proof-of-spacetime/foxy-gh-farmer/configuration/#example-configuration) for reference.

## Are my keys safe?

Yes, Foxy-GH-Farmer itself is open source. It uses the [Gigahorse Farmer and Harvester](https://github.com/madMAx43v3r/chia-gigahorse) from madMAx43v3r under the hood which is closed source, however. As such the farming topology has not changed, your locally running farmer still signs your blocks, same as when running a local full node. Your keys do not leave your machine.

## License

GNU GPLv3 (see [LICENSE](https://github.com/foxypool/foxy-gh-farmer/blob/main/LICENSE))
