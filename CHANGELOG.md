# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
* Allow fetching only certain types of interfaces (ethernet, wifi, wwan) in
  func `get_ifaces`.
* utils: Match the QMI control device to its interface and report it in
  resulting json data.
* tests: Add mock data for Mox ABC with two QMI modems.

### Changed
* Omnia: Improve labels of USB ports (front/rear).

## [0.11.0] - 2023-02-22
### Added
* Add optional info about pci slot path for wireless devices.

### Changed
* Refactor usage of function "append_iface" across devices.

## [0.10.0] - 2022-12-15
### Added
* Detect interfaces with VLAN id.

### Changed
* Refactor internal processing of interfaces.

### Removed
* CI: Remove Python 3.7 tests

## [0.9.0] - 2022-06-27
### Changed
* Mox: Refactor the ethernet port mapping, so we can tell which ethernet port
    belongs to which Mox module again on TOS 6.0.

## [0.8.0] - 2022-06-16
### Changed
* Turris 1.x: Improve detection of Turris 1.x routers on TOS 6.0
* Turris 1.x: Adjust the PCIe slots paths, so wireless card can be detected again on TOS 6.0.
    (not compatible with TOS 5.3.x)

## [0.7.0] - 2022-06-13
### Changed
* Return interfaces sorted based on interface name (natural sort order).

## [0.6.0] - 2022-05-19
### Changed
* Mox + Omnia: Get LAN & SFP interface name from label instead of port id
* Mox: Change interfaces names from numbers (0..n-1) to `LAN1..LANn`
    (e.g. LAN1-LAN12) and also rename port 0 on Module A to `ETH0`.

## [0.5.3] - 2022-04-28
### Fixed
* Fix interface labels mismatch (LAN1=lan5, ..., LAN5=lan1) on Turris 1.x,
    so it is now consistent with other Turris devices

## [0.5.2] - 2022-02-03
### Fixed
* Fix reading of interface speed; fallback to 0 on unexpected values

## [0.5.1] - 2021-08-06
### Fixed
* ignore files and consider only symlinks in `/sys/class/net` as interfaces

## [0.5.0] - 2021-05-31
### Added
* initial support for Turris 1.x

### Changed
* code cleanup and refactoring

### Removed
* drop Turris OS 3.x compatibility
* drop python2 tests on gitlab CI

## [0.4.3] - 2019-07-10
### Changed
* return 0 instead of None in `get_interfaces`

## [0.4.2] - 2019-02-26
### Changed
* omnia: remove hardcoded name of WAN device

## [0.4.1] - 2018-11-27
### Added
* added `macaddr` among interface info

## [0.4] - 2018-11-15
### Added
* add support for USB devices connected to PCI (such as LTE modems)

### Changed
* dynamic detection of interfaces

## [0.3] - 2018-11-07
### Added
* detect wifi interfaces

### Changed
* additional refactoring

## [0.2] - 2018-10-04
### Changed
* initial rework + code refactoring

## [0.1] - 2018-07-31
### Added
* initial implementation
