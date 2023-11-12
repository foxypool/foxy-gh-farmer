# Changelog

## [Unreleased]

## [1.7.0] - 2023-11-12

### Added

- Add new `init` command to ensure configurations and the gigahorse binary are available without running the farmer.
- Add support for `--version` argument to print the version and exit.
- Add support for the pool to show the Foxy-GH-Farmer version.

## [1.6.1] - 2023-11-05

### Changed

- Show a more helpful error message when the `foxy-gh-farmer.yaml` is not formatted correctly and can not be parsed.

### Fixed

- Fix a crash when the daemon startup takes a long time.
- Fix harvester not connecting to the farmer on new installs.

## [1.6.0] - 2023-11-05

### Added

- Add plot refresh batch options `plot_refresh_batch_size` and `plot_refresh_batch_sleep_ms`.
- Add port override config options and `--root-path` command line argument to allow running multiple Foxy-GH-Farmer instances.

### Fixed

- Fix crash on startup when using the binary and no `farmer_reward_address` and/or `pool_payout_address` are set.
- Fix parsing of multiline syslog messages.

## [1.5.0] - 2023-11-03

### Added

- Add sentry error reporting.
- Print harvester id on startup for easy identification same as Foxy-Farmer.
- Add `plot_nfts` config option to easily deploy new Foxy-GH-Farmers for already joined PlotNFTs.

### Changed

- Update gigahorse to 2.1.1.giga23.

### Fixed

- Fix the daemon not shutting down when exiting on keyring unlock with a newly started daemon.

## [1.4.2] - 2023-10-31

### Fixed

- Prevent deadlock when joining many PlotNFTs to the pool.

## [1.4.1] - 2023-10-30

### Changed

- Update the `./foxy-gh-farmer summary` command to show effective capacity as well.
- Package ubuntu binaries using ubuntu 20.04 to support older systems.

### Fixed

- Prevent crash by exiting early on missing `farmer_reward_address` and/or `pool_payout_address`.

## [1.4.0] - 2023-10-26

### Added

- Add `auth` command to generate PlotNFT login links.

## [1.3.0] - 2023-10-25

### Added

- Add support for configuring a different syslog port, default is `11514`.

### Changed

- Update gigahorse to 2.1.1.giga22.

## [1.2.3] - 2023-10-24

### Fixed

- Fix a crash when an existing chia config from chia-blockchain 1.1.7 or earlier was used to create the foxy-gh-farmer chia config.

## [1.2.2] - 2023-10-22

### Changed

- Update gigahorse to 1.8.2.giga22.

### Fixed

- Setting an integer value for one of the chiapos environment config options works correctly now.

## [1.2.1] - 2023-10-22

### Changed

- Update gigahorse to 1.8.2.giga21.

## [1.2.0] - 2023-10-21

### Added

- Update gigahorse to 1.8.2.giga20.
- Add additional wallet sync info while running `./foxy-gh-farmer join-pool`.

### Fixed

- Running `join-pool` with an already started daemon with a locked keyring works correctly now.
- Fix `join-pool` on systems where the wallet startup took longer than 5 seconds.

## [1.1.1] - 2023-10-18

### Fixed

- Downloading Gigahorse from within China works correctly now.

## [1.1.0] - 2023-10-17

### Added

- Support adding your first key via a `CHIA_MNEMONIC` environment variable to simplify docker setups.

### Fixed

- Fix `join-pool` command not working properly when another chia wallet is running.

## [1.0.2] - 2023-10-12

### Fixed

- Fix https requests on systems with outdated ca stores

## [1.0.1] - 2023-10-08

### Fixed

- Fix a crash on startup when the chia config is missing the `connect_to_unknown_peers` config option

## [1.0.0] - 2023-10-08

### Added

- Initial release

[unreleased]: https://github.com/foxypool/foxy-gh-farmer/compare/1.7.0...HEAD
[1.7.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.6.1...1.7.0
[1.6.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.6.0...1.6.1
[1.6.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.5.0...1.6.0
[1.5.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.4.2...1.5.0
[1.4.2]: https://github.com/foxypool/foxy-gh-farmer/compare/1.4.1...1.4.2
[1.4.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.2.3...1.3.0
[1.2.3]: https://github.com/foxypool/foxy-gh-farmer/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/foxypool/foxy-gh-farmer/compare/1.2.1...1.2.2
[1.2.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.1.1...1.2.0
[1.1.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.1.0...1.1.1
[1.1.0]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.2...1.1.0
[1.0.2]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/foxypool/foxy-gh-farmer/releases/tag/1.0.0
