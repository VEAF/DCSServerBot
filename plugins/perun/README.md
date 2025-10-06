
# Perun Plugin for DCSServerBot

## Overview

The Perun plugin integrates with and manages Perun, a DCS extension that provides additional functionality for DCS servers. This plugin allows DCSServerBot to control Perun installations, manage their configuration, and monitor their status.

## Configuration

Configuration is done in `nodes.yaml` and has two sections:

### Node Section

```yaml
nodes:
  - name: DCS #1
    perun:
      installation: C:\path\to\Perun
      config: C:\path\to\config
```

### Instance Section

```yaml
instances:
  - name: instance1
    perun:
      host: 127.0.0.1
      port: 8080
      autostart: true
      always_on: false
      no_shutdown: false
      minimized: true
      debug: false
```

### Parameters

#### Required Parameters

- `installation`: Path to the Perun installation directory
- `config`: Path to the Perun configuration directory

#### Optional Parameters

- `host`: IP address for Perun to listen on (default: node's public IP)
- `port`: Port for Perun to listen on (default: 8080)
- `autostart`: Whether to start Perun when the DCS server starts (default: true)
- `always_on`: Whether to keep Perun running even when no DCS server is running (default: false)
- `no_shutdown`: Whether to prevent Perun from shutting down when DCS servers stop (default: false)
- `minimized`: Whether to start Perun with a minimized window (default: true)
- `debug`: Whether to enable debug output for Perun (default: false)

## Installation

1. Ensure you have Perun installed on your system
2. Configure the plugin in `nodes.yaml` as described above
3. Restart DCSServerBot to apply the changes

## Features

### Automatic Startup and Shutdown

The plugin can automatically start Perun when a DCS server starts and shut it down when all servers stop, based on your configuration.

### Configuration Management

The plugin manages Perun's configuration, ensuring that the necessary directories and files exist.

### Port Conflict Detection

The plugin checks for port conflicts before starting Perun and logs warnings if conflicts are detected.

### Process Monitoring

The plugin monitors the Perun process and can report its status.

## Advanced Configuration Examples

### Running Perun on a Different Port

```yaml
instances:
  - name: instance1
    perun:
      port: 8081
```

### Keeping Perun Running Independently of DCS Servers

```yaml
instances:
  - name: instance1
    perun:
      always_on: true
      no_shutdown: true
```

### Running Multiple Perun Instances

```yaml
instances:
  - name: instance1
    perun:
      port: 8080
  - name: instance2
    perun:
      port: 8081
```

## Troubleshooting

### Perun Won't Start

- Check that the installation path is correct
- Verify that the Perun executable exists and is accessible
- Check for port conflicts with other applications
- Review the logs for specific error messages

### Port Conflicts

If you see a message about port conflicts:
1. Change the port in your configuration
2. Identify and stop the application using the conflicting port
3. Restart DCSServerBot

### Process Monitoring Issues

If the plugin can't determine if Perun is running:
1. Check that the process is not being blocked by antivirus software
2. Verify that the plugin has permission to monitor processes
3. Try running DCSServerBot with administrator privileges

## Logging

The plugin logs information about Perun's status and operations. Check the DCSServerBot logs for messages prefixed with `[Perun]` for troubleshooting.

## Support

For issues with the Perun plugin, please refer to the DCSServerBot documentation or contact the developers.
