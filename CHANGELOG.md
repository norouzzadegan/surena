# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2024-05-24
### Fixed
- Fixed the issue with getting a free port from the remote SSH server.

## [0.1.2] - 2024-05-23
### Fixed
- Updated logs for when Surena cannot remove a Docker image or container.

## [0.1.1] - 2024-05-23
### Added
- Added support for the 'get-docker-host' command to gain access to the Docker host using two methods: Tor network and reverse SSH.
- Added support for the 'is-docker-host' command to determine if a Docker service is accessible from the TCP network.
