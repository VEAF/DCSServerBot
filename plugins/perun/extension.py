
import asyncio
import os
import psutil
import subprocess
import sys
import tempfile
import aiofiles
import shutil
import logging
from typing import Optional, Dict, Any, List, Iterator, Union, Tuple
from configparser import RawConfigParser
from core import Extension, utils, Server, get_translation, InstallException

_ = get_translation(__name__.split('.')[1])

# Global registry of used ports to prevent conflicts
ports: Dict[int, str] = dict()

__all__ = [
    "Perun"
]


class Perun(Extension):
    """
    Perun extension for DCSServerBot.
    
    This extension manages the Perun DCS server extension, handling its lifecycle
    (startup, shutdown) and configuration.
    """

    CONFIG_DICT = {
        "port": {
            "type": int,
            "label": _("Perun Port"),
            "placeholder": _("Unique port number for Perun"),
            "required": True,
            "default": 6001
        },
        "host": {
            "type": str,
            "label": _("Perun Host"),
            "placeholder": _("Host address for Perun"),
            "required": False,
            "default": "127.0.0.1"
        }
    }

    def __init__(self, server: Server, config: Dict[str, Any]):
        """
        Initialize the Perun extension.
        
        Args:
            server: The DCS server instance
            config: Configuration dictionary for this extension
        """
        self.log = logging.getLogger(__name__)
        self.cfg = RawConfigParser()
        self.cfg.optionxform = str
        self.process: Optional[psutil.Process] = None
        self._inst_path: Optional[str] = None
        self.exe_name: Optional[str] = None
        
        self.log.debug(f"Initializing Perun extension for server: {server.name}")
        self.log.debug(f"Perun config: {config}")
        
        # Validate required configuration
        if 'installation' not in config and sys.platform not in ['win32', 'linux']:
            self.log.error(f"Unsupported platform {sys.platform} and no installation path provided")
            raise InstallException(f"Unsupported platform {sys.platform} and no installation path provided")
        
        if 'installation' in config:
            self.log.debug(f"Using specified installation path: {config['installation']}")
        else:
            self.log.debug(f"No installation path provided, will use default for platform: {sys.platform}")
            
        super().__init__(server, config)

    def get_config_path(self) -> str:
        """
        Get the path to the Perun configuration file.
        
        Returns:
            The absolute path to the configuration file
        """
        config_path = self.config.get('config')
        if not config_path:
            config_path = os.path.join(self.get_inst_path(), 'perun.cfg')
            self.log.warning(f"  => {self.name}: No config parameter given, using default config path: {config_path}")
        path = os.path.expandvars(config_path.format(server=self.server, instance=self.server.instance))
        self.log.debug(f"Perun config path: {path}")
        return path

    def load_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the Perun configuration file.
        
        Returns:
            Dictionary containing the parsed configuration
        """
        try:
            if 'config' in self.config:
                config_path = self.get_config_path()
                if not os.path.exists(config_path):
                    self.log.warning(f"Configuration file not found at {config_path}")
                    return {}
                
                self.log.debug(f"Loading Perun config from: {config_path}")
                self.cfg.read(config_path, encoding='utf-8')
                self.log.debug(f"Perun config sections: {self.cfg.sections()}")
                for section in self.cfg.sections():
                    self.log.debug(f"Config section [{section}]: {dict(self.cfg[section])}")
                return {
                    s: {_name: utils.parse_value(_value) for _name, _value in self.cfg.items(s)}
                    for s in self.cfg.sections()
                }
            else:
                return {}
        except Exception as ex:
            self.log.error(f"Error loading configuration: {str(ex)}", exc_info=True)
            return {}

    def _maybe_update_config(self, section: str, key: str, value_key: str) -> bool:
        """
        Update a configuration value if needed.
        
        Args:
            section: Configuration section
            key: Configuration key
            value_key: Key in self.config to get the value from
            
        Returns:
            True if the configuration was updated, False otherwise
        """
        if value_key in self.config:
            value = self.config[value_key]
            if not self.cfg.has_section(section):
                self.cfg.add_section(section)
            if not self.cfg[section].get(key) or utils.parse_value(self.cfg[section][key]) != value:
                self.cfg.set(section, key, str(value))
                self.log.info(f"  => {self.server.name}: [{section}][{key}] set to {self.config[value_key]}")
                return True
        return False

    async def _ensure_config_directory(self, path: str) -> None:
        """
        Ensure the configuration directory exists.
        
        Args:
            path: Path to the configuration file
        """
        config_dir = os.path.dirname(path)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
                self.log.info(f"Created configuration directory: {config_dir}")
            except Exception as ex:
                self.log.error(f"Failed to create configuration directory {config_dir}: {str(ex)}", exc_info=True)
                raise

    async def _create_default_config(self, path: str) -> None:
        """
        Create a default configuration file if it doesn't exist.
        
        Args:
            path: Path to the configuration file
        """
        if not os.path.exists(path):
            try:
                if not self.cfg.has_section('Server'):
                    self.cfg.add_section('Server')
                self.cfg.set('Server', 'port', str(self.config.get('port', 6001)))
                self.cfg.set('Server', 'host', self.config.get('host', '127.0.0.1'))
                
                with open(path, mode='w', encoding='utf-8') as ini:
                    self.cfg.write(ini)
                self.log.info(f"Created default configuration file: {path}")
            except Exception as ex:
                self.log.error(f"Failed to create default configuration file {path}: {str(ex)}", exc_info=True)
                raise

    async def _check_port_conflicts(self) -> bool:
        """
        Check for port conflicts with other Perun instances.
        
        Returns:
            True if no conflicts, False otherwise
        """
        global ports
        
        port = self.config.get('port', 6001)
        self.log.debug(f"Checking port conflicts for port {port} (default from config)")
        
        if self.cfg.has_section('Server') and self.cfg['Server'].get('port'):
            try:
                port = int(self.cfg['Server'].get('port', '6001'))
                self.log.debug(f"Using port {port} from Perun configuration file")
            except ValueError:
                self.log.error(f"Invalid port value in configuration: {self.cfg['Server'].get('port')}")
                return False
        
        self.log.debug(f"Checking if port {port} is already registered for another server")
        if ports.get(port, self.server.name) != self.server.name:
            self.log.error(f"  => {self.server.name}: {self.name} port {port} already in use by server {ports[port]}!")
            self.log.debug(f"Port conflict detected: port {port} is already used by {ports[port]}")
            return False
        else:
            self.log.debug(f"Registering port {port} for server {self.server.name}")
            ports[port] = self.server.name
            return True

    async def prepare(self) -> bool:
        """
        Prepare the Perun extension for use.
        
        Returns:
            True if preparation was successful, False otherwise
        """
        try:
            path = self.get_config_path()
            
            # Ensure config directory exists
            await self._ensure_config_directory(path)

            # Create default config if it doesn't exist
            await self._create_default_config(path)

            # Update configuration if needed
            dirty = False
            if not self.cfg.has_section('Server'):
                self.cfg.add_section('Server')
                dirty = True

            dirty = self._maybe_update_config('Server', 'port', 'port') or dirty
            dirty = self._maybe_update_config('Server', 'host', 'host') or dirty

            if dirty:
                with open(path, mode='w', encoding='utf-8') as ini:
                    self.cfg.write(ini)
                self.locals = self.load_config()

            # Check port conflicts
            if not await self._check_port_conflicts():
                return False

            # Handle always_on configuration
            if self.config.get('always_on', False):
                self.config['no_shutdown'] = self.config.get('no_shutdown', True)
                if not await asyncio.to_thread(self.is_running):
                    asyncio.create_task(self.startup())
            
            return await super().prepare()
        except Exception as ex:
            self.log.error(f"Error during preparation: {str(ex)}", exc_info=True)
            return False

    async def startup(self) -> bool:
        """
        Start the Perun server.
        
        Returns:
            True if startup was successful, False otherwise
        """
        if self.config.get('autostart', True):
            self.log.debug(f"Launching Perun server with: \"{self.get_exe_path()}\" -config=\"{self.get_config_path()}\"")

            def run_subprocess():
                """Create and run the Perun subprocess"""
                try:
                    if sys.platform == 'win32' and self.config.get('minimized', True):
                        import win32process
                        import win32con

                        info = subprocess.STARTUPINFO()
                        info.dwFlags |= win32process.STARTF_USESHOWWINDOW
                        info.wShowWindow = win32con.SW_SHOWMINNOACTIVE
                        self.log.debug("Using minimized window for Perun process")
                    else:
                        info = None
                    
                    out = subprocess.DEVNULL if not self.config.get('debug', False) else None
                    self.log.debug(f"Subprocess output redirected to {'console' if out is None else 'DEVNULL'}")

                    self.log.debug(f"Executing command: [{self.get_exe_path()}, -config={self.get_config_path()}]")
                    return subprocess.Popen([
                        self.get_exe_path(),
                        f"-config={self.get_config_path()}"
                    ], startupinfo=info, stdout=out, stderr=out, close_fds=True)
                except Exception as ex:
                    self.log.error(f"Failed to start Perun process: {str(ex)}", exc_info=True)
                    raise

            try:
                async with self.lock:
                    if self.is_running():
                        self.log.info(f"Perun is already running for {self.server.name}")
                        return True
                    self.log.debug(f"Starting new Perun process for {self.server.name}")
                    p = await asyncio.to_thread(run_subprocess)
                    self.process = psutil.Process(p.pid)
                    self.log.info(f"Started Perun process with PID {p.pid}")
            except psutil.NoSuchProcess:
                self.log.error(f"Error during launch of {self.get_exe_path()}!")
                return False
            except Exception as ex:
                self.log.error(f"Unexpected error during Perun startup: {str(ex)}", exc_info=True)
                return False

        # Give Perun time to start with timeout
        timeout = 10  # seconds
        self.log.debug(f"Waiting up to {timeout}s for Perun to start")
        for i in range(0, timeout):
            if self.is_running():
                self.log.info(f"Perun started successfully for {self.server.name} after {i+1}s")
                break
            self.log.debug(f"Waiting for Perun to start... ({i+1}/{timeout}s)")
            await asyncio.sleep(1)
        else:
            self.log.error(f"Timeout waiting for Perun to start after {timeout}s")
            return False
        
        return await super().startup()

    def shutdown(self) -> bool:
        """
        Shut down the Perun server.
        
        Returns:
            True if shutdown was successful, False otherwise
        """
        if self.config.get('autostart', True) and not self.config.get('no_shutdown', False):
            self.log.debug(f"Shutdown requested for Perun on {self.server.name}")
            if self.is_running():
                try:
                    self.log.debug("Calling parent shutdown method")
                    super().shutdown()
                    if not self.process:
                        self.log.debug(f"Finding Perun process for shutdown using exe_name={self.exe_name}")
                        self.process = next(utils.find_process(self.exe_name, self.server.instance.name), None)
                        if self.process:
                            self.log.debug(f"Found Perun process with PID {self.process.pid}")
                        else:
                            self.log.debug("No Perun process found")
                    
                    if self.process:
                        pid = self.process.pid
                        self.log.info(f"Terminating Perun process with PID {pid}")
                        self.log.debug(f"Using utils.terminate_process for PID {pid}")
                        utils.terminate_process(self.process)
                        self.log.info(f"Perun process with PID {pid} terminated")
                        self.process = None
                        return True
                    else:
                        self.log.warning(f"  => Could not find a running Perun server process.")
                except Exception as ex:
                    self.log.error(f'Error during shutdown of Perun: {str(ex)}', exc_info=True)
                    return False
            else:
                self.log.debug(f"Perun is not running for {self.server.name}, no shutdown needed")
        else:
            self.log.debug(f"Skipping Perun shutdown due to configuration (autostart={self.config.get('autostart', True)}, no_shutdown={self.config.get('no_shutdown', False)})")
        return True

    def is_running(self) -> bool:
        """
        Check if the Perun server is running.
        
        Returns:
            True if the server is running, False otherwise
        """
        try:
            if not self.process:
                self.log.debug(f"No process reference, searching for Perun process (exe_name={self.exe_name})")
                self.process = next(utils.find_process(self.exe_name, self.server.instance.name), None)
                if self.process:
                    self.log.debug(f"Found Perun process with PID {self.process.pid}")
                else:
                    self.log.debug("No Perun process found")
                    return False
            
            # Check if the process is still running
            if not self.process.is_running():
                self.log.debug(f"Process with PID {self.process.pid} is no longer running")
                self.process = None
                return False
            elif hasattr(psutil, 'STATUS_ZOMBIE') and self.process.status() == psutil.STATUS_ZOMBIE:
                self.log.debug(f"Process with PID {self.process.pid} is in zombie state")
                self.process = None
                return False
            else:
                self.log.debug(f"Process with PID {self.process.pid} is running with status: {self.process.status()}")
                
            # Check if the server is accepting connections
            if self.locals and 'Server' in self.locals:
                server_ip = self.locals['Server'].get('host', '127.0.0.1')
                server_port = self.locals['Server'].get('port', 6001)
                if server_ip == '0.0.0.0':
                    server_ip = '127.0.0.1'
                
                self.log.debug(f"Checking if port {server_port} is open on {server_ip} (timeout: 2.0s)")
                # Add timeout to prevent hanging
                try:
                    running = utils.is_open(server_ip, int(server_port), timeout=2.0)
                    if running:
                        self.log.debug(f"Port {server_port} is open, Perun is running")
                    else:
                        self.log.debug(f"Port {server_port} is not open, Perun may not be fully started")
                        self.process = None
                    return running
                except Exception as ex:
                    self.log.warning(f"Error checking if port is open: {str(ex)}")
                    return False
            else:
                self.log.debug("Using process status only to determine if running")
                return True
        except Exception as ex:
            self.log.error(f"Error checking if Perun is running: {str(ex)}", exc_info=True)
            self.log.exception("Detailed exception while checking Perun status:")
            return False

    def get_inst_path(self) -> str:
        if not self._inst_path:
            if self.config.get('installation'):
                self._inst_path = os.path.expandvars(self.config.get('installation'))
                if not os.path.exists(self._inst_path):
                    raise InstallException(
                        f"The {self.name} installation dir can not be found at {self.config.get('installation')}!")
            else:
                # Default installation paths for different platforms
                if sys.platform == 'win32':
                    self._inst_path = os.path.join(os.path.expandvars('%ProgramFiles%'), 'Perun')
                else:
                    self._inst_path = os.path.join(os.path.expandvars('$HOME'), 'Perun')
                
                if not os.path.exists(self._inst_path):
                    raise InstallException(f"Can't detect the {self.name} installation dir, "
                                           "please specify it manually in your nodes.yaml!")
        return self._inst_path

    def get_exe_path(self) -> str:
        if sys.platform == 'win32':
            self.exe_name = 'perun.exe'
        else:
            self.exe_name = 'perun'
        return os.path.join(self.get_inst_path(), self.exe_name)

    @property
    def version(self) -> Optional[str]:
        try:
            if sys.platform == 'win32':
                version_file = os.path.join(self.get_inst_path(), 'version.txt')
            else:
                version_file = os.path.join(self.get_inst_path(), 'version')
            
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "Unknown"

    async def render(self, param: Optional[dict] = None) -> dict:
        """
        Render extension information for display.
        
        Args:
            param: Optional parameters for rendering
            
        Returns:
            Dictionary with extension information
        """
        if not self.locals or 'Server' not in self.locals:
            return {}
        
        # Use the node's public IP as default
        host = self.config.get('host', self.node.public_ip)
        port = self.locals['Server'].get('port', 6001)
        value = f"{host}:{port}"
        
        return {
            "name": self.name,
            "version": self.version,
            "value": value
        }

    def is_installed(self) -> bool:
        if not super().is_installed():
            return False
        
        # check if Perun is installed
        exe_path = self.get_exe_path()
        if not os.path.exists(exe_path):
            self.log.error(f"  => Perun executable not found in {exe_path}")
            return False
        
        return True

    async def get_ports(self) -> dict:
        if self.locals and 'Server' in self.locals:
            return {
                "Perun Port": self.locals['Server'].get('port', 6001)
            }
        return {}
