Foxy-GH-Farmer
======

Foxy-GH-Farmer is a simplified Gigahorse farmer for the chia blockchain using the Foxy-Pool Gigahorse node to farm without a full node running on your machine.

> **Note**:
> If you can run a full node, you should!

Foxy-GH-Farmer is useful in the following scenarios:
- Your hardware does not support running a full node

If you are migrating from FlexFarmer please check out [this guide](https://docs.foxypool.io/proof-of-spacetime/guides/switching-from-flex-farmer-to-foxy/).

The docs can be found [here](https://docs.foxypool.io/proof-of-spacetime/foxy-gh-farmer/).

## Installing

### Using the binary

1. On Linux ensure you have `libgomp1` as well as `ocl-icd-libopencl1` installed
2. Download the latest binary zip for your OS from the [releases page](https://github.com/foxypool/foxy-gh-farmer/releases/latest)
3. Run the binary, it will create a default `foxy-gh-farmer.yaml` in the current directory based on your current chia `config.yaml`
   > **Note**:
   > If you never set up chia before on this machine you will need to import your 24 word mnemonic using `./foxy-gh-farmer keys add` and ensure the `config.yaml` in `<USER_HOME>/.foxy-gh-farmer/mainnet/config/` includes your PlotNFT in the pool list. This can be achieved by manually copying it from another `config.yaml` or running `./foxy-gh-farmer join-pool`.

4. Edit the `foxy-gh-farmer.yaml` to your liking and restart foxy-gh-farmer
5. Profit!

### Running from source

1. On Linux ensure you have `libgomp1` as well as `ocl-icd-libopencl1` installed
2. Clone the git repo and cd into it: `git clone https://github.com/foxypool/foxy-gh-farmer && cd foxy-gh-farmer`
3. Create a venv:
    ```bash
    python3 -m venv venv
    ```
4. Install the dependencies:
    ```bash
    venv/bin/pip install .
    ```
5. Run using `venv/bin/foxy-gh-farmer` (or activate the venv using `source venv/bin/activate` and then just use `foxy-gh-farmer`), it will create a default `foxy-gh-farmer.yaml` in the current directory based on your current chia `config.yaml` if available.
   > **Note**:
   > If you never set up chia before on this machine you will need to import your 24 word mnemonic using `venv/bin/foxy-gh-farmer keys add` and ensure the `config.yaml` in `<USER_HOME>/.foxy-gh-farmer/mainnet/config/` includes your PlotNFT in the pool list. This can be achieved by manually copying it from another `config.yaml` or running `venv/bin/foxy-gh-farmer join-pool`.

6. Edit the `foxy-gh-farmer.yaml` to your liking and restart foxy-gh-farmer
7. Profit!

### Using docker

A docker image based on the provided [Dockerfile](https://github.com/foxypool/foxy-gh-farmer/blob/main/Dockerfile) is available via `ghcr.io/foxypool/foxy-gh-farmer:latest` and `foxypool/foxy-gh-farmer:latest`.
For specific tags see [this list](https://github.com/foxypool/foxy-gh-farmer/pkgs/container/foxy-gh-farmer).
A [docker-compose.yaml](https://github.com/foxypool/foxy-gh-farmer/blob/main/docker-compose.yaml) example is available as well, to get started.

Currently, this requires you to have a working `foxy-gh-farmer.yaml` already available to mount into the container. See this [example configuration](https://docs.foxypool.io/proof-of-spacetime/foxy-gh-farmer/configuration/#example-configuration) for reference.
If you do not have a `.chia_keys` directory from a previous chia install, you can set the `CHIA_MNEMONIC` environment variable to your 24 words and it will create they keyring accordingly. Please unset it again once done.

> **Note**:
> To execute the `join-pool` command please first `exec` into the running container with
> ```bash
> docker exec -it <name of your container> bash
> ```
> Then you can run `foxy-gh-farmer join-pool` inside the container.

## Updating

### Using the binary

Just download the latest version of the binary [from here](https://github.com/foxypool/foxy-gh-farmer/releases/latest) like you did on install and replace the existing binary, that's it.

### Running from source

1. Open a terminal in the `foxy-gh-farmer` directory which you cloned during install.
2. Run `git pull`
3. Run `venv/bin/pip install --upgrade .`

### Using docker

Pull the latest image using `docker pull ghcr.io/foxypool/foxy-gh-farmer:latest` and recreate the container using `docker compose up -d`.

## Are my keys safe?

Yes, Foxy-GH-Farmer itself is open source. It uses the [Gigahorse Farmer and Harvester](https://github.com/madMAx43v3r/chia-gigahorse) from madMAx43v3r under the hood which is closed source, however. As such the farming topology has not changed, your locally running farmer still signs your blocks, same as when running a local full node. Your keys do not leave your machine.

## License

GNU GPLv3 (see [LICENSE](https://github.com/foxypool/foxy-gh-farmer/blob/main/LICENSE))
