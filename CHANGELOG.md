# Changelog

## [Unreleased]

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

[unreleased]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.2...HEAD
[1.0.2]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/foxypool/foxy-gh-farmer/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/foxypool/foxy-gh-farmer/releases/tag/1.0.0
